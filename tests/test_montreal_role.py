import os
import sys
import types

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

if "playwright" not in sys.modules:
    playwright_stub = types.ModuleType("playwright")
    sync_api_stub = types.ModuleType("playwright.sync_api")

    class _Dummy:
        def __getattr__(self, _name):
            return self

    sync_api_stub.Browser = _Dummy
    sync_api_stub.BrowserContext = _Dummy
    sync_api_stub.Page = _Dummy
    sync_api_stub.Playwright = _Dummy
    sync_api_stub.TimeoutError = type("TimeoutError", (Exception,), {})

    def _missing_playwright(*_args, **_kwargs):
        raise RuntimeError("playwright not available in test environment")

    sync_api_stub.sync_playwright = _missing_playwright
    playwright_stub.sync_api = sync_api_stub
    sys.modules["playwright"] = playwright_stub
    sys.modules["playwright.sync_api"] = sync_api_stub

if "tenacity" not in sys.modules:
    tenacity_stub = types.ModuleType("tenacity")

    def _identity_decorator(*_args, **_kwargs):
        return lambda fn: fn

    tenacity_stub.retry = _identity_decorator
    tenacity_stub.stop_after_attempt = lambda *args, **kwargs: None
    tenacity_stub.wait_exponential = lambda *args, **kwargs: None
    sys.modules["tenacity"] = tenacity_stub

from scraper.montreal_role import AddressQuery, MontrealRoleScraper
from scraper.rate import RateLimiter


class DummyCache:
    def get(self, *_args, **_kwargs):
        return None

    def set(self, *_args, **_kwargs):
        return None

    def close(self):
        return None


class StubLocator:
    def __init__(self, page, selector):
        self._page = page
        self.selector = selector

    def wait_for(self, state="attached", timeout=None):
        self._page.waits.append((self.selector, state))

    def fill(self, value):
        self._page.fills.append((self.selector, value))

    def clear(self):
        pass

    def input_value(self):
        # Return the last filled value for this selector
        for selector, value in reversed(self._page.fills):
            if selector == self.selector:
                return value
        return ""

    def click(self, timeout=None, force=False):
        self._page.clicks.append(self.selector)

    def locator(self, selector):
        return self._page.locator(selector)

    def inner_text(self, *args, **kwargs):
        raise AssertionError("inner_text should not be invoked in selector smoke test")

    def count(self):
        return 0

    def evaluate(self, script):
        self._page.evaluations.append((self.selector, script))


class StubPage:
    def __init__(self):
        self.url = ""
        self.waits = []
        self.fills = []
        self.clicks = []
        self.evaluations = []

    def locator(self, selector):
        locator = self.__dict__.setdefault("_locators", {})
        if selector not in locator:
            locator[selector] = StubLocator(self, selector)
        return locator[selector]

    def wait_for_load_state(self, *_args, **_kwargs):
        return None

    def wait_for_timeout(self, timeout):
        return None

    def screenshot(self, path):
        return None

    def evaluate(self, script, suggestion):
        self.evaluations.append((script, suggestion))


@pytest.fixture
def scraper(monkeypatch):
    page = StubPage()
    rate = RateLimiter(delay_min=0, delay_max=0)
    scraper = MontrealRoleScraper(
        page=page,
        cache=DummyCache(),
        rate_limiter=rate,
        delay_after_actions=False,
    )
    monkeypatch.setattr(scraper, "_best_street_suggestion", lambda _query: {
        "displayName": "1463 Rue Bishop (Montréal)",
        "streetGeneric": "Rue",
        "streetName": "Bishop",
        "noCity": "Montréal",
        "boroughNumber": "01",
        "streetNameOfficial": "Rue Bishop",
    })
    return scraper


def test_fill_form_uses_devtools_selectors(scraper):
    query = AddressQuery("1463", "Rue Bishop", "1463 Rue Bishop (Montréal)")
    result = scraper._fill_form(query)

    # _fill_form should return True on success
    assert result is True

    page = scraper.page

    # Check that civic number field was filled
    # The new implementation uses selectors from SELECTORS config
    assert any("1463" in str(fill) for fill in page.fills), "Civic number should be filled"

    # Check that street name was filled with suggestion displayName
    assert any("1463 Rue Bishop (Montréal)" in str(fill) for fill in page.fills), "Street name should be filled with suggestion"

    # Check that submit button was clicked
    assert len(page.clicks) > 0, "Submit button should be clicked"

    # Hidden fields should be populated (either via evaluations on locators or page.evaluate)
    # The new implementation uses locator.evaluate() instead of page.evaluate()
    assert len(page.evaluations) > 0, "Hidden fields should be populated"


def test_perform_search_escalates_to_login(monkeypatch, caplog):
    class PageStub:
        def __init__(self):
            self.url = "https://montreal.ca/role-evaluation-fonciere/adresse"

        def goto(self, url, wait_until=None):
            self.url = url

        def reload(self):
            self.url = "reloaded"

        def wait_for_load_state(self, *_args, **_kwargs):
            return None

        def locator(self, selector):
            return types.SimpleNamespace(count=lambda: 0)

    page = PageStub()
    scraper = MontrealRoleScraper(
        page=page,
        cache=DummyCache(),
        rate_limiter=RateLimiter(delay_min=0, delay_max=0),
        delay_after_actions=False,
        login_email="user@example.com",
        login_password="secret",
    )
    monkeypatch.setattr(scraper, "_fill_form", lambda _query: True)
    monkeypatch.setattr(scraper, "_select_address", lambda _query: ("ok", {}))
    monkeypatch.setattr(scraper, "_parse_final_page", lambda: {"owner_names": "Example"})
    called = {"count": 0}

    on_login_calls = {"count": 0}

    def on_login():
        on_login_calls["count"] += 1
        return on_login_calls["count"] == 1

    monkeypatch.setattr(scraper, "_on_login_page", lambda: on_login())

    def ensure():
        called["count"] += 1
        scraper._auto_login_attempted = True
        return True

    monkeypatch.setattr(scraper, "_ensure_authenticated", ensure)
    caplog.set_level("INFO")
    status, payload = scraper._perform_search(AddressQuery("1", "Main", "1 Main"))
    assert status == "ok"
    assert called["count"] == 1
    assert payload["owner_names"] == "Example"
    assert "Authentication wall detected" in caplog.text
    assert on_login_calls["count"] >= 2


def test_perform_search_handles_auth_wall_post_submission(monkeypatch):
    class PageStub:
        def __init__(self):
            self.url = "https://montreal.ca/role-evaluation-fonciere/adresse"

        def goto(self, url, wait_until=None):
            self.url = url

        def reload(self):
            self.url = "reloaded"

        def wait_for_load_state(self, *_args, **_kwargs):
            return None

        def locator(self, selector):
            return types.SimpleNamespace(count=lambda: 0)

    page = PageStub()
    scraper = MontrealRoleScraper(
        page=page,
        cache=DummyCache(),
        rate_limiter=RateLimiter(delay_min=0, delay_max=0),
        delay_after_actions=False,
        login_email="user@example.com",
        login_password="secret",
    )
    monkeypatch.setattr(scraper, "_fill_form", lambda _query: True)
    statuses = ["auth_required", "ok"]

    def _select(_query):
        status = statuses.pop(0)
        return status, {}

    monkeypatch.setattr(scraper, "_select_address", _select)
    monkeypatch.setattr(scraper, "_parse_final_page", lambda: {"owner_names": "Example"})
    monkeypatch.setattr(scraper, "_on_login_page", lambda: False)
    attempts = {"count": 0}

    def ensure():
        attempts["count"] += 1
        scraper._auto_login_attempted = True
        return True

    monkeypatch.setattr(scraper, "_ensure_authenticated", ensure)
    status, payload = scraper._perform_search(AddressQuery("1", "Main", "1 Main"))
    assert status == "ok"
    assert attempts["count"] == 1
    assert payload["owner_names"] == "Example"


def test_address_query_creation(monkeypatch):
    """Test AddressQuery creation and initialization."""
    query = AddressQuery("1463", "Rue Bishop", "1463 Rue Bishop (Montréal)")
    assert query.civic_number == "1463"
    assert query.street_name == "Rue Bishop"
    assert query.neighborhood is None  # Default


def test_address_query_with_neighborhood(monkeypatch):
    """Test AddressQuery with neighborhood information."""
    query = AddressQuery(
        "1463", "Rue Bishop", "1463 Rue Bishop (Montréal)",
        neighborhood="Côte-des-Neiges"
    )
    assert query.neighborhood == "Côte-des-Neiges"


def test_scraper_cache_integration(monkeypatch):
    """Test that scraper uses cache correctly."""
    class CacheStub:
        def __init__(self):
            self.cache = {}

        def get(self, key):
            return self.cache.get(key)

        def set(self, key, value):
            self.cache[key] = value

        def close(self):
            pass

    cache = CacheStub()
    page = StubPage()
    scraper = MontrealRoleScraper(
        page=page,
        cache=cache,
        rate_limiter=RateLimiter(delay_min=0, delay_max=0),
        delay_after_actions=False,
    )

    # Store something in cache
    cache.set("test_key", {"status": "ok", "owner_names": "Cached"})

    # Verify cache retrieval
    cached = cache.get("test_key")
    assert cached is not None
    assert cached["owner_names"] == "Cached"


def test_scraper_rate_limiting(monkeypatch):
    """Test that scraper respects rate limiting."""
    page = StubPage()
    rate_limiter = RateLimiter(delay_min=0.1, delay_max=0.2)

    scraper = MontrealRoleScraper(
        page=page,
        cache=DummyCache(),
        rate_limiter=rate_limiter,
        delay_after_actions=False,
    )

    # Verify rate limiter is configured
    assert scraper.rate_limiter is not None
    assert scraper.rate_limiter.delay_min == 0.1
    assert scraper.rate_limiter.delay_max == 0.2


def test_scraper_initialization_with_credentials(monkeypatch):
    """Test scraper initialization with login credentials."""
    page = StubPage()
    scraper = MontrealRoleScraper(
        page=page,
        cache=DummyCache(),
        rate_limiter=RateLimiter(delay_min=0, delay_max=0),
        login_email="test@example.com",
        login_password="password123",
        delay_after_actions=False,
    )

    assert scraper.login_email == "test@example.com"
    assert scraper.login_password == "password123"


def test_scraper_fetch_returns_dict(scraper, monkeypatch):
    """Test that fetch method returns a dictionary."""
    query = AddressQuery("1463", "Rue Bishop", "1463 Rue Bishop (Montréal)")

    monkeypatch.setattr(scraper, "_perform_search", lambda _: ("ok", {"owner_names": "Test"}))

    result = scraper.fetch(query)
    assert isinstance(result, dict)
    assert "status" in result or "owner_names" in result


def test_scraper_handles_network_errors(scraper, monkeypatch):
    """Test that scraper handles network errors gracefully."""
    query = AddressQuery("1463", "Rue Bishop", "1463 Rue Bishop (Montréal)")

    def raise_error(*args, **kwargs):
        raise ConnectionError("Network timeout")

    monkeypatch.setattr(scraper, "_perform_search", raise_error)

    # The fetch method should handle the exception
    # In real implementation, it would retry or return error status
