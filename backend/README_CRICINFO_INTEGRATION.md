# ESPNCricinfo Integration for Dream11 Team Predictor

This integration scrapes cricket data from ESPNCricinfo and uses it to enhance player statistics and fantasy predictions in the Dream11 Team Predictor application.

## Overview

The ESPNCricinfo integration component consists of:

1. **Web Scraper**: A Python module that scrapes player statistics, match results, and performance data from ESPNCricinfo.
2. **Data Processing**: Tools to process and analyze the scraped data.
3. **Database Integration**: Functions to update the Dream11 Team Predictor database with the latest player statistics.
4. **Management Commands**: Django management commands for easy integration with the application.

## Features

- Scrape IPL (and other cricket tournament) matches
- Collect detailed player statistics from match scorecards
- Gather player profile information including role, batting average, and bowling average
- Calculate fantasy points based on player performances
- Update player statistics in the database
- Track player recent form based on recent matches

## Installation

To use the ESPNCricinfo integration, make sure you have the required dependencies:

```bash
cd backend
pip install -r predictor/management/commands/scraper_requirements.txt
```

## Usage

### Scraping Match Data

You can scrape match data using the Django management command:

```bash
# Navigate to the backend directory
cd backend

# Scrape IPL matches for a specific season
python manage.py scrape_cricinfo --season 2023

# Scrape a specific match
python manage.py scrape_cricinfo --match-url "https://www.espncricinfo.com/series/indian-premier-league-2023-1345038/chennai-super-kings-vs-gujarat-titans-final-1370353/full-scorecard"

# Scrape a player profile
python manage.py scrape_cricinfo --player-id 253802  # Virat Kohli
```

### Using the API Endpoints

All API endpoints require authentication. After obtaining a token, you can call:

1. **Scrape Match**:
   ```http
   POST /api/scrape/match/1370168/
   Content-Type: application/json
   Authorization: Bearer <your_token>

   {
     "update_stats": true
   }
   ```

2. **Scrape Player**:
   ```http
   POST /api/scrape/player/253802/
   Content-Type: application/json
   Authorization: Bearer <your_token>

   {
     "update_stats": true
   }
   ```

3. **Scrape Season**:
   ```http
   POST /api/scrape/season/2023/
   Content-Type: application/json
   Authorization: Bearer <your_token>

   {
     "scrape_matches": true,
     "limit_matches": true,
     "update_stats": true
   }
   ```

4. **Update Stats**:
   ```http
   POST /api/update-stats/
   Content-Type: application/json
   Authorization: Bearer <your_token>

   {
     "dry_run": false,
     "days": 90
   }
   ```

### Updating Player Statistics

After scraping data, update player statistics in the database:

```bash
# Update all player statistics based on scraped data
python manage.py update_stats

# Run a dry-run update to preview changes
python manage.py update_stats --dry-run

# Consider only recent matches (e.g., last 30 days)
python manage.py update_stats --days 30
```

### Testing the Integration

There are several test scripts to verify the functionality:

```bash
# Test the scraper functionality
python test_cricinfo_scraper.py

# Test the player statistics update
python test_player_stats_update.py

# Test the full integration with the API
python test_api.py

# Test specific API components (core or scraper)
python simple_test_api.py --type scraper
```

For more detailed testing instructions, see the `API_TEST_GUIDE.md` file.

## How It Works

### 1. Data Collection

The scraper collects the following data from ESPNCricinfo:

- **Match Results**: Teams, venues, dates, and outcomes
- **Player Performances**: Runs, wickets, strike rates, economy rates
- **Player Profiles**: Career statistics, player roles, team affiliations

### 2. Data Processing

Raw data is processed to:

- Calculate fantasy points based on performance metrics
- Determine player recent form
- Update batting and bowling averages

### 3. Database Integration

The processed data is used to update the Django models:

- `Player` model: batting_average, bowling_average, recent_form
- `Team` model: new teams discovered in scraped data
- `Venue` model: new venues discovered in scraped data

### 4. Prediction Enhancement

The updated statistics are used by the prediction algorithm to generate more accurate team predictions based on:

- Current player form
- Historical performance
- Match conditions

## Directory Structure

```
backend/
  ├── predictor/
  │   ├── management/
  │   │   ├── commands/
  │   │   │   ├── scrape_cricinfo.py     # ESPNCricinfo scraper command
  │   │   │   ├── update_stats.py        # Player statistics update command
  │   │   │   ├── cricket_data/          # Scraped data storage (created automatically)
  │   │   │   ├── scraper_requirements.txt  # Dependencies
  │   │   │   ├── README_cricinfo_scraper.md  # Detailed documentation
  │   │   │   └── scraper_examples.md    # Example usage
  ├── test_cricinfo_scraper.py        # Scraper test script
  └── test_player_stats_update.py     # Statistics update test script
```

## Contributing

To enhance the ESPNCricinfo integration:

1. Improve the scraper to handle more cricket tournaments
2. Add more sophisticated player matching algorithms
3. Enhance the fantasy points calculation logic
4. Develop more advanced recent form metrics

## Troubleshooting

**The scraper fails to find data**:
- ESPNCricinfo may have updated their HTML structure. Check the CSS selectors in the scraper code.
- The URL format may have changed. Verify the URLs manually.

**Player statistics aren't updating**:
- Check that the player names in the database match those on ESPNCricinfo.
- Verify that the scraped data files exist in the cricket_data directory.

**Import errors**:
- Make sure you've installed all dependencies from scraper_requirements.txt
- Ensure your Django environment is properly configured

## Future Enhancements

1. **Machine Learning Integration**: Use historical data to predict player performance
2. **Recent Form Weighting**: Give more weight to more recent matches
3. **Opposition Analysis**: Consider past performance against specific teams
4. **Venue Performance**: Factor in player performance at specific venues
5. **Automated Scraping**: Set up scheduled tasks to automatically update player data
