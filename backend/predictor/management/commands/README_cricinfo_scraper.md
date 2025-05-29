# ESPNCricinfo Scraper for Dream11 Team Predictor

This tool scrapes cricket data from ESPNCricinfo and imports it into the Dream11 Team Predictor database.

## Features

- Scrape IPL matches for specific seasons
- Scrape detailed match scorecards
- Scrape player profiles and statistics
- Automatically calculate fantasy points based on player performances
- Import all scraped data into Django database models

## Usage

The scraper is implemented as a Django management command, so you can run it from the command line:

```bash
# Navigate to your project directory
cd dream11-team-predictor/backend

# Activate your virtual environment (if you're using one)
# source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# Scrape IPL matches for a specific season
python manage.py scrape_cricinfo --season 2023

# Scrape a specific match using its URL
python manage.py scrape_cricinfo --match-url "https://www.espncricinfo.com/series/indian-premier-league-2023-1345038/chennai-super-kings-vs-gujarat-titans-1st-match-1359475/full-scorecard"

# Scrape a specific player's profile (requires the player ID from ESPNCricinfo)
python manage.py scrape_cricinfo --player-id 253802  # Virat Kohli's ID

# Import existing scraped data into Django models without scraping new data
python manage.py scrape_cricinfo --import-only
```

## Data Directory

The scraper creates a `cricket_data` directory inside the `management/commands` folder to store:

- CSV files with scraped data
- SQLite database for intermediate storage before importing to Django

## Scraped Data

The scraper collects the following data:

### Teams
- Team names
- Short names (abbreviations)
- ESPNCricinfo IDs

### Players
- Player names
- Team affiliations
- Player roles (BAT, BWL, AR, WK)
- Batting averages
- Bowling averages
- Recent form metrics
- ESPNCricinfo IDs

### Matches
- Match dates and venues
- Teams involved
- Match results
- Match IDs

### Player Performances
- Runs scored and balls faced
- Fours and sixes hit
- Wickets taken
- Overs bowled
- Runs conceded
- Calculated fantasy points

## Integration with Dream11 Predictor

The scraped data is used by the prediction algorithm to generate optimal team compositions based on:

- Player recent performance
- Player statistics (batting/bowling averages)
- Match conditions (venue, pitch type)

This real-world data significantly improves the accuracy of team predictions compared to using static or manually entered data.
