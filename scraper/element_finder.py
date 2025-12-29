"""
Robust element finding utilities with fallback strategies.

Provides utilities to locate elements using multiple selector strategies,
improving resilience against website changes.
"""

import logging
from typing import List, Optional
from datetime import datetime
from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

from scraper.selectors import TIMEOUTS

logger = logging.getLogger(__name__)


class ElementNotFoundError(Exception):
    """Raised when element cannot be found with any selector strategy."""

    pass


class SelectorHealthError(Exception):
    """Raised when critical selectors are broken."""

    pass


def find_element_with_fallbacks(
    page: Page,
    selector_list: List[str],
    state: str = "visible",
    timeout: Optional[int] = None,
    screenshot_on_failure: bool = True,
) -> Locator:
    """
    Find element using multiple selector strategies with fallback.

    Args:
        page: Playwright page object
        selector_list: List of selectors to try in order
        state: Desired element state ('visible', 'attached', 'hidden', 'detached')
        timeout: Timeout in milliseconds (uses default if None)
        screenshot_on_failure: Whether to capture screenshot on failure

    Returns:
        Locator object for the found element

    Raises:
        ElementNotFoundError: If element not found with any selector
    """
    if timeout is None:
        timeout = TIMEOUTS["element_visible"]

    errors = []

    for idx, selector in enumerate(selector_list):
        try:
            logger.debug(f"Trying selector {idx + 1}/{len(selector_list)}: {selector}")
            locator = page.locator(selector)

            # Wait for the element in the desired state
            locator.wait_for(state=state, timeout=timeout)

            logger.info(f"Successfully found element with selector: {selector}")
            return locator

        except PlaywrightTimeoutError as e:
            error_msg = f"Timeout waiting for selector '{selector}' (state={state}, timeout={timeout}ms)"
            logger.debug(error_msg)
            errors.append(error_msg)
            continue

        except Exception as e:
            error_msg = f"Error with selector '{selector}': {type(e).__name__}: {e}"
            logger.debug(error_msg)
            errors.append(error_msg)
            continue

    # All selectors failed
    error_summary = f"Failed to find element with any selector. Tried {len(selector_list)} strategies:\n"
    for idx, (selector, error) in enumerate(zip(selector_list, errors)):
        error_summary += f"  {idx + 1}. {selector}\n     -> {error}\n"

    logger.error(error_summary)

    # Capture screenshot for debugging
    if screenshot_on_failure:
        try:
            screenshot_path = f"screenshots/element_not_found_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Failed to capture screenshot: {e}")

    raise ElementNotFoundError(error_summary)


def find_element_safe(
    page: Page,
    selector_list: List[str],
    state: str = "visible",
    timeout: Optional[int] = None,
) -> Optional[Locator]:
    """
    Safe version that returns None instead of raising exception.

    Args:
        page: Playwright page object
        selector_list: List of selectors to try in order
        state: Desired element state
        timeout: Timeout in milliseconds

    Returns:
        Locator if found, None otherwise
    """
    try:
        return find_element_with_fallbacks(
            page, selector_list, state, timeout, screenshot_on_failure=False
        )
    except ElementNotFoundError:
        return None


def fill_element_with_fallbacks(
    page: Page,
    selector_list: List[str],
    value: str,
    timeout: Optional[int] = None,
) -> bool:
    """
    Fill input element using fallback selectors.

    Args:
        page: Playwright page object
        selector_list: List of selectors to try in order
        value: Value to fill
        timeout: Timeout in milliseconds

    Returns:
        True if successful, False otherwise
    """
    try:
        locator = find_element_with_fallbacks(
            page, selector_list, state="visible", timeout=timeout
        )

        # Wait for element to be enabled
        page.wait_for_timeout(100)  # Small delay for stability

        # Clear existing value
        locator.clear()

        # Fill new value
        locator.fill(value)

        # Verify fill succeeded
        filled_value = locator.input_value()
        if filled_value != value:
            logger.warning(
                f"Fill verification failed. Expected '{value}', got '{filled_value}'"
            )
            return False

        logger.info(f"Successfully filled element with value: {value}")
        return True

    except Exception as e:
        logger.error(f"Failed to fill element: {type(e).__name__}: {e}")
        return False


def click_element_with_fallbacks(
    page: Page,
    selector_list: List[str],
    timeout: Optional[int] = None,
    force: bool = False,
) -> bool:
    """
    Click element using fallback selectors.

    Args:
        page: Playwright page object
        selector_list: List of selectors to try in order
        timeout: Timeout in milliseconds
        force: Whether to force the click (bypass actionability checks)

    Returns:
        True if successful, False otherwise
    """
    try:
        locator = find_element_with_fallbacks(
            page, selector_list, state="visible", timeout=timeout
        )

        # Wait for element to be stable
        page.wait_for_timeout(100)

        # Click the element
        locator.click(force=force)

        logger.info(f"Successfully clicked element")
        return True

    except Exception as e:
        logger.error(f"Failed to click element: {type(e).__name__}: {e}")
        return False


def validate_critical_selectors(page: Page, selector_groups: dict) -> None:
    """
    Validate that critical selectors are present on the page.

    Args:
        page: Playwright page object
        selector_groups: Dictionary of selector groups to validate

    Raises:
        SelectorHealthError: If any critical selector is broken
    """
    broken_selectors = []

    for group_name, selectors in selector_groups.items():
        logger.info(f"Validating selector group: {group_name}")

        for selector_name, selector_list in selectors.items():
            # Try to find element with fallbacks
            found = False
            for selector in selector_list:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        found = True
                        logger.debug(
                            f"✓ {group_name}.{selector_name}: Found with '{selector}'"
                        )
                        break
                except Exception:
                    continue

            if not found:
                broken_selectors.append(f"{group_name}.{selector_name}")
                logger.error(
                    f"✗ {group_name}.{selector_name}: NOT FOUND with any selector"
                )

    if broken_selectors:
        error_msg = f"Critical selectors broken: {', '.join(broken_selectors)}"
        logger.error(error_msg)
        raise SelectorHealthError(error_msg)

    logger.info("All critical selectors validated successfully")


def get_element_text_with_fallbacks(
    page: Page,
    selector_list: List[str],
    timeout: Optional[int] = None,
) -> Optional[str]:
    """
    Get element text using fallback selectors.

    Args:
        page: Playwright page object
        selector_list: List of selectors to try in order
        timeout: Timeout in milliseconds

    Returns:
        Element text if found, None otherwise
    """
    try:
        locator = find_element_with_fallbacks(
            page, selector_list, state="attached", timeout=timeout
        )

        text = locator.inner_text(timeout=timeout or TIMEOUTS["short"])
        logger.info(f"Successfully retrieved text: {text[:50]}...")
        return text

    except Exception as e:
        logger.error(f"Failed to get element text: {type(e).__name__}: {e}")
        return None
