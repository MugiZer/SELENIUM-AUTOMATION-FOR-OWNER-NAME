# Quick Setup Guide

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python environment management. **No prior Python installation needed!**

## 🚀 One-Command Setup

### Windows
```bash
setup.bat
```

### macOS/Linux
```bash
bash setup.sh
```

This will automatically:
- ✅ Install uv (if not already installed)
- ✅ Install Python 3.11 (if needed)
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Install Playwright browsers
- ✅ Create necessary directories
- ✅ Set up configuration files

## 🏃 Running the Automation

### Option 1: Quick Run (Recommended)

**Windows:**
```bash
run.bat "your-file.csv" --headless
```

**macOS/Linux:**
```bash
bash run.sh "your-file.csv" --headless
```

### Option 2: Manual Run

**Activate environment first:**
```bash
# Windows
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

**Then run:**
```bash
python main.py "your-file.csv" --headless
```

## 📋 Command-Line Options

```bash
# Process entire CSV file
python main.py input.csv --headless

# Process only first 10 rows
python main.py input.csv --headless --max-rows 10

# Show browser while running (helpful for debugging)
python main.py input.csv

# Process with custom output file
python main.py input.csv --output-file results.csv --headless

# Enable debug logging
python main.py input.csv --headless --debug
```

## 🔧 Configuration

Edit `.env` file to configure:
- Montreal account credentials (optional, for login)
- Delay between requests
- Output directories
- Logging level

## 📂 Input CSV Format

Your CSV should have these columns (French or English names):
- `CIVIQUE_DEBUT` or `civic_number` - Building number
- `NOM_RUE` or `street_name` - Street name
- `NO_ARROND_ILE_CUM` or `borough` - Borough/neighborhood (optional but recommended)

Example:
```csv
CIVIQUE_DEBUT,NOM_RUE,NO_ARROND_ILE_CUM
810,rue de Liège Ouest,Arrondissement de Villeray - Saint-Michel - Parc-Extension (Montréal)
52,Academy Road,(Westmount)
```

## 📤 Output

Processed files are saved to the `output/` directory with:
- All original columns preserved
- Additional columns with property data:
  - `owner_names`
  - `matricule`
  - `tax_account_number`
  - `assessed_total_current`
  - And many more...

## 🆘 Troubleshooting

### uv not found after installation
Close and reopen your terminal/command prompt.

### Permission errors on Linux/macOS
```bash
chmod +x setup.sh run.sh
```

### Playwright browser issues
```bash
# Reinstall browsers
source .venv/bin/activate  # or .venv\Scripts\activate.bat on Windows
playwright install chromium --with-deps
```

### Reset everything
Delete the `.venv` directory and run `setup.sh` or `setup.bat` again.

## 💡 Why uv?

- **Fast**: 10-100x faster than pip
- **Reliable**: Deterministic dependency resolution
- **Self-contained**: Manages Python versions automatically
- **Cross-platform**: Works on Windows, macOS, Linux

## 📚 More Information

- Full documentation: [README.md](README.md)
- uv documentation: https://github.com/astral-sh/uv
