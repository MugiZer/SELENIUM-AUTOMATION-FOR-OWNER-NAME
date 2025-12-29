# Targeting Issues Fixes - Implementation Summary

This document describes the comprehensive fixes implemented to address targeting issues in the Montreal Role scraper.

## 🎯 Overview

The scraper has been significantly improved with robust element targeting, better error handling, and configurable timeouts. These changes make the scraper more resilient to website changes and provide better debugging capabilities.

## 📋 Changes Implemented

### 1. Centralized Selector Configuration (`scraper/selectors.py`)

**What:** All selectors are now centralized in a single configuration file with fallback strategies.

**Benefits:**
- Easy maintenance - update selectors in one place
- Multiple fallback selectors per element
- Consistent timeout configuration
- URL patterns for validation

**Example:**
```python
from scraper.selectors import SELECTORS, TIMEOUTS

# Access selectors with fallbacks
login_button_selectors = SELECTORS["login"]["login_button"]
# ["button#shell-login-button", "button[aria-label*='login' i]", ...]

# Use configured timeouts
timeout = TIMEOUTS["element_visible"]  # 10,000ms
```

### 2. Robust Element Finder (`scraper/element_finder.py`)

**What:** New utility module for finding elements with automatic fallback strategies.

**Features:**
- Tries multiple selectors automatically
- Captures screenshots on failure
- Specific exception types for better error handling
- Helper functions for common operations

**Key Functions:**
```python
from scraper.element_finder import (
    find_element_with_fallbacks,    # Find element with multiple selectors
    fill_element_with_fallbacks,    # Fill input with validation
    click_element_with_fallbacks,   # Click with retry logic
    get_element_text_with_fallbacks, # Get text safely
    ElementNotFoundError,            # Specific exception type
)
```

**Example Usage:**
```python
# Instead of:
element = page.locator("button#submit")
element.click()

# Use:
if not click_element_with_fallbacks(
    page,
    ["button#submit", "button[type='submit']", "//button[text()='Submit']"],
    timeout=10_000
):
    logger.error("Failed to click submit button")
```

### 3. Improved Login Method

**Changes:**
- Uses fallback selectors from configuration
- Returns boolean success/failure
- Captures screenshots on failure
- Better error logging with specific exception types
- Validates each step (click, fill, submit)

**Before:**
```python
def login(self, email: str, password: str) -> None:
    self.page.click("button#shell-login-button")  # No error handling
    self.page.fill("input#signInName", email)
    # ... brittle, no validation
```

**After:**
```python
def login(self, email: str, password: str) -> bool:
    if not click_element_with_fallbacks(
        self.page,
        SELECTORS["login"]["login_button"],
        timeout=TIMEOUTS["element_visible"],
    ):
        logger.error("Failed to click login button")
        return False
    # ... with screenshot on failure, multiple selectors, validation
```

### 4. Safe Form Filling (Replaced DOM Manipulation)

**Changes:**
- Removed unsafe `page.evaluate()` with unvalidated JavaScript
- Uses Playwright native methods with proper error handling
- Validates that fields are filled correctly
- Better handling of hidden fields

**Before:**
```python
# UNSAFE: Direct DOM manipulation
self.page.evaluate(
    "(suggestion) => {"
    "document.querySelector(\"input[name='streetGeneric']\").value = suggestion.streetGeneric || '';"
    # ... no error handling, could fail silently
)
```

**After:**
```python
# SAFE: Controlled locator evaluation with error handling
try:
    locator = find_element_with_fallbacks(
        self.page,
        SELECTORS["search_form"]["street_generic"],
        state="attached",
        timeout=TIMEOUTS["short"],
    )
    locator.evaluate(f"element => element.value = '{field_value}'")
    logger.debug(f"Set street_generic to: {field_value}")
except ElementNotFoundError:
    logger.debug("Field not found (may not be required)")
```

### 5. Improved Address Selection

**Changes:**
- Better error messages for each failure type
- Specific timeout handling (not broad Exception)
- Detailed logging of matching process
- Uses configured timeouts
- Captures context on failures

**Improvements:**
- Distinguishes between timeout vs element not found
- Logs each address candidate during matching
- Better handling of stale elements
- Clear error status codes

### 6. Enhanced Login Detection

**Changes:**
- Uses URL patterns from configuration
- Multiple selector strategies for detection
- Better error handling
- Clear debug logging

### 7. Configurable Timeouts

**Changes:**
- All timeouts centralized in `TIMEOUTS` configuration
- Different timeouts for different operation types
- Can be adjusted without code changes

**Timeout Types:**
```python
TIMEOUTS = {
    "default": 10_000,        # Default for most operations
    "short": 5_000,           # Quick operations
    "medium": 15_000,         # Moderate operations
    "long": 30_000,           # Long-running operations
    "network": 60_000,        # Network requests
    "element_visible": 10_000, # Wait for visibility
    "element_attached": 5_000, # Wait for attachment
    "page_load": 30_000,      # Page navigation
}
```

### 8. Selector Validation Method

**What:** New `validate_selectors()` method to check if selectors work before batch processing.

**Usage:**
```python
scraper = MontrealRoleScraper(...)

# Validate selectors before running batch
if scraper.validate_selectors():
    print("✓ All selectors working")
    # Run batch...
else:
    print("✗ Some selectors broken - fix before batch")
```

**Output:**
```
INFO: Validating critical selectors...
INFO: ✓ search_form.civic_number: Found with 'input[data-test='input'][name='civicNumber']'
INFO: ✓ search_form.street_name: Found with 'div[data-test='combobox'] input[...]'
INFO: ✓ search_form.submit_button: Found with 'button[data-test='submit'][form]'
INFO: Selector validation PASSED. All 3 critical selectors are working.
```

### 9. Better Error Handling

**Changes:**
- Replaced broad `except Exception:` with specific exceptions
- Added `PlaywrightTimeoutError` handling
- Better error messages with context
- Screenshots captured on failures
- Detailed logging at each step

**Before:**
```python
try:
    suggestion = self._best_street_suggestion(query)
except Exception:  # Too broad!
    suggestion = {}
```

**After:**
```python
try:
    self.sleep()
    suggestion = self._best_street_suggestion(query)
    logger.debug(f"Got street suggestion: {suggestion.get('displayName', 'None')}")
except Exception as e:
    logger.warning(f"Failed to get street suggestion: {type(e).__name__}: {e}")
    suggestion = {}
```

### 10. Enhanced Testing

**Changes:**
- Updated test stubs to support new methods
- Test assertions updated for boolean returns
- Better mocking of element finder behavior

## 🚀 Usage Examples

### Basic Scraping with Validation

```python
from scraper.browser import launch_browser, new_page
from scraper.cache import Cache
from scraper.rate import RateLimiter
from scraper.montreal_role import MontrealRoleScraper, AddressQuery

# Setup
with launch_browser() as (playwright, browser, context):
    page = new_page(context)
    cache = Cache("cache.db")
    rate_limiter = RateLimiter(delay_min=1, delay_max=3)

    scraper = MontrealRoleScraper(
        page=page,
        cache=cache,
        rate_limiter=rate_limiter,
        login_email="user@example.com",
        login_password="password",
    )

    # Validate selectors before batch processing
    if not scraper.validate_selectors():
        print("ERROR: Selectors are broken!")
        exit(1)

    # Run scraping
    query = AddressQuery(
        civic_number="1234",
        street_name="Rue Example",
        raw_address="1234 Rue Example"
    )

    result = scraper.fetch(query)
    print(result)
```

### Handling Errors

```python
from scraper.element_finder import ElementNotFoundError

try:
    result = scraper.fetch(query)
    if result.get("status") == "ok":
        print(f"Owner: {result.get('owner_names')}")
    else:
        print(f"Error: {result.get('status')}")
except ElementNotFoundError as e:
    print(f"Element targeting failed: {e}")
    # Check screenshots/ directory for debugging
```

## 🔧 Maintenance

### Updating Selectors

When website structure changes, update `scraper/selectors.py`:

```python
SELECTORS = {
    "search_form": {
        "civic_number": [
            "input[data-test='input'][name='civicNumber']",  # Try this first
            "input[name='civicNumber']",                      # Then this
            "input[placeholder*='civic' i]",                  # Then this
            # Add more fallbacks...
        ],
    }
}
```

### Adjusting Timeouts

Modify `TIMEOUTS` in `scraper/selectors.py`:

```python
TIMEOUTS = {
    "default": 15_000,  # Increase from 10s to 15s for slower networks
    # ...
}
```

### Debugging Failed Selectors

1. Check `screenshots/` directory for failure screenshots
2. Review logs for specific selector failures
3. Use browser DevTools to test selectors
4. Update `SELECTORS` configuration with working selectors

## 📊 Improvements Summary

| Area | Before | After |
|------|--------|-------|
| **Login** | Hardcoded selectors, no error handling | Multiple fallback selectors, validates each step |
| **Form Filling** | Unsafe DOM eval, no validation | Safe Playwright methods, validates fills |
| **Element Finding** | Single selector, fails immediately | Multiple selectors with fallbacks |
| **Error Handling** | Broad exceptions, silent failures | Specific exceptions, detailed logging |
| **Timeouts** | Hardcoded 10s everywhere | Configurable per operation type |
| **Debugging** | No screenshots, unclear errors | Auto-screenshots, detailed error context |
| **Maintenance** | Selectors scattered in code | Centralized configuration |
| **Testing** | No pre-flight validation | `validate_selectors()` method |

## 🎓 Best Practices

1. **Always validate selectors** before batch processing
2. **Check screenshots/** on failures for visual debugging
3. **Update selectors centrally** in `selectors.py`, not in code
4. **Add fallback selectors** when you find working alternatives
5. **Review logs** for warning messages about selector issues
6. **Test in production environment** before large batches

## 📝 Migration Guide

If you have existing code using the old scraper:

1. **Login method now returns boolean:**
   ```python
   # Before:
   scraper.login(email, password)

   # After:
   if not scraper.login(email, password):
       print("Login failed!")
   ```

2. **_fill_form is now internal and returns boolean** (you shouldn't call it directly)

3. **Import new modules if needed:**
   ```python
   from scraper.selectors import SELECTORS, TIMEOUTS
   from scraper.element_finder import find_element_with_fallbacks
   ```

## 🐛 Troubleshooting

### Selectors Not Working

Run validation:
```python
scraper.validate_selectors()
```

Check screenshots in `screenshots/` directory.

### Timeouts Too Aggressive

Increase timeouts in `scraper/selectors.py`:
```python
TIMEOUTS = {
    "default": 20_000,  # 20 seconds
    "page_load": 60_000,  # 60 seconds
}
```

### Element Not Found Errors

1. Check if website structure changed
2. Use browser DevTools to find new selectors
3. Add new selectors to `SELECTORS` configuration
4. Re-run validation

## 📚 Files Modified

- `scraper/selectors.py` - **NEW** - Centralized selector configuration
- `scraper/element_finder.py` - **NEW** - Robust element finding utilities
- `scraper/browser.py` - Updated to use configurable timeouts
- `scraper/montreal_role.py` - Major refactoring with all improvements
- `tests/test_montreal_role.py` - Updated tests for new behavior
- `screenshots/` - **NEW** - Directory for debugging screenshots

## ✅ Testing

Run tests:
```bash
pytest tests/test_montreal_role.py -v
```

Validate selectors in production:
```python
scraper.validate_selectors()
```

## 🎉 Conclusion

The scraper is now significantly more robust, maintainable, and debuggable. The centralized configuration and fallback strategies make it resilient to website changes, while improved error handling and logging make issues easier to diagnose and fix.
