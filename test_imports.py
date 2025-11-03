try:
    from scraper.montreal_role import MontrealRoleScraper
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
    raise
