@echo off
echo Running ESPNCricinfo scraper for 2025 IPL data...
python manage.py scrape_cricinfo --season 2025

echo.
echo Cleaning up old match data (preserving all player, team, and venue data)...
echo Only keeping 2025 IPL matches...
python manage.py scrape_cricinfo --clean-seed-data

echo.
echo Scraping and import process completed.
echo All player data is preserved!
