import re
from typing import Dict

OUTPUT_COLUMNS = [
    "owner_names",
    "owner_type",
    "matricule",
    "tax_account_number",
    "municipality",
    "fiscal_years",
    "nb_logements",
    "assessed_terrain_current",
    "assessed_batiment_current",
    "assessed_total_current",
    "assessed_total_previous",
    "tax_distribution_json",
    "last_fetched_at",
    "source_url",
    "status",
]

BOROUGH_COLUMN = "NO_ARROND_ILE_CUM"
NORMALIZED_BOROUGH_FIELD = "_normalized_borough"

CANONICAL_BOROUGH_NAMES = {
    "villeraysaintmichelparcextension",
    "westmount",
    "plateaumontroyal",
    "sudouest",
    "villemarie",
    "cotedesneiges notredamedegrace",
    "saintleonard",
    "lachine",
    "verdun",
    "rosemontlapetitepatrie",
    "pierrefondsroxboro",
    "outremont",
    "saintlaurent",
    "ahuntsiccartierville",
    "mercierhochelagamaisonneuve",
}


def normalize_borough(value: str) -> str:
    """Normalize borough name for matching."""
    if not value:
        return ""
    normalized = value.lower()
    normalized = re.sub(r"[^a-z]", "", normalized)
    return normalized


def attach_normalized_borough(row: Dict[str, str]) -> Dict[str, str]:
    """Add normalized borough field to row dict."""
    borough_value = row.get(BOROUGH_COLUMN, "")
    row[NORMALIZED_BOROUGH_FIELD] = normalize_borough(borough_value)
    return row
