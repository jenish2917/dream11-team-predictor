"""
Dream11 Team Predictor - API Views for Prediction Functionality

This module contains the API views for handling team prediction requests.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .logic.prediction import predict_team as predict_team_logic, load_player_data, load_match_data, update_player_data
from .models import Player, Team, Venue

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_player_performance(request):
    """
    Predict player performance and return results.
    """
    try:
        # Get input parameters from request
        team1_id = request.data.get('team1')
        team2_id = request.data.get('team2')
        venue_id = request.data.get('venue')
        
        # Validate input
        if not all([team1_id, team2_id, venue_id]):
            return Response(
                {"error": "Missing required parameters: team1, team2, and venue are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get team and venue objects
        team1 = Team.objects.get(id=team1_id)
        team2 = Team.objects.get(id=team2_id)
        venue = Venue.objects.get(id=venue_id)
          # Make predictions
        prediction_results = predict_team_logic(
            team1_name=team1.name,
            team2_name=team2.name,
            venue_name=venue.name,
            update_data=False  # Don't force data update every prediction
        )
        
        return Response(prediction_results, status=status.HTTP_200_OK)
        
    except Team.DoesNotExist:
        return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
    except Venue.DoesNotExist:
        return Response({"error": "Venue not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": f"Prediction failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

