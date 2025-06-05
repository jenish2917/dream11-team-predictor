#!/usr/bin/env python3
"""
Test script to verify that the prediction logic is using actual CSV data
"""
import os
import sys
import django
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dream11_backend.settings')
django.setup()

from predictor.logic.prediction import Dream11TeamPredictor

def test_csv_data_loading():
    """Test if CSV data is being loaded correctly"""
    print("=" * 60)
    print("TESTING CSV DATA LOADING")
    print("=" * 60)
    
    # Initialize predictor with explicit data folder path
    data_folder = Path(__file__).parent.parent / 'data' / 'IPL-DATASET'
    print(f"Data folder path: {data_folder}")
    print(f"Data folder exists: {data_folder.exists()}")
    
    if not data_folder.exists():
        print("ERROR: Data folder not found!")
        return False
    
    # List files in data folder
    print("\nFiles in data folder:")
    for file in data_folder.glob("*.csv"):
        print(f"  - {file.name}")
    
    # Initialize predictor
    try:
        predictor = Dream11TeamPredictor(str(data_folder))
        print(f"\n✅ Predictor initialized successfully")
        
        # Check if teams were loaded
        teams = predictor.get_all_teams()
        print(f"✅ Found {len(teams)} teams: {teams}")
          # Check if any team has players
        total_players = 0
        for team in teams:
            players = predictor.get_team_players(team)
            total_players += len(players)
            print(f"  - {team}: {len(players)} players")
            
            # Show first few players for sample team
            if len(players) > 0 and team == teams[0]:
                print(f"    Sample players from {team}:")
                for i, player in enumerate(players[:3]):
                    print(f"      {i+1}. {player['name']} ({player['role']}, ₹{player['price']:.1f}cr)")
        
        print(f"\n✅ Total players loaded: {total_players}")
        
        # Test batting stats
        if hasattr(predictor, 'batting_stats') and predictor.batting_stats:
            print(f"✅ Batting stats loaded for {len(predictor.batting_stats)} players")
            # Show sample batting stats
            sample_players = list(predictor.batting_stats.keys())[:3]
            for player in sample_players:
                stats = predictor.batting_stats[player]
                print(f"  - {player}: {stats['runs']} runs in {stats['matches']} matches")
        else:
            print("❌ No batting stats loaded")
        
        # Test bowling stats
        if hasattr(predictor, 'bowling_stats') and predictor.bowling_stats:
            print(f"✅ Bowling stats loaded for {len(predictor.bowling_stats)} players")
            # Show sample bowling stats
            sample_players = list(predictor.bowling_stats.keys())[:3]
            for player in sample_players:
                stats = predictor.bowling_stats[player]
                print(f"  - {player}: {stats['wickets']} wickets in {stats['matches']} matches")
        else:
            print("❌ No bowling stats loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing predictor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_prediction():
    """Test actual prediction with real data"""
    print("\n" + "=" * 60)
    print("TESTING PREDICTION FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Initialize predictor
        data_folder = Path(__file__).parent.parent / 'data' / 'IPL-DATASET'
        predictor = Dream11TeamPredictor(str(data_folder))
        
        # Get available teams
        teams = predictor.get_all_teams()
        if len(teams) < 2:
            print("❌ Need at least 2 teams for prediction")
            return False
        
        # Test prediction with first two teams
        team1, team2 = teams[0], teams[1]
        print(f"Testing prediction for: {team1} vs {team2}")
        
        # Make prediction
        result = predictor.predict_team(team1, team2, budget=100)
        
        print(f"\n✅ Prediction successful!")
        print(f"Selected team size: {len(result['team'])}")
        print(f"Total score: {result['score']:.1f}")
        print(f"Budget used: {result['budget_used']:.1f} cr")
        print(f"Budget remaining: {result['budget_remaining']:.1f} cr")
        print(f"Team composition: {result['roles']}")
        print(f"Team distribution: {result['team_distribution']}")
        
        print(f"\nSelected players:")
        for i, player in enumerate(result['team'], 1):
            print(f"  {i:2d}. {player['name']} ({player['role']}, {player['team']}, ₹{player['price']:.1f}cr)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Dream11 Team Predictor - CSV Data Test")
    print("Testing if the prediction system is using real CSV data...")
    
    # Test 1: Data loading
    data_loaded = test_csv_data_loading()
    
    # Test 2: Prediction functionality
    if data_loaded:
        prediction_success = test_prediction()
        
        if prediction_success:
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED! The prediction system is using real CSV data.")
            print("=" * 60)
        else:
            print("\n❌ Prediction test failed!")
    else:
        print("\n❌ Data loading test failed!")
