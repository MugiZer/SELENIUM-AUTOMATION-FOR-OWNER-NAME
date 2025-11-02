import argparse
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv

from scraper.browser import launch_browser, new_page
from scraper.cache import Cache
from scraper.csvio import (
    backup_original,
    ensure_output_columns,
    export_snapshot,
    read_csv,
    write_csv,
)
from scraper.schema import BOROUGH_COLUMN, OUTPUT_COLUMNS
from scraper.log import configure_logging
from scraper.montreal_role import MontrealRoleScraper, parse_input_row
from scraper.rate import RateLimiter
from scraper.sheets import (
    SheetConfig,
    batch_update,
    ensure_columns,
    get_client,
    open_sheet,
    range_for_rows,
)


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Montreal role scraper")
    parser.add_argument("--csv", type=str, help="Path to CSV file")
    parser.add_argument("--sheet", type=str, help="Google Sheet name")
    parser.add_argument("--tab", type=str, help="Google Sheet tab name")
    parser.add_argument("--from-row", type=int, default=2, help="Starting row (1-indexed)")
    parser.add_argument("--max", type=int, default=0, help="Maximum rows to process")
    parser.add_argument("--delay-min", type=float, default=1.5)
    parser.add_argument("--delay-max", type=float, default=3.0)
    parser.add_argument("--headful", action="store_true", help="Run browser headful")
    parser.add_argument("--login", action="store_true", help="Use login flow")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    configure_logging(level=os.getenv("LOG_LEVEL", "INFO"))

    sheet_name = args.sheet or os.getenv("SHEET_NAME")
    sheet_tab = args.tab or os.getenv("SHEET_TAB")

    if args.csv and sheet_name:
        raise SystemExit("Specify either --csv or --sheet")
    if not args.csv and not sheet_name:
        raise SystemExit("Specify either --csv or --sheet")

    if not args.csv:
        args.sheet = sheet_name
        args.tab = sheet_tab
        if not args.sheet or not args.tab:
            raise SystemExit("Both --sheet and --tab (or SHEET_NAME/SHEET_TAB) are required")

    cache_path = Path(os.getenv("CACHE_PATH", "cache.sqlite"))
    rate_limiter = RateLimiter(delay_min=args.delay_min, delay_max=args.delay_max)
    cache = Cache(cache_path)
    try:
        with launch_browser(headless=not args.headful) as (_, _, context):
            page = new_page(context)
            login_email = os.getenv("MONTREAL_EMAIL")
            login_password = os.getenv("MONTREAL_PASSWORD")
            scraper = MontrealRoleScraper(
                page=page,
                cache=cache,
                rate_limiter=rate_limiter,
                login_email=login_email,
                login_password=login_password,
            )
            if args.login:
                if not login_email or not login_password:
                    raise SystemExit("Missing MONTREAL_EMAIL or MONTREAL_PASSWORD in environment")
                scraper.login(login_email, login_password)

            if args.csv:
                process_csv(Path(args.csv), scraper, args)
            else:
                process_sheet(args, scraper)
    finally:
        cache.close()


def process_csv(path: Path, scraper: MontrealRoleScraper, args):
    df = read_csv(path)
    backup_original(path, df.copy())
    start_index = max(0, args.from_row - 2)
    processed = 0
    failures: List[Tuple[int, str]] = []
    borough_present = BOROUGH_COLUMN in df.columns
    if not borough_present:
        logger.warning(
            "Column '%s' not found in CSV; borough-aware selection will be skipped",
            BOROUGH_COLUMN,
        )
    for idx in range(start_index, len(df)):
        if args.max and processed >= args.max:
            break
        row = df.iloc[idx].to_dict()
        row = ensure_output_columns(row)
        query = parse_input_row(row)
        status = "error:missing_address"
        result: Dict[str, str] = {}
        if query and not query.borough and borough_present:
            logger.debug(
                "Row %s missing borough value in '%s'; falling back to address-only matching",
                idx + 1,
                BOROUGH_COLUMN,
            )
        if not query:
            logger.warning("Skipping row %s due to missing address fields", idx + 1)
        else:
            result = scraper.fetch(query) or {}
            status = result.get("status", "error:unknown")
        if status == "ok":
            for key in OUTPUT_COLUMNS:
                df.at[idx, key] = result.get(key, "")
        else:
            df.at[idx, "status"] = status
            failures.append((idx + 1, status))
        processed += 1
    if failures:
        for row_number, failure_status in failures:
            logger.warning("Row %s not updated due to status '%s'", row_number, failure_status)
    write_csv(path, df)
    enriched_path = path.with_name(f"{path.stem}_enriched{path.suffix}")
    df.to_csv(enriched_path, index=False)
    export_snapshot(df, Path("exports"))


def process_sheet(args, scraper: MontrealRoleScraper) -> None:
    service_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not service_json:
        raise SystemExit("GOOGLE_SERVICE_ACCOUNT_JSON must be set for Sheets mode")
    client = get_client(service_json)
    config = SheetConfig(spreadsheet=args.sheet, tab=args.tab, from_row=args.from_row)
    ws = open_sheet(client, config)
    header = ensure_columns(ws)
    borough_present = BOROUGH_COLUMN in header
    if not borough_present:
        logger.warning(
            "Column '%s' not found in Sheet header; borough-aware selection will be skipped",
            BOROUGH_COLUMN,
        )

    all_values = ws.get_all_values()
    start_row_idx = config.from_row - 1
    processed = 0
    success_rows: List[Tuple[int, Dict[str, str], Dict[str, str]]] = []
    failure_statuses: List[Tuple[int, str]] = []
    for row_idx in range(start_row_idx, len(all_values)):
        if args.max and processed >= args.max:
            break
        row_number = row_idx + 1
        row_values = all_values[row_idx]
        row_dict = {header[i]: row_values[i] if i < len(row_values) else "" for i in range(len(header))}
        row_dict = ensure_output_columns(row_dict)
        query = parse_input_row(row_dict)
        status = "error:missing_address"
        result: Dict[str, str] = {}
        if query and not query.borough and borough_present:
            logger.debug(
                "Row %s missing borough value in '%s'; using address-only matching",
                row_number,
                BOROUGH_COLUMN,
            )
        if not query:
            logger.warning("Skipping row %s due to missing address fields", row_number)
        else:
            result = scraper.fetch(query) or {}
            status = result.get("status", "error:unknown")
        if status == "ok":
            original_row = row_dict.copy()
            updated_row = row_dict.copy()
            for key in OUTPUT_COLUMNS:
                updated_row[key] = result.get(key, "")
            success_rows.append((row_number, original_row, updated_row))
            if len(success_rows) >= 20:
                _commit_batch(ws, success_rows, header)
                success_rows = []
        else:
            logger.warning(
                "Row %s not updated due to status '%s'", row_number, status
            )
            failure_statuses.append((row_number, status))
            if success_rows:
                _commit_batch(ws, success_rows, header)
                success_rows = []
        processed += 1
    if success_rows:
        _commit_batch(ws, success_rows, header)
    if failure_statuses:
        _apply_status_updates(ws, header, failure_statuses)


def _commit_batch(
    ws,
    indexed_rows: List[Tuple[int, Dict[str, str], Dict[str, str]]],
    header: List[str],
) -> None:
    if not indexed_rows:
        return
    ordered = sorted(indexed_rows, key=lambda item: item[0])
    current_start: int = -1
    current_rows: List[Tuple[int, Dict[str, str], Dict[str, str]]] = []
    previous_row: int = -1

    def _dispatch(start: int, rows: List[Tuple[int, Dict[str, str], Dict[str, str]]]) -> None:
        if not rows:
            return
        updated_payload = [updated for (_, _, updated) in rows]
        try:
            batch_update(ws, start, updated_payload, header)
        except Exception as exc:
            end_row = start + len(rows) - 1
            range_label = range_for_rows(start, len(rows), header)
            logger.warning(
                "sheets.batch_failure %s",
                json.dumps({
                    "start_row": start,
                    "end_row": end_row,
                    "range": range_label,
                    "error": str(exc),
                }),
            )
            snapshot = None
            if hasattr(ws, "get"):
                try:
                    snapshot = ws.get(range_label)
                except Exception as fetch_exc:
                    logger.debug(
                        "Unable to snapshot rows %s-%s prior to rollback: %s",
                        start,
                        end_row,
                        fetch_exc,
                    )
            if snapshot is not None:
                logger.info(
                    "sheets.snapshot %s",
                    json.dumps({
                        "range": range_label,
                        "values": snapshot,
                    }),
                )
            original_payload = [original for (_, original, _) in rows]
            try:
                batch_update(ws, start, original_payload, header)
            except Exception as rollback_exc:
                logger.error(
                    "Rollback failed for rows %s-%s: %s",
                    start,
                    end_row,
                    rollback_exc,
                )
                raise
            logger.info(
                "sheets.rollback %s",
                json.dumps({
                    "start_row": start,
                    "end_row": end_row,
                    "range": range_label,
                }),
            )
            time.sleep(2)
            try:
                batch_update(ws, start, updated_payload, header)
            except Exception as final_exc:
                logger.error(
                    "Batch update retry failed for rows %s-%s: %s",
                    start,
                    end_row,
                    final_exc,
                )
                raise

    for row_number, original, updated in ordered:
        if not current_rows:
            current_start = row_number
            current_rows = [(row_number, original, updated)]
        elif row_number == previous_row + 1:
            current_rows.append((row_number, original, updated))
        else:
            _dispatch(current_start, current_rows)
            current_start = row_number
            current_rows = [(row_number, original, updated)]
        previous_row = row_number
    _dispatch(current_start, current_rows)


def _apply_status_updates(ws, header: List[str], updates: List[Tuple[int, str]]) -> None:
    if not updates:
        return
    try:
        status_col_index = header.index("status") + 1
    except ValueError:
        logger.error("Status column missing from header; cannot record failures")
        return
    try:
        from gspread.utils import rowcol_to_a1
    except ImportError:
        logger.error("gspread is required to update status cells")
        return

    for row_number, status in updates:
        cell = rowcol_to_a1(row_number, status_col_index)
        try:
            ws.update(cell, [[status]])
        except Exception as exc:
            logger.error(
                "Failed to update status for row %s at %s: %s",
                row_number,
                cell,
                exc,
            )


if __name__ == "__main__":
    main()
