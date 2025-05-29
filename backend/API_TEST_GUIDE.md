# API Testing Guide for Dream11 Team Predictor

This guide explains how to use the test scripts provided to verify the functionality of the Dream11 Team Predictor API, including the ESPNCricinfo scraper integration.

## Setup Instructions

1. Ensure your Django development server is running:
   ```
   cd d:\dream11-team-predictor\backend
   .\env\Scripts\Activate.ps1
   python manage.py runserver
   ```

2. Open a new terminal window for running the test scripts.

## Running the API Tests

The main API test script (`test_api.py`) allows you to test all API endpoints, including core prediction functionality and the ESPNCricinfo scraper integration.

### Basic API Tests

To run all API tests:
```
cd d:\dream11-team-predictor\backend
.\env\Scripts\Activate.ps1
python test_api.py
```

This will:
1. Register a test user (or login if already registered)
2. Test team and venue endpoints
3. Make a team prediction
4. Test the scraper-related endpoints

### Testing Only Scraper Endpoints

If you want to test only the scraper-related endpoints:

```python
# Modify main() in test_api.py to only run scraper tests
def main():
    # Login to get token
    login_response = login_user()
    
    if not login_response:
        print("Login failed. Trying to register...")
        register_response = register_user()
        
        if not register_response:
            print("Registration failed. Exiting.")
            return
            
        # Try login again after registration
        login_response = login_user()
    
    # Extract token
    token = login_response.get('access')
    if not token:
        print("Failed to get access token. Exiting.")
        return
    
    # Run only scraper tests
    test_scraper_functionality(token)
```

## Standalone Scraper Tests

For testing the scraper functionality without involving the API (direct testing):

```
cd d:\dream11-team-predictor\backend
.\env\Scripts\Activate.ps1
python test_cricinfo_scraper.py
```

This will test:
- Scraping IPL matches for a specific season
- Scraping a specific match scorecard
- Scraping a player profile

## Player Statistics Update Tests

To test the player statistics calculation and update mechanism:

```
cd d:\dream11-team-predictor\backend
.\env\Scripts\Activate.ps1
python test_player_stats_update.py
```

This will:
1. Create sample cricket match data if needed
2. Show player statistics before update
3. Run the update process
4. Show player statistics after update and the changes made

## Test Coverage

The test scripts cover the following functionality:

1. **Core API Functions**:
   - User registration and authentication
   - Team and venue listing
   - Player details retrieval
   - Dream11 team prediction

2. **Scraper API Endpoints**:
   - `/api/scrape/match/{match_id}/` - Scrape match scorecards
   - `/api/scrape/player/{player_id}/` - Scrape player profiles
   - `/api/scrape/season/{year}/` - Scrape entire IPL seasons
   - `/api/update-stats/` - Update player statistics based on scraped data

3. **Scraper Core Functionality**:
   - Parsing ESPNCricinfo HTML
   - Extracting batting and bowling statistics
   - Calculating fantasy points
   - Player profile data extraction

## Sample Cricket IDs for Testing

### IPL Match IDs:
- 1370168: IPL 2023 Final (CSK vs GT)
- 1359518: IPL 2023 Match (RCB vs MI)
- 1304111: IPL 2022 Match (CSK vs KKR)

### Player IDs:
- 253802: MS Dhoni
- 34102: Virat Kohli
- 625383: Jasprit Bumrah
- 265755: Ravindra Jadeja
- 227457: Rohit Sharma

### IPL Seasons:
- 2023: Latest completed IPL season
- 2022: Previous IPL season
- 2020: COVID-affected IPL season (held in UAE)

## Troubleshooting

If you encounter any issues with the tests:

1. **Authentication Failures**:
   - Ensure the Django server is running
   - Check the JWT token expiration (tokens expire after 5 minutes by default)

2. **Scraper Issues**:
   - Verify your internet connection
   - ESPNCricinfo might have changed their HTML structure
   - Check for rate limiting (scraper has built-in delays to avoid this)

3. **Database Issues**:
   - Make sure migrations are applied: `python manage.py migrate`
   - Check for schema conflicts if you've modified models
