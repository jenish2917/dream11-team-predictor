# Dream11 Team Predictor API Guide

This document provides guidance on using the API endpoints for the Dream11 Team Predictor application, including the ESPNCricinfo scraper integration.

## Authentication

### Register a New User

**Request:**
```
POST /api/register/
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "testpassword123",
  "password2": "testpassword123", 
  "first_name": "Test",
  "last_name": "User"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  },
  "refresh": "eyJ0eX...",
  "access": "eyJ0eX..."
}
```

### Login

**Request:**
```
POST /api/login/
{
  "username": "testuser",
  "password": "testpassword123"
}
```

**Response:**
```json
{
  "refresh": "eyJ0eX...",
  "access": "eyJ0eX..."
}
```

### Refresh Token

**Request:**
```
POST /api/token/refresh/
{
  "refresh": "eyJ0eX..."
}
```

**Response:**
```json
{
  "access": "eyJ0eX..."
}
```

## Core API Endpoints

### Get Teams

**Request:**
```
GET /api/teams/
Headers:
  Authorization: Bearer eyJ0eX...
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Chennai Super Kings",
    "short_name": "CSK",
    "logo": null
  },
  {
    "id": 2,
    "name": "Mumbai Indians",
    "short_name": "MI",
    "logo": null
  }
]
```

### Get Team Players

**Request:**
```
GET /api/teams/1/players/
Headers:
  Authorization: Bearer eyJ0eX...
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "MS Dhoni",
    "team": 1,
    "role": "WK",
    "batting_average": 38.5,
    "bowling_average": 0.0,
    "recent_form": 38.5
  },
  {
    "id": 2,
    "name": "Ravindra Jadeja",
    "team": 1,
    "role": "AR",
    "batting_average": 26.4,
    "bowling_average": 29.7,
    "recent_form": 26.4
  }
]
```

### Get Venues

**Request:**
```
GET /api/venues/
Headers:
  Authorization: Bearer eyJ0eX...
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "M. A. Chidambaram Stadium",
    "city": "Chennai",
    "country": "India"
  },
  {
    "id": 2,
    "name": "Wankhede Stadium",
    "city": "Mumbai",
    "country": "India"
  }
]
```

### Make a Prediction

**Request:**
```
POST /api/predict-team/
Headers:
  Authorization: Bearer eyJ0eX...
  Content-Type: application/json
{
  "team1": 1,
  "team2": 2,
  "venue": 1,
  "pitch_type": "BAL"
}
```

**Response:**
```json
{
  "predictions": {
    "AGG": [
      {
        "player_id": 1,
        "player_name": "MS Dhoni",
        "team": "CSK",
        "role": "WK",
        "expected_points": 45.2,
        "is_captain": true,
        "is_vice_captain": false
      },
      ...
    ],
    "BAL": [...],
    "RISK": [...]
  }
}
```

## ESPNCricinfo Scraper API

### Scrape Match

**Request:**
```
POST /api/scrape/match/1370353/
Headers:
  Authorization: Bearer eyJ0eX...
  Content-Type: application/json
{
  "update_stats": true
}
```

**Response:**
```json
{
  "match_id": "1370353",
  "url": "https://www.espncricinfo.com/matches/engine/match/1370353.html",
  "batting_performances": 22,
  "bowling_performances": 10,
  "teams": ["Chennai Super Kings", "Gujarat Titans"],
  "top_scorer": "Devon Conway",
  "top_wicket_taker": "Ravindra Jadeja",
  "data_imported": true,
  "player_stats_updated": true
}
```

### Scrape Player

**Request:**
```
POST /api/scrape/player/253802/
Headers:
  Authorization: Bearer eyJ0eX...
  Content-Type: application/json
{
  "update_stats": true
}
```

**Response:**
```json
{
  "name": "Virat Kohli",
  "role": "BAT",
  "team": "Royal Challengers Bangalore",
  "batting_average": 37.9,
  "bowling_average": 33.9,
  "recent_form": 37.9,
  "data_imported": true
}
```

### Scrape Season

**Request:**
```
POST /api/scrape/season/2023/
Headers:
  Authorization: Bearer eyJ0eX...
  Content-Type: application/json
{
  "series_id": "indian-premier-league-2023-1345038",
  "scrape_matches": true,
  "limit_matches": true,
  "update_stats": true
}
```

**Response:**
```json
{
  "season": 2023,
  "matches_found": 74,
  "series_id": "indian-premier-league-2023-1345038",
  "teams": ["Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bangalore", "..."],
  "venues": ["M. A. Chidambaram Stadium", "Wankhede Stadium", "..."],
  "match_details_scraped": 5,
  "data_imported": true,
  "player_stats_updated": true
}
```

### Update Player Stats

**Request:**
```
POST /api/update-stats/
Headers:
  Authorization: Bearer eyJ0eX...
  Content-Type: application/json
{
  "dry_run": false,
  "days": 90
}
```

**Response:**
```json
{
  "dry_run": false,
  "days_considered": 90,
  "players_updated": 15,
  "updated_players": [
    {
      "player_id": 1,
      "player_name": "MS Dhoni",
      "old_batting_average": 38.5,
      "new_batting_average": 42.3,
      "old_recent_form": 38.5,
      "new_recent_form": 45.1
    },
    ...
  ],
  "note": "Showing only the first 10 of 15 updated players"
}
```

## Using Postman to Test the API

1. Create a new Postman Collection called "Dream11 Team Predictor API"

2. Create a folder called "Authentication"
   - Add requests for Register, Login, and Refresh Token

3. Create a folder called "Core API"
   - Add requests for Teams, Venues, Players, and Predictions

4. Create a folder called "ESPNCricinfo Integration"
   - Add requests for Scrape Match, Scrape Player, Scrape Season, and Update Stats

5. Set up a Collection-level variable for `base_url` with value `http://localhost:8000/api`

6. Set up an environment with the following variables:
   - `access_token`: Empty initially, will be filled after login
   - `refresh_token`: Empty initially, will be filled after login

7. Create a Pre-request Script at the Collection level to automatically include the authentication token:
   ```javascript
   if (pm.environment.get('access_token')) {
     pm.request.headers.add({
       key: 'Authorization',
       value: 'Bearer ' + pm.environment.get('access_token')
     });
   }
   ```

8. Create a Test script for the Login request to automatically set the tokens:
   ```javascript
   var jsonData = pm.response.json();
   if (jsonData.access) {
     pm.environment.set('access_token', jsonData.access);
   }
   if (jsonData.refresh) {
     pm.environment.set('refresh_token', jsonData.refresh);
   }
   ```

9. Test the API flow:
   - Register a new user or login
   - Get teams and venues
   - Make predictions
   - Use the ESPNCricinfo integration to update player statistics
   - Make predictions again to see if they've improved
