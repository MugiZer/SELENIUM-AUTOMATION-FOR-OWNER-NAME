import datetime as dt
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from playwright.sync_api import Page, TimeoutError

from .cache import Cache, normalize_key
from .parsers import parse_result_json, parse_result_page
from .rate import RateLimiter, retryable

logger = logging.getLogger(__name__)

BASE_URL = "https://montreal.ca/role-evaluation-fonciere/adresse"
STREET_API = "https://montreal.ca/info-recherche/api/evaluation-fonciere/gem/streets"


@dataclass
class AddressQuery:
    civic_number: str
    street_name: str
    raw_address: str

    @property
    def cache_key(self) -> str:
        return normalize_key(self.civic_number, self.street_name or self.raw_address)


class MontrealRoleScraper:
    def __init__(
        self,
        page: Page,
        cache: Cache,
        rate_limiter: RateLimiter,
        delay_after_actions: bool = True,
        login_email: Optional[str] = None,
        login_password: Optional[str] = None,
    ) -> None:
        self.page = page
        self.cache = cache
        self.rate = rate_limiter
        self.delay_after_actions = delay_after_actions
        self.login_email = login_email
        self.login_password = login_password
        self._auto_login_attempted = False

    def sleep(self):
        if self.delay_after_actions:
            self.rate.sleep()

    def fetch(self, query: AddressQuery) -> Dict[str, str]:
        cached = self.cache.get(query.cache_key)
        if cached:
            logger.info("Cache hit for %s", query.raw_address)
            return cached
        logger.info("Processing %s", query.raw_address)
        status, payload = self._perform_search(query)
        if status == "ok":
            payload["status"] = "ok"
            payload["last_fetched_at"] = dt.datetime.utcnow().isoformat()
            payload["source_url"] = self.page.url
            self.cache.set(query.cache_key, payload, payload["last_fetched_at"])
            return payload
        payload.setdefault("status", status)
        return payload

    @retryable(attempts=3)
    def _perform_search(self, query: AddressQuery):
        attempted_login = False
        while True:
            try:
                self.page.goto(BASE_URL, wait_until="load")
            except TimeoutError:
                self.page.reload()
            if self._on_login_page():
                logger.info("Authentication wall detected during navigation; attempting login")
                if attempted_login or not self._ensure_authenticated():
                    return "error:auth_required", {}
                attempted_login = True
                continue
            self.sleep()
            self._fill_form(query)
            self.sleep()
            status, result = self._select_address(query)
            if status == "auth_required":
                logger.info("Authentication wall detected after address submission; attempting login")
                if attempted_login or not self._ensure_authenticated():
                    return "error:auth_required", {}
                attempted_login = True
                continue
            if status != "ok":
                return status, result
            self.sleep()
            final_data = self._parse_final_page()
            return "ok", final_data

    def login(self, email: str, password: str) -> None:
        logger.info("Attempting login")
        self.page.goto("https://montreal.ca/", wait_until="load")
        self.page.click("button#shell-login-button")
        self.page.fill("input#signInName", email)
        self.page.fill("input#password", password)
        self.page.click("button#next")
        self.page.wait_for_load_state("networkidle")
        logger.info("Login flow completed")

    def _fill_form(self, query: AddressQuery) -> None:
        # Selectors sourced from the provided DevTools snapshot for reliability.
        civic_locator = self.page.locator("input[data-test='input'][name='civicNumber']")
        civic_locator.wait_for(state="visible")
        civic_locator.fill(query.civic_number)
        try:
            self.sleep()
            suggestion = self._best_street_suggestion(query)
        except Exception:
            suggestion = {}
        finally:
            self.sleep()
        street_value = suggestion.get("displayName") or suggestion.get("fullStreetName")
        if street_value:
            street_locator = self.page.locator(
                "div[data-test='combobox'] input[data-test='input'][name='streetNameCombobox']"
            )
            street_locator.wait_for(state="visible")
            street_locator.fill(street_value)
            self.page.evaluate(
                "(suggestion) => {"
                "document.querySelector(\"input[name='streetGeneric']\").value = suggestion.streetGeneric || '';"
                "document.querySelector(\"input[name='streetName']\").value = suggestion.streetName || '';"
                "document.querySelector(\"input[name='noCity']\").value = suggestion.noCity || '';"
                "document.querySelector(\"input[name='boroughNumber']\").value = suggestion.boroughNumber || '';"
                "document.querySelector(\"input[name='streetNameOfficial']\").value = suggestion.streetNameOfficial || '';"
                "}",
                suggestion,
            )
        else:
            street_locator = self.page.locator(
                "div[data-test='combobox'] input[data-test='input'][name='streetNameCombobox']"
            )
            street_locator.wait_for(state="visible")
            street_locator.fill(query.street_name)
        submit_locator = self.page.locator("button[data-test='submit'][form]")
        submit_locator.wait_for(state="attached")
        submit_locator.click()
        self.page.wait_for_load_state("networkidle")

    def _select_address(self, query: AddressQuery):
        if self._on_login_page():
            return "auth_required", {}
        try:
            self.page.wait_for_url(re.compile(r"/role-evaluation-fonciere/adresse/liste"), timeout=10_000)
        except TimeoutError:
            return "not_found", {}
        items = self.page.locator("ul[data-test='list-group'] li[data-test='item']")
        count = items.count()
        if count == 0:
            return "not_found", {}
        normalized_target = _normalize_address(query)
        matched_index = None
        for idx in range(count):
            dd_locator = items.nth(idx).locator("dl dd").first
            try:
                address_text = dd_locator.inner_text(timeout=5_000)
            except Exception:
                continue
            normalized_item = _normalize(address_text)
            if normalized_item == normalized_target:
                matched_index = idx
                break
        if matched_index is None:
            if count > 1:
                return "multiple_matches", {}
            matched_index = 0
        items.nth(matched_index).locator("form button[data-test='button']").click()
        try:
            self.page.wait_for_url(re.compile(r"/role-evaluation-fonciere/adresse/liste/resultat"), timeout=10_000)
        except TimeoutError:
            return "error:timeout", {}
        if self._on_login_page():
            return "auth_required", {}
        self.page.wait_for_load_state("networkidle")
        return "ok", {}

    def _parse_final_page(self) -> Dict[str, str]:
        next_data = None
        try:
            next_data = self.page.evaluate("() => window.__NEXT_DATA__ || null")
        except Exception as exc:
            logger.debug("Unable to evaluate __NEXT_DATA__: %s", exc)
        if isinstance(next_data, dict):
            for url in _candidate_next_data_urls(next_data):
                if not url:
                    continue
                try:
                    self.sleep()
                    response = self.page.context.request.get(url)
                except Exception as exc:
                    logger.debug("Error fetching %s: %s", url, exc)
                    continue
                if not getattr(response, "ok", False):
                    logger.debug("_next data request failed for %s with status %s", url, response.status)
                    continue
                try:
                    payload = response.json()
                except Exception as exc:
                    logger.debug("Unable to decode JSON from %s: %s", url, exc)
                    continue
                try:
                    result = parse_result_json(payload)
                except ValueError:
                    logger.debug("JSON payload from %s did not contain parsable HTML", url)
                    continue
                except Exception as exc:
                    logger.debug("Failed to parse JSON payload from %s: %s", url, exc)
                    continue
                logger.info("Parsed result page via _next JSON payload: %s", url)
                return result
        html = self.page.content()
        data = parse_result_page(html)
        return data

    @retryable(attempts=3)
    def _best_street_suggestion(self, query: AddressQuery) -> Dict[str, str]:
        self.sleep()
        params = urllib.parse.urlencode({"q": query.street_name, "page": 1, "size": 10})
        url = f"{STREET_API}?{params}"
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(request) as response:
                payload = json.loads(response.read().decode("utf-8"))
                status = getattr(response, "status", 200)
                if status >= 500:
                    raise urllib.error.HTTPError(url, status, "Server error", hdrs=None, fp=None)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 or exc.code >= 500:
                logger.warning("Street suggestion API throttled (%s), retrying", exc.code)
                raise
            logger.debug("Street suggestion HTTP error %s", exc.code)
            return {}
        finally:
            self.sleep()
        suggestions = payload.get("data") or payload
        if not suggestions:
            return {}
        normalized_target = _normalize(query.street_name)
        for suggestion in suggestions:
            display = suggestion.get("displayName") or suggestion.get("fullStreetName") or ""
            if _normalize(display) == normalized_target:
                return suggestion
        return suggestions[0]

    def _on_login_page(self) -> bool:
        try:
            current_url = self.page.url
        except Exception:
            current_url = ""
        if current_url and ("login" in current_url or "compte" in current_url):
            return True
        try:
            locator = self.page.locator("input#signInName")
            return locator.count() > 0
        except Exception:
            return False

    def _ensure_authenticated(self) -> bool:
        if self._auto_login_attempted:
            logger.error("Authentication wall encountered after previous login attempt")
            return False
        if not self.login_email or not self.login_password:
            logger.error("Authentication required but credentials are unavailable")
            return False
        self._auto_login_attempted = True
        logger.info("Automatically signing in with configured credentials")
        self.login(self.login_email, self.login_password)
        try:
            self.page.wait_for_load_state("networkidle")
        except TimeoutError:
            pass
        self.page.goto(BASE_URL, wait_until="load")
        return not self._on_login_page()


def _normalize_address(query: AddressQuery) -> str:
    if query.civic_number and query.street_name:
        return _normalize(f"{query.civic_number} {query.street_name}")
    return _normalize(query.raw_address)


def _normalize(value: str) -> str:
    value = value or ""
    value = value.lower()
    value = re.sub(r"[^a-z0-9]", "", value)
    return value


def _candidate_next_data_urls(next_data: Dict[str, Any]) -> List[str]:
    build_id = next_data.get("buildId")
    if not build_id:
        return []
    locale = next_data.get("locale") or next_data.get("defaultLocale") or "fr-CA"
    path = "/role-evaluation-fonciere/adresse/liste"
    urls: List[str] = []
    base = "https://montreal.ca"
    urls.append(f"{base}/_next/data/{build_id}/{locale}{path}.json")
    asset_prefix = next_data.get("assetPrefix") or ""
    asset_prefix = asset_prefix.rstrip("/")
    if asset_prefix and asset_prefix != "/":
        prefixed = f"{base}{asset_prefix}/_next/data/{build_id}/{locale}{path}.json"
        if prefixed not in urls:
            urls.append(prefixed)
    return urls


def parse_input_row(row: Dict[str, str]) -> Optional[AddressQuery]:
    civic_number = clean_number(row.get("civicNumber") or row.get("civic_number"))
    street_name = (row.get("streetName") or row.get("street_name") or "").strip()
    raw_address = row.get("address") or row.get("Adresse") or ""
    if not civic_number and raw_address:
        match = re.match(r"(\d+[a-zA-Z]?)\s+(.*)", raw_address)
        if match:
            civic_number = match.group(1)
            street_name = street_name or match.group(2)
    street_name = street_name.strip()
    if not civic_number or not street_name:
        return None
    return AddressQuery(civic_number=civic_number, street_name=street_name, raw_address=raw_address or f"{civic_number} {street_name}")


def clean_number(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[^0-9a-zA-Z]", "", value)
