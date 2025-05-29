## ESPNCricinfo Scraper Command Line Examples

This document provides example commands for using the ESPNCricinfo scraper to collect data for the Dream11 Team Predictor application.

### Installation

Make sure you have the required dependencies installed:

```bash
pip install -r scraper_requirements.txt
```

### Basic Usage

#### 1. Scraping IPL matches for a specific season

```bash
# Scrape 2023 IPL season matches
python manage.py scrape_cricinfo --season 2023

# Scrape with a known series ID
python manage.py scrape_cricinfo --season 2023 --series-id "indian-premier-league-2023-1345038"
```

#### 2. Scraping a specific match

```bash
# Scrape a specific match scorecard
python manage.py scrape_cricinfo --match-url "https://www.espncricinfo.com/series/indian-premier-league-2023-1345038/chennai-super-kings-vs-gujarat-titans-1st-match-1359475/full-scorecard"
```

#### 3. Scraping a player profile

```bash
# Scrape Virat Kohli's profile
python manage.py scrape_cricinfo --player-id 253802

# Scrape MS Dhoni's profile
python manage.py scrape_cricinfo --player-id 28081
```

#### 4. Import existing data to Django models

If you've already scraped data but haven't imported it to the Django models:

```bash
python manage.py scrape_cricinfo --import-only
```

### Updating Player Statistics

After scraping data, update player statistics in the database:

```bash
# Update player stats
python manage.py update_stats

# Dry run to see what would change without modifying the database
python manage.py update_stats --dry-run

# Consider only matches from the last 30 days for "recent form" calculation
python manage.py update_stats --days 30
```

### Example Workflow

Here's a complete workflow for updating player data before a match:

```bash
# 1. Scrape recent IPL matches
python manage.py scrape_cricinfo --season 2023

# 2. Import the data to Django models
python manage.py scrape_cricinfo --import-only

# 3. Update player statistics based on the new data
python manage.py update_stats

# 4. Generate predictions using updated player stats
# (Use your application UI or API for this)
```

### Advanced Usage

#### Using the standalone test script

For testing the scraper outside of the Django management command system:

```bash
python test_scraper.py
```

#### Updating player stats with a custom script

```bash
python update_player_stats.py --dry-run
```

### Finding Player and Series IDs

- **Player IDs**: Visit a player's profile on ESPNCricinfo. The ID is the number at the end of the URL.
  Example: https://www.espncricinfo.com/player/virat-kohli-253802 → ID is 253802

- **Series IDs**: Visit the series page on ESPNCricinfo. The ID is in the URL.
  Example: https://www.espncricinfo.com/series/indian-premier-league-2023-1345038 → ID is "indian-premier-league-2023-1345038"
