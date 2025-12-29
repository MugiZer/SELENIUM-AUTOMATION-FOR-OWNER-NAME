import datetime as dt
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from .cache import Cache, normalize_key
from .parsers import parse_result_json, parse_result_page
from .rate import RateLimiter, retryable
from .selectors import SELECTORS, TIMEOUTS, URL_PATTERNS
from .element_finder import (
    find_element_with_fallbacks,
    fill_element_with_fallbacks,
    click_element_with_fallbacks,
    get_element_text_with_fallbacks,
    ElementNotFoundError,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://montreal.ca/role-evaluation-fonciere/adresse"
STREET_API = "https://montreal.ca/info-recherche/api/evaluation-fonciere/gem/streets"


@dataclass
class AddressQuery:
    civic_number: str
    street_name: str
    raw_address: str
    neighborhood: Optional[str] = None  # NO_ARROND_ILE_CUM from CSV

    @property
    def cache_key(self) -> str:
        # Include neighborhood in cache key to differentiate same address in different boroughs
        base_key = normalize_key(self.civic_number, self.street_name or self.raw_address)
        if self.neighborhood:
            return f"{base_key}_{normalize_key(self.neighborhood, '')}"
        return base_key


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

    def validate_selectors(self) -> bool:
        """
        Validate that critical selectors are present on the search page.
        Run this before batch processing to ensure selectors haven't changed.

        Returns:
            True if all selectors valid, False if any are broken
        """
        logger.info("Validating critical selectors...")

        try:
            # Navigate to search page
            self.page.goto(BASE_URL, wait_until="load", timeout=TIMEOUTS["page_load"])
        except Exception as e:
            logger.error(f"Failed to navigate to search page: {type(e).__name__}: {e}")
            return False

        broken_selectors = []
        validated_selectors = []

        # Validate search form selectors
        form_selectors = {
            "civic_number": SELECTORS["search_form"]["civic_number"],
            "street_name": SELECTORS["search_form"]["street_name_combobox"],
            "submit_button": SELECTORS["search_form"]["submit_button"],
        }

        for field_name, selector_list in form_selectors.items():
            found = False
            for selector in selector_list:
                try:
                    count = self.page.locator(selector).count()
                    if count > 0:
                        found = True
                        validated_selectors.append(f"search_form.{field_name}")
                        logger.info(f"✓ search_form.{field_name}: Found with '{selector}'")
                        break
                except Exception:
                    continue

            if not found:
                broken_selectors.append(f"search_form.{field_name}")
                logger.error(f"✗ search_form.{field_name}: NOT FOUND with any selector")

        # Report results
        if broken_selectors:
            logger.error(f"Selector validation FAILED. Broken selectors: {', '.join(broken_selectors)}")
            logger.error("The website structure may have changed. Please update selectors.")
            return False

        logger.info(f"Selector validation PASSED. All {len(validated_selectors)} critical selectors are working.")
        return True

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
                self.page.goto(BASE_URL, wait_until="load", timeout=TIMEOUTS["page_load"])
            except PlaywrightTimeoutError:
                logger.warning("Page load timeout, reloading...")
                self.page.reload()
            if self._on_login_page():
                logger.info("Authentication wall detected during navigation; attempting login")
                if attempted_login or not self._ensure_authenticated():
                    return "error:auth_required", {}
                attempted_login = True
                continue
            self.sleep()
            if not self._fill_form(query):
                logger.error("Form filling failed")
                return "error:form_fill_failed", {}
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

    def login(self, email: str, password: str) -> bool:
        """
        Perform login with robust error handling and fallback selectors.

        Args:
            email: User email/username
            password: User password

        Returns:
            True if login successful, False otherwise
        """
        logger.info("Attempting login")

        try:
            # Navigate to homepage
            self.page.goto("https://montreal.ca/", wait_until="load", timeout=TIMEOUTS["page_load"])

            # Click login button with fallbacks
            if not click_element_with_fallbacks(
                self.page,
                SELECTORS["login"]["login_button"],
                timeout=TIMEOUTS["element_visible"],
            ):
                logger.error("Failed to click login button")
                return False

            # Wait for login form to appear
            self.page.wait_for_timeout(1000)

            # Fill email field
            if not fill_element_with_fallbacks(
                self.page,
                SELECTORS["login"]["email_input"],
                email,
                timeout=TIMEOUTS["element_visible"],
            ):
                logger.error("Failed to fill email field")
                return False

            # Fill password field
            if not fill_element_with_fallbacks(
                self.page,
                SELECTORS["login"]["password_input"],
                password,
                timeout=TIMEOUTS["element_visible"],
            ):
                logger.error("Failed to fill password field")
                return False

            # Click submit button
            if not click_element_with_fallbacks(
                self.page,
                SELECTORS["login"]["submit_button"],
                timeout=TIMEOUTS["element_visible"],
            ):
                logger.error("Failed to click submit button")
                return False

            # Wait for navigation after login
            try:
                self.page.wait_for_load_state("networkidle", timeout=TIMEOUTS["long"])
            except PlaywrightTimeoutError:
                logger.warning("Network idle timeout after login, continuing anyway")

            logger.info("Login flow completed successfully")
            return True

        except Exception as e:
            logger.error(f"Login failed with error: {type(e).__name__}: {e}")
            try:
                screenshot_path = f"screenshots/login_failed_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.page.screenshot(path=screenshot_path)
                logger.error(f"Login failure screenshot saved: {screenshot_path}")
            except Exception:
                pass
            return False

    def _fill_form(self, query: AddressQuery) -> bool:
        """
        Fill the address search form with robust error handling.

        Args:
            query: Address query to fill

        Returns:
            True if form filled successfully, False otherwise
        """
        logger.info(f"Filling form for: {query.civic_number} {query.street_name}")

        # Fill civic number field
        if not fill_element_with_fallbacks(
            self.page,
            SELECTORS["search_form"]["civic_number"],
            query.civic_number,
            timeout=TIMEOUTS["element_visible"],
        ):
            logger.error("Failed to fill civic number field")
            return False

        # Get street suggestion from API
        suggestion = {}
        try:
            self.sleep()
            suggestion = self._best_street_suggestion(query)
            logger.debug(f"Got street suggestion: {suggestion.get('displayName', 'None')}")
        except Exception as e:
            logger.warning(f"Failed to get street suggestion: {type(e).__name__}: {e}")
        finally:
            self.sleep()

        # Determine street value to use
        street_value = suggestion.get("displayName") or suggestion.get("fullStreetName")

        if street_value:
            # Fill street name combobox with suggestion
            if not fill_element_with_fallbacks(
                self.page,
                SELECTORS["search_form"]["street_name_combobox"],
                street_value,
                timeout=TIMEOUTS["element_visible"],
            ):
                logger.error("Failed to fill street name field")
                return False

            # Fill hidden fields using Playwright native methods instead of unsafe eval
            hidden_fields = [
                ("street_generic", suggestion.get("streetGeneric", "")),
                ("street_name", suggestion.get("streetName", "")),
                ("no_city", suggestion.get("noCity", "")),
                ("borough_number", suggestion.get("boroughNumber", "")),
                ("street_name_official", suggestion.get("streetNameOfficial", "")),
            ]

            for field_key, field_value in hidden_fields:
                if field_value:  # Only fill if we have a value
                    try:
                        locator = find_element_with_fallbacks(
                            self.page,
                            SELECTORS["search_form"][field_key],
                            state="attached",  # Hidden fields may not be visible
                            timeout=TIMEOUTS["short"],
                            screenshot_on_failure=False,
                        )
                        # Use JavaScript to set value for hidden fields
                        # This is safer than direct eval as it's limited to specific elements
                        locator.evaluate(f"element => element.value = '{field_value}'")
                        logger.debug(f"Set {field_key} to: {field_value}")
                    except ElementNotFoundError:
                        logger.debug(f"Hidden field {field_key} not found (may not be required)")
                    except Exception as e:
                        logger.warning(f"Failed to set {field_key}: {type(e).__name__}: {e}")
        else:
            # No suggestion available, use raw street name
            logger.info("No street suggestion available, using raw street name")
            if not fill_element_with_fallbacks(
                self.page,
                SELECTORS["search_form"]["street_name_combobox"],
                query.street_name,
                timeout=TIMEOUTS["element_visible"],
            ):
                logger.error("Failed to fill street name field")
                return False

        # Submit the form
        if not click_element_with_fallbacks(
            self.page,
            SELECTORS["search_form"]["submit_button"],
            timeout=TIMEOUTS["element_visible"],
        ):
            logger.error("Failed to click submit button")
            return False

        # Wait for page to load
        try:
            self.page.wait_for_load_state("networkidle", timeout=TIMEOUTS["long"])
        except PlaywrightTimeoutError:
            logger.warning("Network idle timeout after form submission, continuing anyway")

        logger.info("Form filled and submitted successfully")
        return True

    def _select_address(self, query: AddressQuery):
        """
        Select the matching address from the results list.

        Args:
            query: Address query to match

        Returns:
            Tuple of (status, result_data)
        """
        if self._on_login_page():
            return "auth_required", {}

        # Wait for results page to load
        try:
            self.page.wait_for_url(
                re.compile(URL_PATTERNS["search_page"]),
                timeout=TIMEOUTS["medium"]
            )
        except PlaywrightTimeoutError:
            logger.error("Timeout waiting for search results page")
            return "not_found", {}

        # Find list items
        try:
            items = find_element_with_fallbacks(
                self.page,
                SELECTORS["address_selection"]["list_items"],
                state="attached",
                timeout=TIMEOUTS["medium"],
                screenshot_on_failure=False,
            )
        except ElementNotFoundError:
            logger.info("No address results found")
            return "not_found", {}

        # Get count of items
        items_locator = self.page.locator(SELECTORS["address_selection"]["list_items"][0])
        count = items_locator.count()

        if count == 0:
            logger.info("No address matches found")
            return "not_found", {}

        logger.info(f"Found {count} address result(s)")

        # Try to match the address
        normalized_target = _normalize_address(query)
        matched_index = None

        for idx in range(count):
            try:
                # Get the address description text from this item
                item_locator = items_locator.nth(idx)
                dd_locator = item_locator.locator(SELECTORS["address_selection"]["address_description"][0]).first

                address_text = dd_locator.inner_text(timeout=TIMEOUTS["short"])
                normalized_item = _normalize(address_text)

                logger.debug(f"Comparing item {idx + 1}: '{address_text}' -> '{normalized_item}'")

                if normalized_item == normalized_target:
                    matched_index = idx
                    logger.info(f"Found exact match at index {idx}: {address_text}")
                    break

            except PlaywrightTimeoutError:
                logger.warning(f"Timeout getting text for item {idx}")
                continue
            except Exception as e:
                logger.warning(f"Error processing item {idx}: {type(e).__name__}: {e}")
                continue

        # If no exact match and multiple results, return error
        if matched_index is None:
            if count > 1:
                logger.warning(f"Multiple addresses found but no exact match for: {query.raw_address}")
                return "multiple_matches", {}
            # If only one result, use it
            matched_index = 0
            logger.info("Only one result, using it even without exact match")

        # Click the select button for the matched item
        try:
            item_locator = items_locator.nth(matched_index)
            select_button = item_locator.locator(SELECTORS["address_selection"]["select_button"][0])
            select_button.click(timeout=TIMEOUTS["element_visible"])
            logger.info(f"Clicked select button for item {matched_index}")
        except Exception as e:
            logger.error(f"Failed to click select button: {type(e).__name__}: {e}")
            return "error:click_failed", {}

        # Wait for results page
        try:
            self.page.wait_for_url(
                re.compile(URL_PATTERNS["results_page"]),
                timeout=TIMEOUTS["medium"]
            )
        except PlaywrightTimeoutError:
            logger.error("Timeout waiting for results page after selection")
            return "error:timeout", {}

        # Check if redirected to login
        if self._on_login_page():
            logger.warning("Redirected to login page after address selection")
            return "auth_required", {}

        # Wait for page to stabilize
        try:
            self.page.wait_for_load_state("networkidle", timeout=TIMEOUTS["long"])
        except PlaywrightTimeoutError:
            logger.warning("Network idle timeout on results page, continuing anyway")

        logger.info("Address selection completed successfully")
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
        
        # Normalize target street and neighborhood for matching
        normalized_street = _normalize(query.street_name)
        normalized_neighborhood = _normalize(query.neighborhood) if query.neighborhood else None
        
        # If neighborhood provided, find suggestion matching both street AND neighborhood
        if normalized_neighborhood:
            logger.debug(f"Filtering suggestions by neighborhood: {query.neighborhood}")
            for suggestion in suggestions:
                display = suggestion.get("displayName") or suggestion.get("fullStreetName") or ""
                normalized_display = _normalize(display)
                # Check if neighborhood appears in the display name
                if normalized_neighborhood in normalized_display:
                    logger.info(f"Matched suggestion by neighborhood: {display}")
                    return suggestion
            # If no neighborhood match, log warning but continue with fallback
            logger.warning(f"No suggestion matched neighborhood '{query.neighborhood}', using first match")
        
        # Fallback: exact street name match
        for suggestion in suggestions:
            display = suggestion.get("displayName") or suggestion.get("fullStreetName") or ""
            if _normalize(display) == normalized_street:
                return suggestion
        
        # Last resort: return first suggestion
        return suggestions[0]

    def _on_login_page(self) -> bool:
        """
        Check if currently on a login page.

        Returns:
            True if on login page, False otherwise
        """
        # Check URL for login patterns
        try:
            current_url = self.page.url.lower()
            for pattern in URL_PATTERNS["login_patterns"]:
                if pattern in current_url:
                    logger.debug(f"Login page detected via URL pattern: {pattern}")
                    return True
        except Exception as e:
            logger.debug(f"Failed to get current URL: {type(e).__name__}: {e}")

        # Check for login form elements
        try:
            # Check if any of the login email input selectors are present
            for selector in SELECTORS["login"]["email_input"]:
                try:
                    count = self.page.locator(selector).count()
                    if count > 0:
                        logger.debug(f"Login page detected via selector: {selector}")
                        return True
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Failed to check for login elements: {type(e).__name__}: {e}")

        return False

    def _ensure_authenticated(self) -> bool:
        """
        Ensure user is authenticated, attempting auto-login if needed.

        Returns:
            True if authenticated, False otherwise
        """
        if self._auto_login_attempted:
            logger.error("Authentication wall encountered after previous login attempt")
            return False

        if not self.login_email or not self.login_password:
            logger.error("Authentication required but credentials are unavailable")
            return False

        self._auto_login_attempted = True
        logger.info("Automatically signing in with configured credentials")

        # Attempt login
        if not self.login(self.login_email, self.login_password):
            logger.error("Auto-login failed")
            return False

        # Wait for page to stabilize
        try:
            self.page.wait_for_load_state("networkidle", timeout=TIMEOUTS["long"])
        except PlaywrightTimeoutError:
            logger.warning("Network idle timeout after login")

        # Navigate back to base URL
        try:
            self.page.goto(BASE_URL, wait_until="load", timeout=TIMEOUTS["page_load"])
        except PlaywrightTimeoutError:
            logger.error("Timeout navigating to base URL after login")
            return False

        # Verify we're not on login page
        is_authenticated = not self._on_login_page()

        if is_authenticated:
            logger.info("Auto-login successful")
        else:
            logger.error("Auto-login failed - still on login page")

        return is_authenticated


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
    
    # Extract neighborhood from various possible column names
    neighborhood = (
        row.get("NO_ARROND_ILE_CUM") or 
        row.get("no_arrond_ile_cum") or 
        row.get("neighborhood") or 
        row.get("neighbourhood") or 
        row.get("arrondissement") or 
        row.get("borough") or 
        ""
    ).strip() or None
    
    if not civic_number and raw_address:
        match = re.match(r"(\d+[a-zA-Z]?)\s+(.*)", raw_address)
        if match:
            civic_number = match.group(1)
            street_name = street_name or match.group(2)
    street_name = street_name.strip()
    if not civic_number or not street_name:
        return None
    return AddressQuery(
        civic_number=civic_number, 
        street_name=street_name, 
        raw_address=raw_address or f"{civic_number} {street_name}",
        neighborhood=neighborhood
    )


def clean_number(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[^0-9a-zA-Z]", "", value)
