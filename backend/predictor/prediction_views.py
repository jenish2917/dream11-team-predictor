"""
API view for player performance prediction using machine learning.
"""

import os
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.management import call_command

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_player_performance(request):
    """
    Predict player performance for an upcoming match using machine learning models.
    
    Args:
        request: Contains match details (team1, team2, venue)
    
    Returns:
        Response with predictions or error
    """
    try:
        # Get parameters
        team1 = request.data.get('team1')
        team2 = request.data.get('team2')
        venue = request.data.get('venue')
        export_format = request.data.get('export_format', 'json')
        update_db = request.data.get('update_db', False)
        
        # Validate required parameters
        if not all([team1, team2, venue]):
            return Response(
                {"error": "team1, team2, and venue parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
          # Import fixed player performance predictor
        from .player_performance_predictor_fixed import PlayerPerformancePredictor
        
        # Initialize predictor
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'management', 'commands', 'cricket_data')
        predictor = PlayerPerformancePredictor(data_dir)
        
        # Try to load existing models
        success = predictor.load_models()
        if not success:
            # If no models found, try to train new ones
            # First load the data
            load_success = predictor.load_data()
            if not load_success:
                return Response(
                    {"error": "Failed to load player data. Please ensure data is available."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Train models
            train_success = predictor.train_models()
            if not train_success:
                return Response(
                    {"error": "Failed to train prediction models."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Generate predictions
        predictions = predictor.generate_match_predictions(team1, team2, venue)
        if not predictions:
            return Response(
                {"error": "Failed to generate predictions for the match."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Export predictions to files
        exported_files = []
        if export_format in ['json', 'both']:
            json_path = predictor.export_predictions(predictions, 'json')
            if json_path:
                exported_files.append({"format": "json", "path": json_path})
        
        if export_format in ['csv', 'both']:
            csv_path = predictor.export_predictions(predictions, 'csv')
            if csv_path:
                exported_files.append({"format": "csv", "path": csv_path})
        
        # Update database if requested
        if update_db:
            # Use the management command to update the database
            call_command('predict_player_performance',
                         team1=team1,
                         team2=team2,
                         venue=venue,
                         update_db=True,
                         verbosity=0)
        
        # Prepare response
        result = {
            "match": f"{team1} vs {team2} at {venue}",
            "predictions": {
                "team1": {
                    "name": team1,
                    "players": {
                        player: {
                            "batting": pred.get("batting", {}),
                            "bowling": pred.get("bowling", {})
                        }
                        for player, pred in predictions["team1"]["players"].items()
                    }
                },
                "team2": {
                    "name": team2,
                    "players": {
                        player: {
                            "batting": pred.get("batting", {}),
                            "bowling": pred.get("bowling", {})
                        }
                        for player, pred in predictions["team2"]["players"].items()
                    }
                }
            },
            "exported_files": exported_files,
            "database_updated": update_db
        }
        
        return Response(result)
    
    except ImportError as e:
        return Response(
            {"error": f"Required module not found: {str(e)}"},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
    except Exception as e:
        logging.error(f"Error in predict_player_performance view: {str(e)}")
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
