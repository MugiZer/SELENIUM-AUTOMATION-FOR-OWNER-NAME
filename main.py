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
from typing import Any, Dict, List, Optional, Tuple, Generator, Union

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
        with launch_browser(headless=args.headless) as (playwright, browser, context):
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
) -> Dict[str, Any]:
    """
    Process a CSV file containing property addresses and save the results.
    
    Args:
        input_path: Path to the input CSV file
        output_path: Path to save the output CSV file
        scraper: Initialized MontrealRoleScraper instance
        chunk_size: Number of rows to process in each chunk
        max_rows: Maximum number of rows to process (None for no limit)
        start_row: Row number to start processing from (0-based)
        
    Returns:
        Dict containing processing statistics and output path:
        {
            'total_processed': int,
            'success_count': int,
            'failure_count': int,
            'output_path': str
        }
    """
    import pandas as pd
    from tqdm import tqdm
    
    # Read input CSV
    logger.info(f"Reading input file: {input_path}")
    
    # Check if input file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Read CSV in chunks for memory efficiency
    chunks = pd.read_csv(
        input_path,
        chunksize=chunk_size,
        dtype=str,
        skiprows=range(1, start_row + 1)  # Skip header + start_row rows
    )
    
    # Prepare output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Process in chunks to handle large files
    total_processed = 0
    success_count = 0
    failure_count = 0
    
    # Get the header from the first chunk
    first_chunk = True
    
    for chunk in chunks:
        chunk_processed = 0
        chunk_success = 0
        chunk_failure = 0
        
        # Process each row in the chunk
        updated_chunk = []
        
        for _, row in chunk.iterrows():
            # Check max rows limit
            if max_rows is not None and total_processed >= max_rows:
                break
                
            # Ensure all required columns exist
            row_dict = row.to_dict()
            for col in REQUIRED_INPUT_COLUMNS:
                if col not in row_dict:
                    row_dict[col] = ""
            
            # Parse input row
            query = parse_input_row(row_dict)
            status = "error:missing_address"
            result: Dict[str, str] = {}
            
            if query:
                # Check for borough column if present
                if query.borough is None and BOROUGH_COLUMN in row_dict and row_dict[BOROUGH_COLUMN]:
                    query.borough = str(row_dict[BOROUGH_COLUMN]).strip()
                    logger.debug(f"Using borough from CSV: {query.borough}")
                
                # Fetch property data
                try:
                    result = scraper.fetch(query) or {}
                    status = result.get("status", "error:unknown")
                except Exception as e:
                    logger.error(f"Error processing row {total_processed + 1}: {str(e)}")
                    status = f"error:exception:{str(e)[:100]}"
            
            # Update row with results
            result_row = row_dict.copy()
            if status == "ok":
                for key in OUTPUT_COLUMNS:
                    result_row[key] = result.get(key, "")
                result_row["status"] = "success"
                success_count += 1
                chunk_success += 1
            else:
                result_row["status"] = status
                failure_count += 1
                chunk_failure += 1
                logger.warning(f"Row {total_processed + 1} failed with status: {status}")
            
            # Add timestamp
            result_row["last_updated"] = datetime.now().isoformat()
            updated_chunk.append(result_row)
            total_processed += 1
            chunk_processed += 1
        
        # Write the processed chunk to the output file
        try:
            # Convert to DataFrame for easier CSV writing
            result_df = pd.DataFrame(updated_chunk)
            
            # For the first chunk, write header, otherwise append
            mode = 'w' if first_chunk else 'a'
            header = first_chunk  # Write header only for first chunk
            
            result_df.to_csv(
                output_path,
                mode=mode,
                header=header,
                index=False,
                encoding='utf-8'
            )
            
            logger.info(f"Processed {chunk_processed} rows in this chunk "
                       f"({chunk_success} success, {chunk_failure} failed)")
            
            # Save a checkpoint
            checkpoint_path = output_path.parent / f"{output_path.stem}_checkpoint_{total_processed}{output_path.suffix}"
            result_df.to_csv(checkpoint_path, index=False)
            logger.debug(f"Saved checkpoint to {checkpoint_path}")
            
            first_chunk = False
            
        except Exception as e:
            logger.error(f"Error writing to output file: {str(e)}")
            # Save failed chunk to a backup file
            backup_path = output_path.parent / f"{output_path.stem}_failed_{int(time.time())}.csv"
            pd.DataFrame(updated_chunk).to_csv(backup_path, index=False)
            logger.error(f"Saved failed chunk to {backup_path}")
        
        # Check max rows limit again in case we're in the middle of a chunk
        if max_rows is not None and total_processed >= max_rows:
            logger.info(f"Reached maximum number of rows to process ({max_rows})")
            break
    
    logger.info(f"Processing complete. Total: {total_processed} rows "
               f"({success_count} success, {failure_count} failed)")
    
    # Save final output with all processed data
    return {
        "total_processed": total_processed,
        "success_count": success_count,
        "failure_count": failure_count,
        "output_path": str(output_path)
    }


if __name__ == "__main__":
    main()
