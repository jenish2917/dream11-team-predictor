"""
Test script for validating ML prediction integration with Dream11 Team Predictor.

This script tests:
1. ML prediction functionality using the fixed predictor
2. Integration with the team prediction algorithm
"""

import os
import sys
import django
import json
import pandas as pd
import numpy as np

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dream11_backend.settings')
django.setup()

# Import necessary modules
from predictor.player_performance_predictor_fixed import PlayerPerformancePredictor
from predictor.prediction_algorithm_enhanced import TeamPredictor
from predictor.models import Player, Team, Venue
from predictor.ml_prediction_helpers import prepare_player_input_features

def test_ml_prediction():
    """Test the ML prediction functionality with sample data."""
    print("\n--- Testing ML Prediction Functionality ---")
    
    # Setup test data directory
    test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_cricket_data')
    
    # Initialize predictor
    predictor = PlayerPerformancePredictor(test_data_dir)
    
    # Create and train models if needed
    if not predictor.load_models():
        print("No pre-trained models found. Training new models...")
        
        # Load sample data
        predictor.load_data(
            batting_file=os.path.join(test_data_dir, 'batting_data_ml.csv'),
            bowling_file=os.path.join(test_data_dir, 'bowling_data_ml.csv')
        )
        
        # Train models
        predictor.train_models()
        
        # Save models
        predictor.save_models()
        print("Models trained and saved successfully.")
      # Test prediction for a sample player
    sample_player = {
        'player_name': 'Virat Kohli',
        'role': 'BAT',
        'team': 'India',
        'opposing_team': 'Australia',
        'venue': 'Melbourne Cricket Ground'
    }
      # Prepare input features for prediction
    batting_input = prepare_player_input_features(sample_player, 'batting')
    bowling_input = prepare_player_input_features(sample_player, 'bowling')
    
    # Get predictions for both batting and bowling
    batting_prediction = predictor.predict_performance(batting_input, prediction_type='batting')
    bowling_prediction = predictor.predict_performance(bowling_input, prediction_type='bowling')
    
    # Combine predictions
    prediction = {
        'player_name': sample_player['player_name'],
        'batting_prediction': batting_prediction,
        'bowling_prediction': bowling_prediction
    }
    
    print(f"ML Prediction for {sample_player['player_name']}:")
    print(json.dumps(prediction, indent=2))
    
    return predictor

def test_team_predictor_with_ml():
    """Test the integration of ML predictions with team prediction."""
    print("\n--- Testing Team Predictor with ML Integration ---")
    
    # Get some teams from the database
    teams = Team.objects.all()[:2]
    if len(teams) < 2:
        print("Not enough teams in the database to test team prediction.")
        return False
    
    team1, team2 = teams[0], teams[1]
    
    # Get a venue
    venue = Venue.objects.first()
    if not venue:
        print("No venues in the database to test team prediction.")
        return False
    
    print(f"Test match: {team1.name} vs {team2.name} at {venue.name}")
    
    # Initialize ML predictor
    test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_cricket_data')
    ml_predictor = PlayerPerformancePredictor(test_data_dir)
    
    # Load models
    if not ml_predictor.load_models():
        print("No ML models available. Running without ML integration...")
        predictor = TeamPredictor(team1.id, team2.id, venue.id, 'BAT')
    else:
        # Generate ML predictions for all players
        ml_predictions = {}
        all_players = list(Player.objects.filter(team__in=[team1, team2]))
        for player in all_players:
            player_data = {
                'player_name': player.name,
                'role': player.role,
                'team': player.team.name,
                'opposing_team': team2.name if player.team == team1 else team1.name,
                'venue': venue.name
            }            # Prepare input features for prediction
            batting_input = prepare_player_input_features(player_data, 'batting')
            bowling_input = prepare_player_input_features(player_data, 'bowling')
            
            # Get both batting and bowling predictions
            batting_prediction = ml_predictor.predict_performance(batting_input, prediction_type='batting')
            bowling_prediction = ml_predictor.predict_performance(bowling_input, prediction_type='bowling')
            
            # Combine predictions
            player_prediction = {
                'player_name': player.name,
                'batting_prediction': batting_prediction,
                'bowling_prediction': bowling_prediction
            }
            ml_predictions[player.id] = player_prediction
        
        # Initialize team predictor with ML predictions
        predictor = TeamPredictor(team1.id, team2.id, venue.id, 'BAT', ml_predictions=ml_predictions)
        print(f"Added ML predictions for {len(ml_predictions)} players")
    
    # Generate team predictions
    predictions = predictor.predict_teams()
    
    print("\nTeam Predictions:")
    for pred_type, players in predictions.items():
        print(f"\n{pred_type} strategy team:")
        for player_data in players:
            player = player_data['player']
            points = player_data['expected_points']
            role = "Captain" if player_data['is_captain'] else ("Vice Captain" if player_data['is_vice_captain'] else "")
            print(f"  - {player.name} ({player.role}): {points:.1f} points {role}")
    
    return True

if __name__ == "__main__":
    # Test ML prediction
    predictor = test_ml_prediction()
    
    # Test team prediction with ML integration
    test_team_predictor_with_ml()
    
    print("\nTests completed.")
