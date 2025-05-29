"""
Test script for Player Performance Prediction with Machine Learning.
This script demonstrates how to train and use ML models for cricket player performance prediction.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set up local environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dream11_backend.settings')

def test_player_performance_predictor():
    """Test the player performance prediction functionality."""
    print("=" * 80)
    print("TESTING PLAYER PERFORMANCE PREDICTION")
    print("=" * 80)
    
    # Import the processor
    try:
        from predictor.player_performance_predictor import PlayerPerformancePredictor
        print("✅ Successfully imported PlayerPerformancePredictor")
    except ImportError as e:
        print(f"❌ Failed to import PlayerPerformancePredictor: {str(e)}")
        return False
    
    # Create sample data for testing
    data_dir = create_sample_data_for_ml()
    if not data_dir:
        print("❌ Failed to create sample data")
        return False
    
    print(f"✅ Created sample data in {data_dir}")
    
    # Initialize predictor
    predictor = PlayerPerformancePredictor(data_dir)
    
    # Test data loading
    print("\nLoading data...")
    success = predictor.load_data(
        batting_file=os.path.join(data_dir, 'batting_data_ml.csv'),
        bowling_file=os.path.join(data_dir, 'bowling_data_ml.csv')
    )
    
    if not success:
        print("❌ Failed to load data")
        return False
    
    print(f"✅ Loaded data: {len(predictor.batting_df)} batting records, {len(predictor.bowling_df)} bowling records")
    
    # Train models
    print("\nTraining machine learning models...")
    success = predictor.train_models()
    
    if not success:
        print("❌ Failed to train models")
        return False
    
    print("✅ Successfully trained models")
    
    # Test predictions for sample players
    print("\nGenerating predictions for sample players:")
    
    # Define match details
    match_details = {
        'venue': 'Wankhede Stadium',
        'opposing_team': 'Mumbai Indians'
    }
    
    # Test batting prediction
    batsman = "Virat Kohli"
    print(f"\nPredicting performance for {batsman}:")
    batting_prediction = predictor.predict_next_match_performance(batsman, match_details)
    
    if batting_prediction:
        print("✅ Generated prediction")
        if 'batting' in batting_prediction:
            bat_pred = batting_prediction['batting']
            print(f"  Predicted runs: {bat_pred.get('predicted_runs', 'N/A')}")
            print(f"  Performance class: {bat_pred.get('performance_class', 'N/A')}")
            if 'class_probabilities' in bat_pred:
                print("  Class probabilities:")
                for cls, prob in bat_pred['class_probabilities'].items():
                    print(f"    {cls}: {prob:.3f}")
    else:
        print("❌ Failed to generate batting prediction")
    
    # Test bowling prediction
    bowler = "Jasprit Bumrah"
    print(f"\nPredicting performance for {bowler}:")
    bowling_prediction = predictor.predict_next_match_performance(bowler, match_details)
    
    if bowling_prediction:
        print("✅ Generated prediction")
        if 'bowling' in bowling_prediction:
            bowl_pred = bowling_prediction['bowling']
            print(f"  Predicted wickets: {bowl_pred.get('predicted_wickets', 'N/A')}")
            print(f"  Performance class: {bowl_pred.get('performance_class', 'N/A')}")
            if 'class_probabilities' in bowl_pred:
                print("  Class probabilities:")
                for cls, prob in bowl_pred['class_probabilities'].items():
                    print(f"    {cls}: {prob:.3f}")
    else:
        print("❌ Failed to generate bowling prediction")
    
    # Test full match prediction
    print("\nGenerating full match predictions:")
    team1 = "Royal Challengers Bangalore"
    team2 = "Mumbai Indians"
    venue = "Wankhede Stadium"
    
    match_predictions = predictor.generate_match_predictions(team1, team2, venue)
    
    if match_predictions:
        print(f"✅ Generated predictions for {team1} vs {team2} at {venue}")
        
        # Export predictions
        json_path = predictor.export_predictions(match_predictions, 'json')
        if json_path:
            print(f"✅ Exported predictions to JSON: {json_path}")
        
        csv_path = predictor.export_predictions(match_predictions, 'csv')
        if csv_path:
            print(f"✅ Exported predictions to CSV: {csv_path}")
        
        # Print summary
        print("\nPrediction Summary:")
        
        # Team 1 players
        print(f"\n{team1} Players:")
        team1_players = match_predictions['team1']['players']
        for player, pred in team1_players.items():
            output = f"- {player}: "
            if 'batting' in pred:
                output += f"Runs {pred['batting'].get('predicted_runs', 'N/A')} ({pred['batting'].get('performance_class', 'N/A')}) "
            if 'bowling' in pred:
                output += f"Wickets {pred['bowling'].get('predicted_wickets', 'N/A')} ({pred['bowling'].get('performance_class', 'N/A')})"
            print(output)
        
        # Team 2 players
        print(f"\n{team2} Players:")
        team2_players = match_predictions['team2']['players']
        for player, pred in team2_players.items():
            output = f"- {player}: "
            if 'batting' in pred:
                output += f"Runs {pred['batting'].get('predicted_runs', 'N/A')} ({pred['batting'].get('performance_class', 'N/A')}) "
            if 'bowling' in pred:
                output += f"Wickets {pred['bowling'].get('predicted_wickets', 'N/A')} ({pred['bowling'].get('performance_class', 'N/A')})"
            print(output)
    else:
        print("❌ Failed to generate match predictions")
    
    print("\n" + "=" * 80)
    print("PLAYER PERFORMANCE PREDICTION TEST COMPLETE")
    print("=" * 80)
    
    return True

def create_sample_data_for_ml():
    """Create sample cricket data for ML testing."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_cricket_data')
    
    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Create more comprehensive data for ML testing
    # Generate 100 matches worth of data for 20 players
    import random
    from datetime import datetime, timedelta
    
    # Define teams and venues
    teams = ["Royal Challengers Bangalore", "Mumbai Indians", "Chennai Super Kings", "Delhi Capitals", 
             "Kolkata Knight Riders", "Punjab Kings", "Rajasthan Royals", "Sunrisers Hyderabad"]
    
    venues = ["Wankhede Stadium", "M. Chinnaswamy Stadium", "MA Chidambaram Stadium", 
              "Eden Gardens", "Arun Jaitley Stadium", "Punjab Cricket Association Stadium"]
    
    # Define players with roles
    players = {
        "Virat Kohli": {"team": "Royal Challengers Bangalore", "role": "BAT"},
        "Rohit Sharma": {"team": "Mumbai Indians", "role": "BAT"},
        "MS Dhoni": {"team": "Chennai Super Kings", "role": "WK"},
        "KL Rahul": {"team": "Punjab Kings", "role": "BAT"},
        "Jasprit Bumrah": {"team": "Mumbai Indians", "role": "BWL"},
        "Yuzvendra Chahal": {"team": "Royal Challengers Bangalore", "role": "BWL"},
        "Ravindra Jadeja": {"team": "Chennai Super Kings", "role": "AR"},
        "Hardik Pandya": {"team": "Mumbai Indians", "role": "AR"},
        "Rishabh Pant": {"team": "Delhi Capitals", "role": "WK"},
        "Shreyas Iyer": {"team": "Kolkata Knight Riders", "role": "BAT"},
        "Pat Cummins": {"team": "Kolkata Knight Riders", "role": "BWL"},
        "Jos Buttler": {"team": "Rajasthan Royals", "role": "WK"},
        "David Warner": {"team": "Delhi Capitals", "role": "BAT"},
        "Glenn Maxwell": {"team": "Royal Challengers Bangalore", "role": "AR"},
        "Rashid Khan": {"team": "Sunrisers Hyderabad", "role": "BWL"},
        "Kane Williamson": {"team": "Sunrisers Hyderabad", "role": "BAT"},
        "Kagiso Rabada": {"team": "Punjab Kings", "role": "BWL"},
        "Andre Russell": {"team": "Kolkata Knight Riders", "role": "AR"},
        "Faf du Plessis": {"team": "Royal Challengers Bangalore", "role": "BAT"},
        "Bhuvneshwar Kumar": {"team": "Sunrisers Hyderabad", "role": "BWL"}
    }
    
    # Generate match data
    matches = []
    start_date = datetime(2023, 1, 1)
    
    for i in range(100):
        # Select two random teams for a match
        match_teams = random.sample(teams, 2)
        team1 = match_teams[0]
        team2 = match_teams[1]
        
        # Select a random venue
        venue = random.choice(venues)
        
        # Set match date
        match_date = start_date + timedelta(days=i)
        date_str = match_date.strftime("%Y-%m-%d")
        
        # Generate unique match ID
        match_id = f"m{i+1000}"
        
        matches.append({
            "match_id": match_id,
            "team1": team1,
            "team2": team2,
            "venue": venue,
            "date": date_str
        })
    
    # Generate batting and bowling data
    batting_data = []
    bowling_data = []
    
    # Helper function to get players of a team
    def get_team_players(team_name):
        return [name for name, details in players.items() if details["team"] == team_name]
    
    # Generate match statistics
    for match in matches:
        team1_players = get_team_players(match["team1"])
        team2_players = get_team_players(match["team2"])
        
        # Generate batting data for Team 1 vs Team 2
        for player in team1_players:
            if players[player]["role"] in ["BAT", "WK", "AR"]:
                # Base runs depending on player role
                base_runs = 30 if players[player]["role"] == "BAT" else 20
                
                # Add randomness and venue factor
                venue_factor = 1.2 if match["venue"] == "Wankhede Stadium" else 0.9
                opposition_factor = 1.1 if match["team2"] == "Sunrisers Hyderabad" else 0.95
                
                runs = max(0, int(base_runs + random.normalvariate(10, 15) * venue_factor * opposition_factor))
                balls = max(1, int(runs * (1 + random.normalvariate(0, 0.3))))
                fours = int(runs / 10)
                sixes = int(runs / 20)
                
                sr = (runs / balls) * 100 if balls > 0 else 0
                
                batting_data.append({
                    "match_id": match["match_id"],
                    "player_name": player,
                    "player_id": hash(player) % 1000,
                    "team": match["team1"],
                    "opposing_team": match["team2"],
                    "runs": runs,
                    "balls": balls,
                    "fours": fours,
                    "sixes": sixes,
                    "strike_rate": sr,
                    "role": players[player]["role"],
                    "match_date": match["date"],
                    "venue": match["venue"]
                })
        
        # Generate batting data for Team 2 vs Team 1
        for player in team2_players:
            if players[player]["role"] in ["BAT", "WK", "AR"]:
                # Base runs depending on player role
                base_runs = 30 if players[player]["role"] == "BAT" else 20
                
                # Add randomness and venue factor
                venue_factor = 1.2 if match["venue"] == "Wankhede Stadium" else 0.9
                opposition_factor = 1.1 if match["team1"] == "Sunrisers Hyderabad" else 0.95
                
                runs = max(0, int(base_runs + random.normalvariate(10, 15) * venue_factor * opposition_factor))
                balls = max(1, int(runs * (1 + random.normalvariate(0, 0.3))))
                fours = int(runs / 10)
                sixes = int(runs / 20)
                
                sr = (runs / balls) * 100 if balls > 0 else 0
                
                batting_data.append({
                    "match_id": match["match_id"],
                    "player_name": player,
                    "player_id": hash(player) % 1000,
                    "team": match["team2"],
                    "opposing_team": match["team1"],
                    "runs": runs,
                    "balls": balls,
                    "fours": fours,
                    "sixes": sixes,
                    "strike_rate": sr,
                    "role": players[player]["role"],
                    "match_date": match["date"],
                    "venue": match["venue"]
                })
        
        # Generate bowling data for Team 1 vs Team 2
        for player in team1_players:
            if players[player]["role"] in ["BWL", "AR"]:
                # Base wickets depending on player role
                base_wickets = 2 if players[player]["role"] == "BWL" else 1
                
                # Add randomness and venue factor
                venue_factor = 1.1 if match["venue"] == "MA Chidambaram Stadium" else 0.95
                opposition_factor = 1.2 if match["team2"] == "Royal Challengers Bangalore" else 0.9
                
                wickets = max(0, int(base_wickets + random.normalvariate(0, 1) * venue_factor * opposition_factor))
                overs = 4 if wickets <= 4 else 3.2  # Can't take more than 4 wickets in 4 overs typically
                runs_conceded = int(20 + random.normalvariate(0, 5) * (4 / overs if overs > 0 else 1))
                economy = runs_conceded / overs if overs > 0 else 0
                
                bowling_data.append({
                    "match_id": match["match_id"],
                    "player_name": player,
                    "player_id": hash(player) % 1000,
                    "team": match["team1"],
                    "opposing_team": match["team2"],
                    "overs": overs,
                    "maidens": int(random.random() > 0.8),
                    "runs": runs_conceded,
                    "wickets": wickets,
                    "economy": economy,
                    "role": players[player]["role"],
                    "match_date": match["date"],
                    "venue": match["venue"]
                })
        
        # Generate bowling data for Team 2 vs Team 1
        for player in team2_players:
            if players[player]["role"] in ["BWL", "AR"]:
                # Base wickets depending on player role
                base_wickets = 2 if players[player]["role"] == "BWL" else 1
                
                # Add randomness and venue factor
                venue_factor = 1.1 if match["venue"] == "MA Chidambaram Stadium" else 0.95
                opposition_factor = 1.2 if match["team1"] == "Royal Challengers Bangalore" else 0.9
                
                wickets = max(0, int(base_wickets + random.normalvariate(0, 1) * venue_factor * opposition_factor))
                overs = 4 if wickets <= 4 else 3.2  # Can't take more than 4 wickets in 4 overs typically
                runs_conceded = int(20 + random.normalvariate(0, 5) * (4 / overs if overs > 0 else 1))
                economy = runs_conceded / overs if overs > 0 else 0
                
                bowling_data.append({
                    "match_id": match["match_id"],
                    "player_name": player,
                    "player_id": hash(player) % 1000,
                    "team": match["team2"],
                    "opposing_team": match["team1"],
                    "overs": overs,
                    "maidens": int(random.random() > 0.8),
                    "runs": runs_conceded,
                    "wickets": wickets,
                    "economy": economy,
                    "role": players[player]["role"],
                    "match_date": match["date"],
                    "venue": match["venue"]
                })
    
    # Convert to DataFrames
    batting_df = pd.DataFrame(batting_data)
    bowling_df = pd.DataFrame(bowling_data)
    
    # Save to CSV
    try:
        batting_df.to_csv(os.path.join(data_dir, 'batting_data_ml.csv'), index=False)
        bowling_df.to_csv(os.path.join(data_dir, 'bowling_data_ml.csv'), index=False)
        return data_dir
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")
        return None

if __name__ == "__main__":
    test_player_performance_predictor()
