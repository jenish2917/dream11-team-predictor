# PowerShell script for scraping 2025 IPL data
Write-Host "Running ESPNCricinfo scraper for 2025 IPL data..." -ForegroundColor Cyan
python manage.py scrape_cricinfo --season 2025

Write-Host ""
Write-Host "Cleaning up old match data (preserving all player, team, and venue data)..." -ForegroundColor Yellow
Write-Host "Only keeping 2025 IPL matches..." -ForegroundColor Yellow
python manage.py scrape_cricinfo --clean-seed-data

Write-Host ""
Write-Host "Scraping and import process completed." -ForegroundColor Green
Write-Host "All player data is preserved!" -ForegroundColor Green
