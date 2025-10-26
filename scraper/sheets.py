import json
from dataclasses import dataclass
from typing import Dict, List

import gspread
from google.oauth2.service_account import Credentials

from .schema import OUTPUT_COLUMNS


def range_for_rows(start_row: int, count: int, header: List[str]) -> str:
    """Return an A1 range covering ``count`` rows starting at ``start_row``."""
    end_row = start_row + max(count - 1, 0)
    last_col = gspread.utils.rowcol_to_a1(1, len(header))
    column_letters = "".join(filter(str.isalpha, last_col))
    return f"A{start_row}:{column_letters}{end_row}"


@dataclass
class SheetConfig:
    spreadsheet: str
    tab: str
    from_row: int = 2


def get_client(service_account_json: str) -> gspread.Client:
    if service_account_json.strip().startswith("{"):
        info = json.loads(service_account_json)
        credentials = Credentials.from_service_account_info(
            info, scopes=gspread.auth.READ_WRITE_SCOPE
        )
    else:
        credentials = Credentials.from_service_account_file(
            service_account_json, scopes=gspread.auth.READ_WRITE_SCOPE
        )
    return gspread.authorize(credentials)


def open_sheet(client: gspread.Client, config: SheetConfig) -> gspread.Worksheet:
    spreadsheet = client.open(config.spreadsheet)
    return spreadsheet.worksheet(config.tab)


def ensure_columns(ws: gspread.Worksheet) -> List[str]:
    header = ws.row_values(1)
    updated = False
    for column in OUTPUT_COLUMNS:
        if column not in header:
            header.append(column)
            updated = True
    if updated:
        ws.update("A1", [header])
    return header


def batch_update(
    ws: gspread.Worksheet, start_row: int, rows: List[Dict[str, str]], header: List[str]
) -> None:
    if not rows:
        return
    values = []
    for row in rows:
        ordered = [row.get(col, "") for col in header]
        values.append(ordered)
    cell_range = range_for_rows(start_row, len(rows), header)
    ws.update(cell_range, values)
