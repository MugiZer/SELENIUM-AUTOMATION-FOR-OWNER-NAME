import asyncio
import contextlib
import json
import os
import random
from pathlib import Path
from typing import Iterator, Optional

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from scraper.selectors import TIMEOUTS


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]


def _get_proxy_config() -> Optional[dict]:
    """Parse proxy from environment variables."""
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if not https_proxy:
        return None

    from urllib.parse import urlparse
    parsed = urlparse(https_proxy)
    if parsed.username:
        return {
            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
            "username": parsed.username,
            "password": parsed.password or "",
        }
    return {"server": https_proxy}


@contextlib.contextmanager
def launch_browser(headless: bool = True) -> Iterator[tuple[Playwright, Browser, BrowserContext]]:
    playwright = sync_playwright().start()

    # Get proxy configuration
    proxy_config = _get_proxy_config()

    # Build browser args
    browser_args = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--disable-features=IsolateOrigins,site-per-process'
    ]

    # Add proxy args for Chromium if proxy is configured
    if proxy_config:
        browser_args.append(f'--proxy-server={proxy_config["server"]}')

    browser = playwright.chromium.launch(
        headless=headless,
        args=browser_args,
        proxy=proxy_config  # Also pass to launch for proper auth handling
    )
    user_agent = random.choice(USER_AGENTS)

    context = browser.new_context(
        user_agent=user_agent,
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
        proxy=proxy_config  # Context-level proxy for proper routing
    )
    add_stealth(context)
    try:
        yield playwright, browser, context
    finally:
        context.close()
        browser.close()
        playwright.stop()


def add_stealth(context: BrowserContext) -> None:
    """Apply basic stealth scripts to the context."""
    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """
    )


def new_page(context: BrowserContext) -> Page:
    """
    Create a new page with configured default timeout.

    Args:
        context: Browser context to create page in

    Returns:
        Configured page instance
    """
    page = context.new_page()
    page.set_default_timeout(TIMEOUTS["default"])
    return page
