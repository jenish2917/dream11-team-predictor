import requests
import argparse

def test_api_endpoints(test_type="all"):
    BASE_URL = "http://127.0.0.1:8000/api"
    
    print("Testing API Endpoints for Dream11 Team Predictor")
    print("=" * 50)
    
    access_token = None
    
    # Test register endpoint
    print("\nTesting Register Endpoint:")
    register_data = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "password": "testpassword123",
        "password2": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register/", json=register_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code < 400 else response.text}")
        
        if response.status_code < 400:
            print("Registration successful!")
            user_data = response.json()
        else:
            print("Registration failed.")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test login endpoint
    print("\nTesting Login Endpoint:")
    login_data = {
        "username": "testuser123",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login/", json=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code < 400 else response.text}")
        
        if response.status_code < 400:
            print("Login successful!")
            token = response.json().get("access", "")
            print(f"Access Token: {token[:20]}...")
        else:
            # Try with admin credentials
            print("Login failed. Trying with admin credentials...")
            admin_login_data = {
                "username": "admin",
                "password": "admin"
            }
            response = requests.post(f"{BASE_URL}/login/", json=admin_login_data)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json() if response.status_code < 400 else response.text}")
            
            if response.status_code < 400:
                print("Admin login successful!")
                token = response.json().get("access", "")
                print(f"Access Token: {token[:20]}...")
            else:
                print("Admin login failed.")
                token = ""
    except Exception as e:
        print(f"Error: {str(e)}")
        token = ""
    
    if not token:
        print("\nCan't proceed with testing other endpoints without authentication token.")
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Test teams endpoint
    print("\nTesting Teams Endpoint:")
    try:
        response = requests.get(f"{BASE_URL}/teams/", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code < 400 else response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test venues endpoint
    print("\nTesting Venues Endpoint:")
    try:
        response = requests.get(f"{BASE_URL}/venues/", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code < 400 else response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
      # Test players endpoint
    print("\nTesting Players Endpoint:")
    try:
        response = requests.get(f"{BASE_URL}/players/", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()[:3] if response.status_code < 400 else response.text}")
        print("... (truncated for readability)")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test prediction endpoint
    print("\nTesting Team Prediction Endpoint:")
    try:
        # Get teams and venues for prediction
        teams_response = requests.get(f"{BASE_URL}/teams/", headers=headers)
        venues_response = requests.get(f"{BASE_URL}/venues/", headers=headers)
        
        if teams_response.status_code == 200 and venues_response.status_code == 200:
            teams = teams_response.json()
            venues = venues_response.json()
            
            if len(teams) >= 2 and len(venues) >= 1:
                # Make a prediction with the first two teams and first venue
                prediction_data = {
                    "team1": teams[0]["id"],
                    "team2": teams[1]["id"],
                    "venue": venues[0]["id"],
                    "pitch_type": "BAL"  # Balanced pitch
                }
                
                print(f"Sending prediction request with: {prediction_data}")
                response = requests.post(f"{BASE_URL}/predict-team/", json=prediction_data, headers=headers)
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("Prediction successful!")
                    print(f"Available prediction types: {list(result.get('predictions', {}).keys())}")
                    
                    # Print the first player from each prediction type
                    for pred_type, pred_data in result.get('predictions', {}).items():
                        if 'players' in pred_data and pred_data['players']:
                            player = pred_data['players'][0]
                            print(f"\n{pred_type} prediction example player: {player['player']['name']} (Captain: {player['is_captain']})")
                else:
                    print(f"Prediction failed: {response.text}")
            else:
                print("Not enough teams or venues to test prediction")
        else:
            print("Could not fetch teams or venues for prediction test")
    except Exception as e:
        print(f"Error in prediction test: {str(e)}")
      # Test scraper-related endpoints if requested
    if test_type in ["all", "scraper"]:
        print("\nTesting ESPNCricinfo Scraper Endpoints:")
        print("-" * 40)
        
        # Test match scraper
        print("\nTesting Match Scraper Endpoint:")
        try:
            match_id = "1370168"  # IPL 2023 final
            scraper_data = {"update_stats": False}
            
            print(f"Scraping match with ID: {match_id}")
            response = requests.post(f"{BASE_URL}/scrape/match/{match_id}/", 
                                    json=scraper_data, 
                                    headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code < 400:
                result = response.json()
                print("Match scraping successful!")
                print(f"Teams: {result.get('teams', [])}")
                print(f"Top scorer: {result.get('top_scorer', 'N/A')}")
                print(f"Top wicket taker: {result.get('top_wicket_taker', 'N/A')}")
            else:
                print(f"Match scraping failed: {response.text}")
        except Exception as e:
            print(f"Error in match scraper test: {str(e)}")
        
        # Test player scraper
        print("\nTesting Player Scraper Endpoint:")
        try:
            player_id = "253802"  # MS Dhoni
            scraper_data = {"update_stats": False}
            
            print(f"Scraping player with ID: {player_id}")
            response = requests.post(f"{BASE_URL}/scrape/player/{player_id}/", 
                                    json=scraper_data, 
                                    headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code < 400:
                result = response.json()
                print("Player scraping successful!")
                print(f"Name: {result.get('name', 'N/A')}")
                print(f"Teams: {', '.join(result.get('teams', []))}")
                print(f"Batting Style: {result.get('batting_style', 'N/A')}")
            else:
                print(f"Player scraping failed: {response.text}")
        except Exception as e:
            print(f"Error in player scraper test: {str(e)}")
        
        # Test season scraper
        print("\nTesting Season Scraper Endpoint:")
        try:
            year = 2023
            scraper_data = {
                "scrape_matches": False,
                "update_stats": False
            }
            
            print(f"Scraping IPL season: {year}")
            response = requests.post(f"{BASE_URL}/scrape/season/{year}/", 
                                    json=scraper_data, 
                                    headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code < 400:
                result = response.json()
                print("Season scraping successful!")
                print(f"Matches found: {result.get('matches_found', 0)}")
                print(f"Teams: {result.get('teams', [])}")
                print(f"Venues: {result.get('venues', [])}")
            else:
                print(f"Season scraping failed: {response.text}")
        except Exception as e:
            print(f"Error in season scraper test: {str(e)}")
        
        # Test player stats update
        print("\nTesting Player Stats Update Endpoint:")
        try:
            update_data = {
                "dry_run": True,
                "days": 90
            }
            
            print("Running player stats update (dry run)")
            response = requests.post(f"{BASE_URL}/update-stats/", 
                                   json=update_data, 
                                   headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code < 400:
                result = response.json()
                print("Stats update check successful!")
                print(f"Players that would be updated: {result.get('players_updated', 0)}")
                
                # Print sample of player updates if available
                updated_players = result.get('updated_players', [])
                if updated_players:
                    print("\nSample player updates:")
                    for player in updated_players[:2]:  # Show only first 2
                        print(f"- {player.get('player_name', 'Unknown')}")
                        if 'old_batting_average' in player:
                            print(f"  Batting avg: {player.get('old_batting_average')} → {player.get('new_batting_average')}")
                        if 'old_bowling_average' in player:
                            print(f"  Bowling avg: {player.get('old_bowling_average')} → {player.get('new_bowling_average')}")
                        if 'old_recent_form' in player:
                            print(f"  Recent form: {player.get('old_recent_form')} → {player.get('new_recent_form')}")
            else:
                print(f"Stats update check failed: {response.text}")
        except Exception as e:
            print(f"Error in stats update test: {str(e)}")
    
    print("\nAPI Testing Complete!")
    
    if test_type in ["all", "scraper"]:
        print("\n" + "=" * 40)
        print("NOTE: If you see 'ESPNCricinfoScraper is not defined' or 'UpdateStatsCommand is not defined' errors:")
        print("1. Ensure the Django server is running with correct imports")
        print("2. Check that your management commands are properly installed")
        print("3. Try restarting the Django server with the command:")
        print("   python manage.py runserver")
        print("=" * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Dream11 Team Predictor API')
    parser.add_argument('--type', choices=['all', 'core', 'scraper'], default='all', 
                        help='Type of tests to run (all, core, or scraper)')
    args = parser.parse_args()
    test_api_endpoints(args.type)
