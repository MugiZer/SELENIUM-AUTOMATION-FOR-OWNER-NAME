import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator
from .schema import OUTPUT_COLUMNS, BOROUGH_COLUMN

class CSVHandler:
    def __init__(self, input_path: str, output_path: Optional[str] = None):
        """
        Initialize CSV handler with input and optional output paths.
        If output_path is not provided, will append '_output' to the input filename.
        """
        self.input_path = Path(input_path)
        if output_path:
            self.output_path = Path(output_path)
        else:
            # Add _output before the extension
            self.output_path = self.input_path.parent / f"{self.input_path.stem}_output{self.input_path.suffix}"
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def read_rows(self) -> Tuple[List[str], List[Dict[str, str]]]:
        """Read rows from input CSV and return header and rows."""
        with open(self.input_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            rows = list(reader)
        return header, rows
    
    def write_output(self, header: List[str], rows: List[Dict[str, str]]) -> None:
        """Write processed rows to output CSV."""
        # Ensure all output columns are in the header
        output_header = header.copy()
        for col in OUTPUT_COLUMNS:
            if col not in output_header:
                output_header.append(col)
        
        with open(self.output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=output_header)
            writer.writeheader()
            writer.writerows(rows)
    
    def process_in_chunks(self, chunk_size: int = 20) -> Generator[Tuple[List[Dict[str, str]], int, int], None, None]:
        """Process input CSV in chunks to handle large files efficiently."""
        with open(self.input_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            
            chunk = []
            for i, row in enumerate(reader, start=1):
                chunk.append(row)
                if len(chunk) >= chunk_size:
                    yield header, chunk, i - len(chunk) + 1, i
                    chunk = []
            
            if chunk:
                yield header, chunk, max(1, i - len(chunk) + 1), i or 1
    
    def ensure_columns(self, row: Dict[str, str]) -> Dict[str, str]:
        """Ensure all output columns exist in the row."""
        for col in OUTPUT_COLUMNS:
            if col not in row:
                row[col] = ""
        return row
    
    def has_borough_column(self, header: List[str]) -> bool:
        """Check if the header contains the borough column."""
        return BOROUGH_COLUMN in header
