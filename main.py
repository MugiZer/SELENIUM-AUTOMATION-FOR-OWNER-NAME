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
    parser = argparse.ArgumentParser(description="Scrape Montreal property data from CSV")
    
    # Input/Output file arguments
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input CSV file containing addresses to process"
    )
    parser.add_argument(
        "--output-file",
        "-o",
        help="Output CSV file path (default: <input_file>_output.csv)"
    )
    
    # Processing options
    parser.add_argument(
        "--max",
        type=int,
        help="Maximum number of addresses to process"
    )
    
    # Browser options
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    
    # Debugging
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
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


def process_csv(args, scraper: MontrealRoleScraper) -> None:
    """Process addresses from a CSV file and write results to a new CSV."""
    if not os.path.exists(args.input_file):
        raise SystemExit(f"Input file not found: {args.input_file}")
    
    from scraper.csv_handler import CSVHandler
    
    # Initialize CSV handler
    csv_handler = CSVHandler(
        input_path=args.input_file,
        output_path=args.output_file
    )
    
    # Process in chunks to handle large files
    total_processed = 0
    success_count = 0
    failure_count = 0
    
    for header, chunk, start_row, end_row in csv_handler.process_in_chunks(chunk_size=20):
        logger.info(f"Processing rows {start_row} to {end_row}...")
        
        updated_chunk = []
        for row in chunk:
            # Ensure all output columns exist
            row = csv_handler.ensure_columns(row)
            
            # Parse input row
            query = parse_input_row(row)
            status = "error:missing_address"
            result: Dict[str, str] = {}
            
            if query:
                # Check for borough column if present
                if query.borough is None and BOROUGH_COLUMN in row and row[BOROUGH_COLUMN]:
                    query.borough = row[BOROUGH_COLUMN].strip()
                    logger.debug(f"Using borough from CSV: {query.borough}")
                
                # Fetch property data
                try:
                    result = scraper.fetch(query) or {}
                    status = result.get("status", "error:unknown")
                except Exception as e:
                    logger.error(f"Error processing row {start_row + len(updated_chunk)}: {str(e)}")
                    status = "error:exception"
            
            # Update row with results
            if status == "ok":
                for key in OUTPUT_COLUMNS:
                    row[key] = result.get(key, "")
                success_count += 1
            else:
                row["status"] = status
                failure_count += 1
                logger.warning(f"Row {start_row + len(updated_chunk)} failed with status: {status}")
            
            updated_chunk.append(row)
            total_processed += 1
            
            # Check max rows limit
            if args.max and total_processed >= args.max:
                break
        
        # Write the processed chunk to the output file
        try:
            # For the first chunk, write header, otherwise append
            mode = 'w' if start_row == 1 else 'a'
            with open(csv_handler.output_path, mode, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=header + [col for col in OUTPUT_COLUMNS if col not in header])
                if mode == 'w':
                    writer.writeheader()
                writer.writerows(updated_chunk)
            
            logger.info(f"Successfully processed {len(updated_chunk)} rows ({success_count} success, {failure_count} failed)")
        except Exception as e:
            logger.error(f"Error writing to output file: {str(e)}")
            # Save failed chunk to a backup file
            backup_path = f"{csv_handler.output_path}.failed_{int(time.time())}.csv"
            with open(backup_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=header + [col for col in OUTPUT_COLUMNS if col not in header])
                writer.writeheader()
                writer.writerows(updated_chunk)
            logger.error(f"Saved failed chunk to {backup_path}")
        
        # Check max rows limit again in case we're in the middle of a chunk
        if args.max and total_processed >= args.max:
            logger.info(f"Reached maximum number of rows to process ({args.max})")
            break
    
    logger.info(f"Processing complete. Total: {total_processed}, Success: {success_count}, Failed: {failure_count}")
    logger.info(f"Output saved to: {csv_handler.output_path}")
    return csv_handler.output_path


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
