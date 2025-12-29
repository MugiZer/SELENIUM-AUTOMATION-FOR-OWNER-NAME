"""
Centralized selector configuration for Montreal Role scraper.

Each selector key contains a list of fallback selectors, tried in order.
This improves robustness against website changes.
"""

from typing import Dict, List

# Selector configuration with fallback strategies
SELECTORS: Dict[str, Dict[str, List[str]]] = {
    "login": {
        "login_button": [
            "button#shell-login-button",
            "button[aria-label*='login' i]",
            "button[aria-label*='connexion' i]",
            "//button[contains(translate(text(), 'LOGIN', 'login'), 'login')]",
            "//button[contains(translate(text(), 'CONNEXION', 'connexion'), 'connexion')]",
        ],
        "email_input": [
            "input#signInName",
            "input[type='email']",
            "input[name*='email' i]",
            "input[name*='signIn' i]",
            "input[aria-label*='email' i]",
        ],
        "password_input": [
            "input#password",
            "input[type='password']",
            "input[name='password']",
            "input[aria-label*='password' i]",
            "input[aria-label*='mot de passe' i]",
        ],
        "submit_button": [
            "button#next",
            "button[type='submit']",
            "button[aria-label*='submit' i]",
            "button[aria-label*='soumettre' i]",
            "//button[contains(translate(text(), 'NEXT', 'next'), 'next')]",
            "//button[contains(translate(text(), 'SUIVANT', 'suivant'), 'suivant')]",
        ],
    },
    "search_form": {
        "civic_number": [
            "input[data-test='input'][name='civicNumber']",
            "input[name='civicNumber']",
            "input[placeholder*='civic' i]",
            "input[placeholder*='numéro civique' i]",
            "input[aria-label*='civic' i]",
        ],
        "street_name_combobox": [
            "div[data-test='combobox'] input[data-test='input'][name='streetNameCombobox']",
            "input[name='streetNameCombobox']",
            "input[placeholder*='street' i]",
            "input[placeholder*='rue' i]",
            "input[aria-label*='street' i]",
        ],
        "submit_button": [
            "button[data-test='submit'][form]",
            "button[type='submit'][form]",
            "button[data-test='submit']",
            "button[type='submit']",
            "//button[contains(translate(text(), 'SEARCH', 'search'), 'search')]",
            "//button[contains(translate(text(), 'CHERCHER', 'chercher'), 'chercher')]",
        ],
        # Hidden fields populated via autocomplete
        "street_generic": [
            "input[name='streetGeneric']",
        ],
        "street_name": [
            "input[name='streetName']",
        ],
        "no_city": [
            "input[name='noCity']",
        ],
        "borough_number": [
            "input[name='boroughNumber']",
        ],
        "street_name_official": [
            "input[name='streetNameOfficial']",
        ],
    },
    "address_selection": {
        "list_container": [
            "ul[data-test='list-group']",
            "ul[role='list']",
            "ul.list-group",
        ],
        "list_items": [
            "ul[data-test='list-group'] li[data-test='item']",
            "ul[role='list'] li[role='listitem']",
            "ul.list-group li.list-item",
        ],
        "address_description": [
            "dl dd",
            "dd",
            ".description",
        ],
        "select_button": [
            "form button[data-test='button']",
            "button[type='submit']",
            "button[aria-label*='select' i]",
            "button[aria-label*='sélectionner' i]",
        ],
    },
    "autocomplete": {
        "suggestions_list": [
            "div#react-autowhatever-1",
            "div[role='listbox']",
            "ul[role='listbox']",
            ".suggestions-list",
        ],
        "suggestion_items": [
            "div#react-autowhatever-1 ul li",
            "div[role='listbox'] [role='option']",
            "ul[role='listbox'] li",
            ".suggestion-item",
        ],
    },
}

# URL patterns for navigation validation
URL_PATTERNS = {
    "search_page": r"/role-evaluation-fonciere/adresse/liste",
    "results_page": r"/role-evaluation-fonciere/adresse/liste/resultat",
    "login_patterns": ["login", "compte", "signin", "connexion"],
}

# Timeout configuration (in milliseconds)
TIMEOUTS = {
    "default": 10_000,
    "short": 5_000,
    "medium": 15_000,
    "long": 30_000,
    "network": 60_000,
    "element_visible": 10_000,
    "element_attached": 5_000,
    "page_load": 30_000,
}
