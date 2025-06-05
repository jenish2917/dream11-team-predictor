#!/usr/bin/env python3
"""
Test script for Dream11 Team Predictor functionality
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dream11_backend.settings')

import django
django.setup()

from predictor.logic.prediction import Dream11TeamPredictor

def test_predictor():
    """Test the Dream11TeamPredictor functionality"""
    print("Testing Dream11 Team Predictor...")
    
    # Initialize predictor
    data_folder = os.path.join(os.path.dirname(backend_dir), 'data', 'IPL-DATASET')
    print(f"Data folder: {data_folder}")
    
    if not os.path.exists(data_folder):
        print(f"Error: Data folder not found at {data_folder}")
        return False
    
    try:
        predictor = Dream11TeamPredictor(data_folder)
        
        # Test team loading
        teams = predictor.get_all_teams()
        print(f"Loaded {len(teams)} teams: {teams}")
        
        if len(teams) < 2:
            print("Error: Need at least 2 teams for prediction")
            return False
        
        # Test prediction with first two teams
        team1, team2 = teams[0], teams[1]
        print(f"\nTesting prediction for {team1} vs {team2}")
        
        # Test player scores calculation
        player_scores = predictor.calculate_player_scores(team1, team2)
        print(f"Calculated scores for {len(player_scores)} players")
        
        # Test team prediction
        prediction = predictor.predict_team(team1, team2, budget=100)
        print(f"\nPrediction result:")
        print(f"Selected team has {len(prediction['team'])} players")
        print(f"Total score: {prediction['score']}")
        print(f"Budget used: {prediction['budget_used']} crores")
        print(f"Budget remaining: {prediction['budget_remaining']} crores")
        
        # Display selected players
        print("\nSelected players:")
        for i, player in enumerate(prediction['team']):
            print(f"{i+1}. {player['name']} ({player['role']}) - {player['team']} - {player.get('fantasy_points', 0)} pts")
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_predictor()
    sys.exit(0 if success else 1)
