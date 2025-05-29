# Player Statistics Processing Guide

This guide explains how to use the player statistics processing functionality that enhances player data with advanced metrics and visualizations.

## Overview

The player statistics processing module takes the raw data scraped from ESPNCricinfo and performs:

1. **Data Cleaning** - Standardizes column names, handles missing values, and converts data types
2. **Feature Engineering** - Calculates consistency indices, performance metrics against specific teams/venues
3. **Player Profile Generation** - Creates comprehensive player profiles with advanced statistics
4. **Performance Visualization** - Generates performance charts for visual analysis

## Usage Instructions

### Command Line Usage

Use the Django management command to process player statistics:

```bash
# Process all players
python manage.py enhance_player_stats

# Process a specific player
python manage.py enhance_player_stats --player "Virat Kohli"

# Generate performance plots
python manage.py enhance_player_stats --plots

# Export player profiles as JSON and CSV
python manage.py enhance_player_stats --export both

# Update database with processed stats
python manage.py enhance_player_stats --update-db

# Preview changes without updating database
python manage.py enhance_player_stats --update-db --dry-run
```

### API Usage

The player statistics processing functionality is also available through API endpoints:

#### 1. Process Player Statistics

```http
POST /api/enhance-player-stats/
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "dry_run": true,
  "export_format": "json",
  "generate_plots": true
}
```

Response:
```json
{
  "status": "success",
  "dry_run": true,
  "generated_files": [
    {"type": "json_profiles", "path": "cricket_data/player_profiles_20250529_123045.json"},
    {"type": "form_plot", "path": "cricket_data/plots/virat_kohli_recent_form.png"}
  ]
}
```

#### 2. Process Specific Player

```http
POST /api/enhance-player-stats/
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "player": "MS Dhoni",
  "generate_plots": true
}
```

#### 3. Get Enhanced Player Stats

```http
GET /api/players/1/enhanced_stats/
Authorization: Bearer <your_token>
```

Response:
```json
{
  "name": "MS Dhoni",
  "role": "WK",
  "team": "Chennai Super Kings",
  "average_runs_last_5": 45.6,
  "average_wickets_last_5": 0,
  "batting_consistency_index": 7.8,
  "bowling_consistency_index": 0,
  "performance_vs_opposition": {
    "Mumbai Indians": {"matches": 4, "avg_runs": 35.5},
    "Royal Challengers Bangalore": {"matches": 3, "avg_runs": 42.3}
  },
  "venue_stats": {
    "Wankhede Stadium": {"matches": 3, "avg_runs": 38.7},
    "M. A. Chidambaram Stadium": {"matches": 5, "avg_runs": 45.2}
  }
}
```

#### 4. Get Player Performance Chart

```http
GET /api/players/1/performance_chart/?type=form
Authorization: Bearer <your_token>
```

Response:
```json
{
  "player": "MS Dhoni",
  "chart_type": "form",
  "chart_url": "http://localhost:8000/media/player_charts/ms_dhoni_recent_form.png",
  "chart_path": "d:\\dream11-team-predictor\\backend\\predictor\\management\\commands\\cricket_data\\plots\\ms_dhoni_recent_form.png"
}
```

## Player Profile Structure

Each player profile contains the following information:

| Field | Description |
|-------|-------------|
| `name` | Player name |
| `role` | Player role (BAT, BWL, AR, WK) |
| `team` | Player's current team |
| `average_runs_last_5` | Average runs in last 5 matches |
| `average_wickets_last_5` | Average wickets in last 5 matches |
| `batting_consistency_index` | Index measuring batting consistency (1-10) |
| `bowling_consistency_index` | Index measuring bowling consistency (1-10) |
| `performance_vs_opposition` | Performance data against each team |
| `venue_stats` | Performance data at each venue |
| `avg_fantasy_points` | Average fantasy points per match |

## Consistency Index

The consistency index is calculated using the following formula:

```
Consistency Index = (Mean ÷ (Standard Deviation + 1)) × 10
```

This provides a score between 0-10, where higher scores indicate more consistent performance. The formula rewards players with:
- Higher average performance
- Lower variation in performance

## Available Charts

1. **Recent Form Chart** - Line chart showing runs/wickets over last 5 matches
2. **Opposition Performance Chart** - Bar chart showing average runs/wickets against different teams
3. **Venue Performance Chart** - Bar chart showing average runs/wickets at different venues

## Testing

To test the player statistics processing module:

```bash
python test_player_stats_processor.py
```

This will:
1. Create sample cricket data
2. Test data processing
3. Generate player profiles
4. Create sample charts

## Integration with Dream11 Predictions

The enhanced player statistics are automatically used by the prediction algorithm to generate more accurate team predictions based on:

- Player consistency
- Performance against specific opponents
- Performance at specific venues

This results in better fantasy team selections with higher probability of success.
