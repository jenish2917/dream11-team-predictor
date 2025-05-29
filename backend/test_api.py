# Test API requests for Dream11 Predictor
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000/api"

# Register a new user
def register_user():
    url = f"{BASE_URL}/register/"
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "password2": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(url, json=payload)
    print("Register Response Status:", response.status_code)
    print("Register Response:", response.json() if response.status_code < 400 else response.text)
    return response.json() if response.status_code < 400 else None

# Login with user credentials
def login_user():    
    url = f"{BASE_URL}/login/"
    payload = {
        "username": "testuser",
        "password": "testpassword123"
    }
    # For Simple JWT, the payload is different from what we'd normally use
    
    response = requests.post(url, json=payload)
    print("Login Response Status:", response.status_code)
    print("Login Response:", response.json() if response.status_code < 400 else response.text)
    return response.json() if response.status_code < 400 else None

# Get list of teams
def get_teams(token):
    url = f"{BASE_URL}/teams/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    print("Teams Response Status:", response.status_code)
    print("Teams Response:", response.json() if response.status_code < 400 else response.text)
    return response.json() if response.status_code < 400 else None

# Get list of venues
def get_venues(token):
    url = f"{BASE_URL}/venues/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    print("Venues Response Status:", response.status_code)
    print("Venues Response:", response.json() if response.status_code < 400 else response.text)
    return response.json() if response.status_code < 400 else None

# Make a prediction
def make_prediction(token, team1_id, team2_id, venue_id, pitch_type):
    url = f"{BASE_URL}/predict-team/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "team1": team1_id,
        "team2": team2_id,
        "venue": venue_id,
        "pitch_type": pitch_type
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print("Prediction Response Status:", response.status_code)
    print("Prediction Response:", response.json() if response.status_code < 400 else response.text)
    return response.json() if response.status_code < 400 else None

# Get all players for a team
def get_team_players(token, team_id):
    url = f"{BASE_URL}/teams/{team_id}/players/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"Team {team_id} Players Response Status:", response.status_code)
    if response.status_code < 400:
        players = response.json()
        print(f"Found {len(players)} players for team {team_id}")
    else:
        print("Players Response:", response.text)
    
    return response.json() if response.status_code < 400 else None

# Get player details
def get_player_details(token, player_id):
    url = f"{BASE_URL}/players/{player_id}/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"Player {player_id} Details Response Status:", response.status_code)
    if response.status_code < 400:
        player = response.json()
        print(f"Player: {player['name']}, Role: {player['role']}")
        print(f"Batting Avg: {player['batting_average']}, Bowling Avg: {player['bowling_average']}")
        print(f"Recent Form: {player['recent_form']}")
    else:
        print("Player Details Response:", response.text)
    
    return response.json() if response.status_code < 400 else None

# Test the ESPNCricinfo scraper - Match
def test_scrape_match(token, match_id="1370168"):
    """
    Test the match scraper endpoint.
    Args:
        token: Authentication token
        match_id: ESPNCricinfo match ID (default: 1370168 - IPL 2023 final)
    """
    url = f"{BASE_URL}/scrape/match/{match_id}/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "update_stats": False  # Set to True if you want to update player stats after scraping
    }
    
    print(f"\n--- Testing Match Scraper for match ID: {match_id} ---")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Match Scraper Response Status: {response.status_code}")
    
    if response.status_code < 400:
        data = response.json()
        print(f"Successfully scraped match data:")
        print(f"Teams: {data.get('teams', [])}")
        print(f"Batting performances: {data.get('batting_performances', 0)}")
        print(f"Bowling performances: {data.get('bowling_performances', 0)}")
        print(f"Top scorer: {data.get('top_scorer', 'N/A')}")
        print(f"Top wicket taker: {data.get('top_wicket_taker', 'N/A')}")
    else:
        print(f"Failed to scrape match: {response.text}")
    
    return response.json() if response.status_code < 400 else None

# Test the ESPNCricinfo scraper - Player
def test_scrape_player(token, player_id="253802"):
    """
    Test the player scraper endpoint.
    Args:
        token: Authentication token
        player_id: ESPNCricinfo player ID (default: 253802 - MS Dhoni)
    """
    url = f"{BASE_URL}/scrape/player/{player_id}/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "update_stats": False  # Set to True if you want to update player stats after scraping
    }
    
    print(f"\n--- Testing Player Scraper for player ID: {player_id} ---")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Player Scraper Response Status: {response.status_code}")
    
    if response.status_code < 400:
        data = response.json()
        print(f"Successfully scraped player data:")
        print(f"Name: {data.get('name', 'N/A')}")
        print(f"Teams: {', '.join(data.get('teams', []))}")
        print(f"Batting Style: {data.get('batting_style', 'N/A')}")
        print(f"Bowling Style: {data.get('bowling_style', 'N/A')}")
        
        # Print some T20 stats if available
        batting_stats = data.get('batting_stats', {}).get('t20', {})
        bowling_stats = data.get('bowling_stats', {}).get('t20', {})
        
        if batting_stats:
            print(f"T20 Batting - Matches: {batting_stats.get('matches', 'N/A')}, "
                  f"Runs: {batting_stats.get('runs', 'N/A')}, "
                  f"Average: {batting_stats.get('average', 'N/A')}, "
                  f"Strike Rate: {batting_stats.get('strike_rate', 'N/A')}")
        
        if bowling_stats:
            print(f"T20 Bowling - Matches: {bowling_stats.get('matches', 'N/A')}, "
                  f"Wickets: {bowling_stats.get('wickets', 'N/A')}, "
                  f"Economy: {bowling_stats.get('economy', 'N/A')}, "
                  f"Average: {bowling_stats.get('average', 'N/A')}")
    else:
        print(f"Failed to scrape player: {response.text}")
    
    return response.json() if response.status_code < 400 else None

# Test the ESPNCricinfo scraper - Season
def test_scrape_season(token, year=2023):
    """
    Test the season scraper endpoint.
    Args:
        token: Authentication token
        year: IPL season year (default: 2023)
    """
    url = f"{BASE_URL}/scrape/season/{year}/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "scrape_matches": False,  # Set to True to also scrape match details (limited to 5 by default)
        "limit_matches": True,    # Limit to 5 matches if scrape_matches=True
        "update_stats": False     # Set to True to update player stats after scraping
    }
    
    print(f"\n--- Testing Season Scraper for IPL {year} ---")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Season Scraper Response Status: {response.status_code}")
    
    if response.status_code < 400:
        data = response.json()
        print(f"Successfully scraped season data:")
        print(f"Season: {data.get('season', 'N/A')}")
        print(f"Matches found: {data.get('matches_found', 0)}")
        print(f"Teams: {data.get('teams', [])}")
        print(f"Venues: {data.get('venues', [])}")
        
        if data.get('match_details_scraped') is not None:
            print(f"Match details scraped: {data.get('match_details_scraped')}")
    else:
        print(f"Failed to scrape season: {response.text}")
    
    return response.json() if response.status_code < 400 else None

# Test the player stats update
def test_update_player_stats(token):
    """
    Test the player stats update endpoint.
    Args:
        token: Authentication token
    """
    url = f"{BASE_URL}/update-stats/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "dry_run": True,  # Set to False to actually update the database
        "days": 90        # Consider performances from the last 90 days for recent form
    }
    
    print("\n--- Testing Player Stats Update ---")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Stats Update Response Status: {response.status_code}")
    
    if response.status_code < 400:
        data = response.json()
        print(f"Player stats update details:")
        print(f"Dry run: {data.get('dry_run', True)}")
        print(f"Days considered: {data.get('days_considered', 0)}")
        print(f"Players updated: {data.get('players_updated', 0)}")
        
        # Show some of the updated players
        for player in data.get('updated_players', []):
            print(f"\nPlayer: {player.get('player_name')}")
            
            if 'old_batting_average' in player:
                print(f"  Batting avg: {player.get('old_batting_average')} → {player.get('new_batting_average')}")
            
            if 'old_bowling_average' in player:
                print(f"  Bowling avg: {player.get('old_bowling_average')} → {player.get('new_bowling_average')}")
            
            if 'old_recent_form' in player:
                print(f"  Recent form: {player.get('old_recent_form')} → {player.get('new_recent_form')}")
    else:
        print(f"Failed to update player stats: {response.text}")
    
    return response.json() if response.status_code < 400 else None

# Test the enhanced player stats endpoint
def test_enhance_player_stats(token):
    """
    Test the player stats enhancement endpoint.
    Args:
        token: Authentication token
    """
    url = f"{BASE_URL}/enhance-player-stats/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "dry_run": True,
        "export_format": "both",
        "generate_plots": True
    }
    
    print(f"\n--- Testing Enhanced Player Stats ---")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Enhanced Stats Response Status: {response.status_code}")
    
    if response.status_code < 400:
        data = response.json()
        print(f"Successfully processed enhanced player stats:")
        print(f"Status: {data.get('status', 'N/A')}")
        print(f"Dry run: {data.get('dry_run', True)}")
        
        # Show generated files
        generated_files = data.get('generated_files', [])
        if generated_files:
            print(f"Generated {len(generated_files)} files:")
            for file_info in generated_files:
                print(f"- {file_info.get('type')}: {file_info.get('path')}")
        
        # Show plot information if available
        top_plots = data.get('top_player_plots', [])
        if top_plots:
            print(f"Generated plots for top players:")
            for plot in top_plots:
                print(f"- {plot.get('player')}: {plot.get('type')} plot")
    else:
        print(f"Failed to process enhanced stats: {response.text}")
    
    # Test for a specific player
    player_name = "MS Dhoni"  # Choose a player likely to be in the database
    player_payload = {
        "player": player_name,
        "dry_run": True,
        "generate_plots": True
    }
    
    print(f"\n--- Testing Enhanced Stats for {player_name} ---")
    response = requests.post(url, headers=headers, json=player_payload)
    print(f"Player Stats Response Status: {response.status_code}")
    
    if response.status_code < 400:
        data = response.json()
        print(f"Successfully processed stats for {player_name}:")
        if 'profile' in data:
            profile = data['profile']
            print(f"Role: {profile.get('role', 'Unknown')}")
            print(f"Batting avg (last 5): {profile.get('average_runs_last_5', 0)}")
            print(f"Wickets avg (last 5): {profile.get('average_wickets_last_5', 0)}")
            print(f"Consistency index: {profile.get('batting_consistency_index', 0)}")
            
            # Show opposition data if available
            opposition = profile.get('performance_vs_opposition', {})
            if opposition:
                print("Performance vs teams:")
                for team, stats in list(opposition.items())[:2]:  # Show only first 2
                    print(f"- {team}: {stats.get('avg_runs', 0)} runs in {stats.get('matches', 0)} matches")
        
        # Show generated files
        generated_files = data.get('generated_files', [])
        if generated_files:
            print(f"Generated files for {player_name}:")
            for file_info in generated_files:
                print(f"- {file_info.get('type')}: {file_info.get('path')}")
    else:
        print(f"Failed to process stats for {player_name}: {response.text}")
    
    return response.json() if response.status_code < 400 else None

# Test player profile API with enhanced stats
def test_player_enhanced_stats(token, player_id):
    """
    Test the player enhanced stats API endpoint.
    Args:
        token: Authentication token
        player_id: Player ID
    """
    url = f"{BASE_URL}/players/{player_id}/enhanced_stats/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n--- Testing Player Enhanced Stats API for Player {player_id} ---")
    response = requests.get(url, headers=headers)
    print(f"Enhanced Stats API Response Status: {response.status_code}")
    
    if response.status_code < 400:
        data = response.json()
        print(f"Successfully retrieved enhanced stats:")
        print(f"Player: {data.get('name', 'Unknown')}")
        print(f"Team: {data.get('team', 'Unknown')}")
        print(f"Role: {data.get('role', 'Unknown')}")
        print(f"Batting consistency: {data.get('batting_consistency_index', 0)}")
        print(f"Average runs (last 5): {data.get('average_runs_last_5', 0)}")
        
        # Show opposition data if available
        opposition = data.get('performance_vs_opposition', {})
        if opposition:
            print("Performance vs teams:")
            for team, stats in list(opposition.items())[:2]:  # Show only first 2
                print(f"- {team}: {stats.get('avg_runs', 0)} runs in {stats.get('matches', 0)} matches")
    else:
        print(f"Failed to retrieve enhanced stats: {response.text}")
    
    # Test the performance chart API
    chart_url = f"{BASE_URL}/players/{player_id}/performance_chart/"
    chart_params = {"type": "form"}  # or "opposition"
    
    print(f"\n--- Testing Performance Chart API ---")
    response = requests.get(chart_url, headers=headers, params=chart_params)
    print(f"Chart API Response Status: {response.status_code}")
    
    if response.status_code < 400:
        data = response.json()
        print(f"Successfully retrieved chart data:")
        print(f"Chart type: {data.get('chart_type', 'Unknown')}")
        print(f"Chart URL: {data.get('chart_url', 'None')}")
    else:
        print(f"Failed to retrieve chart data: {response.text}")
    
    return response.json() if response.status_code < 400 else None

# Run a test based on scraped data
def test_with_scraped_data(token):
    """
    Test making predictions with the latest scraped data.
    This demonstrates how the scraper enhances the prediction system.
    """
    print("\n=== Testing with Scraped Cricket Data ===\n")
    
    # Get teams
    teams = get_teams(token)
    if not teams or len(teams) < 2:
        print("Failed to get teams or not enough teams. Exiting.")
        return
    
    # Get venues
    venues = get_venues(token)
    if not venues or len(venues) < 1:
        print("Failed to get venues. Exiting.")
        return
    
    # Get players for each team
    print("\n--- Team Players ---")
    team1_players = get_team_players(token, teams[0]['id'])
    team2_players = get_team_players(token, teams[1]['id'])
    
    if not team1_players or not team2_players:
        print("Failed to get players. Exiting.")
        return
    
    # Look at some player details
    print("\n--- Player Details ---")
    if team1_players:
        get_player_details(token, team1_players[0]['id'])
    
    if team2_players:
        get_player_details(token, team2_players[0]['id'])
    
    # Make predictions for different pitch types
    print("\n--- Predictions for Different Pitch Types ---")
    pitch_types = ["BAT", "BWL", "BAL", "SPIN"]
    
    for pitch_type in pitch_types:
        print(f"\nPredicting for {pitch_type} pitch...")
        prediction = make_prediction(token, teams[0]['id'], teams[1]['id'], venues[0]['id'], pitch_type)
        
        if prediction:
            print(f"Prediction successful for {pitch_type} pitch!")
            # Print some details about the prediction
            for pred_type, players in prediction.get('predictions', {}).items():
                captain = next((p for p in players if p.get('is_captain')), None)
                vice_captain = next((p for p in players if p.get('is_vice_captain')), None)
                
                print(f"  {pred_type} strategy:")
                if captain:
                    print(f"    Captain: {captain['player_name']} ({captain['role']})")
                if vice_captain:
                    print(f"    Vice-Captain: {vice_captain['player_name']} ({vice_captain['role']})")
                print(f"    Total players: {len(players)}")

# Test scraper functionality
def test_scraper_functionality(token):
    """
    Test all scraper-related functionality in sequence.
    """
    print("\n===== TESTING CRICINFO SCRAPER FUNCTIONALITY =====\n")
    
    # Test player scraper - MS Dhoni
    player_data = test_scrape_player(token, player_id="253802")
    
    # Test match scraper - An IPL final
    match_data = test_scrape_match(token, match_id="1370168")
    
    # Test season scraper - IPL 2023
    season_data = test_scrape_season(token, year=2023)
    
    # Test player stats update
    stats_update = test_update_player_stats(token)
    
    # Test enhanced player stats
    enhanced_stats = test_enhance_player_stats(token)
    
    # Print summary
    print("\n===== SCRAPER TEST SUMMARY =====\n")
    print(f"Player scraper test: {'Success' if player_data else 'Failed'}")
    print(f"Match scraper test: {'Success' if match_data else 'Failed'}")
    print(f"Season scraper test: {'Success' if season_data else 'Failed'}")
    print(f"Player stats update test: {'Success' if stats_update else 'Failed'}")
    print(f"Enhanced player stats test: {'Success' if enhanced_stats else 'Failed'}")

# Main function to test the API
def main():
    # Try to login first - if fails, register a new user
    login_response = login_user()
    
    if not login_response:
        print("Login failed. Trying to register...")
        register_response = register_user()
        
        if not register_response:
            print("Registration failed. Exiting.")
            return
            
        # Try login again after registration
        login_response = login_user()
    
    # Extract token from login response
    token = login_response.get('access')
    if not token:
        print("Failed to get access token. Exiting.")
        return
    
    # Get teams
    teams = get_teams(token)
    if not teams or len(teams) < 2:
        print("Failed to get teams or not enough teams. Exiting.")
        return
    
    # Get venues
    venues = get_venues(token)
    if not venues or len(venues) < 1:
        print("Failed to get venues. Exiting.")
        return
    
    # Make a prediction
    team1_id = teams[0]['id']
    team2_id = teams[1]['id']
    venue_id = venues[0]['id']
    pitch_type = "BAL"  # Balanced pitch
    
    prediction = make_prediction(token, team1_id, team2_id, venue_id, pitch_type)
    
    if prediction:
        print("Prediction successful!")
        print("Predictions available for:", prediction.get('predictions', {}).keys())
    else:
        print("Prediction failed.")
    
    # Test predictions with scraped data
    test_with_scraped_data(token)
      # Test scraper functionality
    test_scraper_functionality(token)
    
    # Test player enhanced stats API if players are available
    if teams and teams[0]['players']:
        player_id = teams[0]['players'][0]['id']
        test_player_enhanced_stats(token, player_id)

if __name__ == "__main__":
    main()
