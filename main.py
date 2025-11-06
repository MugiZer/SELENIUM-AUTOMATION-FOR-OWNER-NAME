#!/usr/bin/env python3
"""
Montreal Property Data Scraper

This script scrapes property assessment data from the Montreal property assessment website
and saves the results to a CSV file.
"""

import argparse
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator

from dotenv import load_dotenv

# Local imports
from scraper.browser import launch_browser, new_page
from scraper.cache import Cache
from scraper.montreal_role import MontrealRoleScraper, parse_input_row
from scraper.rate import RateLimiter
from scraper.log import configure_logging

# Configuration
from config import (
    NODE_ENV, PORT, SESSION_SECRET, VITE_API_BASE_URL, FRONTEND_URL, CORS_ORIGINS,
    MONTREAL_EMAIL, MONTREAL_PASSWORD, DELAY_MIN, DELAY_MAX, CACHE_PATH, OUTPUT_DIR,
    LOG_LEVEL, LOG_FILE, CSV_CHUNK_SIZE, BACKUP_DIR, DATE_FORMAT, OUTPUT_FILE_PATTERN,
    OUTPUT_COLUMNS, REQUIRED_INPUT_COLUMNS, OPTIONAL_INPUT_COLUMNS, BOROUGH_COLUMN
)

# Configure logging
logger = logging.getLogger(__name__)
configure_logging(LOG_LEVEL, LOG_FILE)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape Montreal property assessment data from a CSV file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input/Output file arguments
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to input CSV file containing property addresses"
    )
    
    parser.add_argument(
        "--output-file", "-o",
        type=str,
        default=None,
        help="Output CSV file path (default: <input_file>_<timestamp>.csv in OUTPUT_DIR)"
    )
    
    # Processing options
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CSV_CHUNK_SIZE,
        help="Number of rows to process in each chunk"
    )
    
    parser.add_argument(
        "--max-rows", "-m",
        type=int,
        default=None,
        help="Maximum number of rows to process"
    )
    
    parser.add_argument(
        "--start-row",
        type=int,
        default=0,
        help="Row number to start processing from (0-based)"
    )
    
    # Browser options
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    
    # Debugging options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching of responses"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable creating backup of input file"
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for the Montreal property data scraper."""
    # Parse command line arguments
    args = parse_args()
    
    # Configure logging
    log_level = 'DEBUG' if args.debug else LOG_LEVEL
    configure_logging(log_level, LOG_FILE)
    
    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize rate limiter and cache
    rate_limiter = RateLimiter(delay_min=DELAY_MIN, delay_max=DELAY_MAX)
    cache = Cache(CACHE_PATH / 'scraper_cache.sqlite')
    
    # Set up output file path
    input_path = Path(args.input_file).resolve()
    timestamp = datetime.now().strftime(DATE_FORMAT)
    
    if args.output_file:
        output_path = Path(args.output_file).resolve()
    else:
        output_filename = f"{input_path.stem}_{timestamp}.csv"
        output_path = OUTPUT_DIR / output_filename
    
    # Create backup of input file
    if not args.no_backup:
        backup_file = BACKUP_DIR / f"{input_path.stem}_{timestamp}{input_path.suffix}"
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(input_path, backup_file)
        logger.info(f"Created backup at: {backup_file}")
    
    try:
        # Initialize browser and scraper
        with launch_browser(headless=args.headless) as (browser, context):
            page = new_page(context)
            
            # Initialize scraper
            scraper = MontrealRoleScraper(
                page=page,
                cache=cache if not args.no_cache else None,
                rate_limiter=rate_limiter,
                login_email=MONTREAL_EMAIL,
                login_password=MONTREAL_PASSWORD,
            )
            
            # Process the CSV file
            process_csv(
                input_path=input_path,
                output_path=output_path,
                scraper=scraper,
                chunk_size=args.chunk_size,
                max_rows=args.max_rows,
                start_row=args.start_row
            )
            
            logger.info(f"Processing complete. Output saved to: {output_path}")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=args.debug)
        sys.exit(1)
        
    finally:
        # Clean up
        cache.close()
        logger.info("Scraping session completed")


def process_csv(
    input_path: Path,
    output_path: Path,
    scraper: MontrealRoleScraper,
    chunk_size: int = 50,
    max_rows: Optional[int] = None,
    start_row: int = 0
) -> None:
    """
    Process a CSV file containing property addresses and save the results.

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
    
                exc,
            )


if __name__ == "__main__":
    main()
