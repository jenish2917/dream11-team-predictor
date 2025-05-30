from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.conf import settings
from django.core.management import call_command
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

# Import prediction views
from .prediction_views import predict_player_performance

from .models import (
    UserProfile, Team, Venue, Player, 
    Prediction, PredictionPlayer, PlayerComment, PredictionLike
)
from .serializers import (
    UserSerializer, UserProfileSerializer, TeamSerializer, 
    VenueSerializer, PlayerSerializer, PlayerDetailSerializer,
    PredictionSerializer, PredictionDetailSerializer,
    PredictionPlayerSerializer, PlayerCommentSerializer,
    PredictionLikeSerializer, UserRegistrationSerializer
)

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import os
import logging
from datetime import datetime, timedelta

# Import scraper and stats update tools
try:
    from .management.commands.scrape_cricinfo import ESPNCricinfoScraper
    from .management.commands.update_stats import Command as UpdateStatsCommand
except ImportError:
    logging.error("Failed to import ESPNCricinfo scraper or stats update command")

# Configuration for scraper integration
SCRAPER_ENABLED = True
DEFAULT_SCRAPER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'management', 'commands')


# Authentication Views
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return get_object_or_404(UserProfile, user=self.request.user)


# Team and Venue Views
class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def players(self, request, pk=None):
        """Get all players for a specific team."""
        team = self.get_object()
        players = team.players.all()
        serializer = PlayerSerializer(players, many=True)
        return Response(serializer.data)

class VenueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    permission_classes = [IsAuthenticated]


# Player Views
class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Player.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PlayerDetailSerializer
        return PlayerSerializer
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        player = self.get_object()
        comments = player.comments.all().order_by('-created_at')
        serializer = PlayerCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        player = self.get_object()
        serializer = PlayerCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, player=player)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=True, methods=['get'])
    def enhanced_stats(self, request, pk=None):
        """
        Get enhanced player statistics including consistency indices and
        performance against different teams/venues.
        """
        player = self.get_object()
        
        try:
            # Import player stats processor
            from .management.commands.process_player_stats import PlayerStatsProcessor
            
            # Initialize processor
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'management', 'commands', 'cricket_data')
            processor = PlayerStatsProcessor(data_dir)
            
            # Load and clean data
            success = processor.load_data()
            if not success:
                return Response({"error": "Failed to load player data"}, status=status.HTTP_404_NOT_FOUND)
            
            processor.clean_data()
            
            # Generate enhanced profile
            profile = processor.player_profile(player.name)
            
            # Add base player data
            profile.update({
                "id": player.id,
                "team": player.team.name if player.team else None,
                "role": player.role,
                "fantasy_points": player.recent_form
            })
            
            # Add ML predictions if available in the player model
            if player.opposition_performance and 'ml_prediction' in player.opposition_performance:
                profile['ml_predictions'] = {
                    'batting': player.opposition_performance['ml_prediction']
                }
                
            if player.venue_performance and 'ml_prediction' in player.venue_performance:
                if 'ml_predictions' not in profile:
                    profile['ml_predictions'] = {}
                profile['ml_predictions']['bowling'] = player.venue_performance['ml_prediction']
            
            return Response(profile)
            
        except ImportError:
            return Response(
                {"error": "Enhanced statistics processing is not available"}, 
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        except Exception as e:
            logging.error(f"Error in enhanced_stats: {str(e)}")
            return Response(
                {"error": f"Failed to process enhanced statistics: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @action(detail=True, methods=['get'])
    def ml_prediction(self, request, pk=None):
        """
        Get machine learning-based performance prediction for a player.
        Predicts runs/wickets and performance category (High/Medium/Low)
        for upcoming matches.
        """
        player = self.get_object()
        
        # Get query parameters for match context
        opposing_team = request.query_params.get('opposing_team')
        venue = request.query_params.get('venue')
        
        if not (opposing_team and venue):
            return Response(
                {"error": "opposing_team and venue parameters are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Import player performance predictor
            from .player_performance_predictor_fixed import PlayerPerformancePredictor
            
            # Initialize predictor
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'management', 'commands', 'cricket_data')
            predictor = PlayerPerformancePredictor(data_dir)
            
            # Load existing models
            success = predictor.load_models()
            if not success:
                return Response({"error": "ML models not found. Models need to be trained first."}, 
                               status=status.HTTP_404_NOT_FOUND)
            
            # Prepare player data for prediction
            player_data = {
                'player_name': player.name,
                'role': player.role,
                'team': player.team.name if player.team else 'Unknown',
                'opposing_team': opposing_team,
                'venue': venue
            }            # Import helper function
            from .ml_prediction_helpers import prepare_player_input_features
            
            # Prepare input features for prediction
            batting_input = prepare_player_input_features(player_data, 'batting')
            bowling_input = prepare_player_input_features(player_data, 'bowling')
            
            # Get predictions for both batting and bowling
            batting_prediction = predictor.predict_performance(batting_input, prediction_type='batting')
            bowling_prediction = predictor.predict_performance(bowling_input, prediction_type='bowling')
            
            # Combine predictions
            prediction = {
                "id": player.id,
                "name": player.name,
                "team": player.team.name if player.team else None,
                "role": player.role,
                "batting_prediction": batting_prediction,
                "bowling_prediction": bowling_prediction
            }
            
            return Response(prediction)
            
        except Exception as e:
            logging.error(f"Error in player ML prediction: {str(e)}")
            return Response(
                {"error": f"Failed to generate ML prediction: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def performance_chart(self, request, pk=None):
        """
        Get a performance chart for the player's recent matches.
        Returns the URL to the generated chart image.
        """
        player = self.get_object()
        chart_type = request.query_params.get('type', 'form')  # form or opposition
        
        try:
            # Import player stats processor
            from .management.commands.process_player_stats import PlayerStatsProcessor
            
            # Initialize processor
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'management', 'commands', 'cricket_data')
            processor = PlayerStatsProcessor(data_dir)
            
            # Load and clean data
            success = processor.load_data()
            if not success:
                return Response({"error": "Failed to load player data"}, status=status.HTTP_404_NOT_FOUND)
            
            processor.clean_data()
            
            # Generate chart
            chart_path = None
            if chart_type == 'form':
                chart_path = processor.plot_recent_form(player.name)
            elif chart_type == 'opposition':
                chart_path = processor.plot_opposition_performance(player.name)
            else:
                return Response({"error": "Invalid chart type"}, status=status.HTTP_400_BAD_REQUEST)
            
            if chart_path:
                # Get the relative path for URL
                base_dir = os.path.dirname(os.path.abspath(__file__))
                rel_path = os.path.relpath(chart_path, base_dir)
                  # Return URL to chart
                request_host = request.get_host()
                
                # Ensure the chart is saved in the media directory
                from django.conf import settings
                media_root = settings.MEDIA_ROOT
                player_charts_dir = os.path.join(media_root, 'player_charts')
                
                # Create directory if it doesn't exist
                os.makedirs(player_charts_dir, exist_ok=True)
                
                # Copy/save the chart to the media directory
                import shutil
                filename = f"{player.name.replace(' ', '_')}_{chart_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                media_chart_path = os.path.join(player_charts_dir, filename)
                shutil.copy2(chart_path, media_chart_path)
                
                # Generate proper URL using MEDIA_URL
                chart_url = f"/media/player_charts/{filename}"
                
                return Response({
                    "player": player.name,
                    "chart_type": chart_type,
                    "chart_url": chart_url,
                    "chart_path": os.path.relpath(media_chart_path, settings.BASE_DIR)
                })
            else:
                return Response(
                    {"error": "Failed to generate chart"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except ImportError:
            return Response(
                {"error": "Performance chart generation is not available"}, 
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        except Exception as e:
            logging.error(f"Error in performance_chart: {str(e)}")
            return Response(
                {"error": f"Failed to generate performance chart: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Prediction Views
class PredictionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            return Prediction.objects.filter(user=self.request.user).order_by('-created_at')
        return Prediction.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PredictionDetailSerializer
        return PredictionSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        prediction = self.get_object()
        like, created = PredictionLike.objects.get_or_create(
            user=request.user,
            prediction=prediction,
            defaults={'is_like': True}
        )
        
        if not created and not like.is_like:
            like.is_like = True
            like.save()
            
        return Response({'status': 'prediction liked'})
    
    @action(detail=True, methods=['post'])
    def dislike(self, request, pk=None):
        prediction = self.get_object()
        like, created = PredictionLike.objects.get_or_create(
            user=request.user,
            prediction=prediction,
            defaults={'is_like': False}
        )
        
        if not created and like.is_like:
            like.is_like = False
            like.save()
            
        return Response({'status': 'prediction disliked'})


# Prediction API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_team(request):
    """
    API endpoint that predicts Dream11 teams based on input parameters.
    
    Parameters:
    - team1: ID of the first team
    - team2: ID of the second team
    - venue: ID of the venue
    - pitch_type: Type of pitch (BAT/BWL/BAL/SPIN)
    
    Returns:
    - Three predicted team compositions (Aggressive, Balanced, Risk-averse)
    """
    try:
        # Extract parameters
        team1_id = request.data.get('team1')
        team2_id = request.data.get('team2')
        venue_id = request.data.get('venue')
        pitch_type = request.data.get('pitch_type')
        
        # Validate parameters
        if not all([team1_id, team2_id, venue_id, pitch_type]):
            return Response({"error": "All parameters are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get objects
        team1 = get_object_or_404(Team, pk=team1_id)
        team2 = get_object_or_404(Team, pk=team2_id)
        venue = get_object_or_404(Venue, pk=venue_id)
        
        # Get players from both teams
        team1_players = Player.objects.filter(team=team1)
        team2_players = Player.objects.filter(team=team2)
        all_players = list(team1_players) + list(team2_players)        # Use our enhanced prediction algorithm to generate team recommendations
        from .prediction_algorithm_enhanced import TeamPredictor
        
        # Get ML predictions if available
        try:
            from .player_performance_predictor_fixed import PlayerPerformancePredictor
            
            # Initialize ML predictor
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'management', 'commands', 'cricket_data')
            ml_predictor = PlayerPerformancePredictor(data_dir)
            
            # Try to load ML models
            if ml_predictor.load_models():
                # Generate ML predictions for all players
                ml_predictions = {}
                for player in all_players:
                    player_data = {
                        'player_name': player.name,
                        'role': player.role,
                        'team': player.team.name,
                        'opposing_team': team2.name if player.team == team1 else team1.name,
                        'venue': venue.name
                    }
                    player_prediction = ml_predictor.predict_performance(player_data)
                    ml_predictions[player.id] = player_prediction
                    
                # Create enhanced predictor with ML predictions
                predictor = TeamPredictor(team1_id, team2_id, venue_id, pitch_type, ml_predictions=ml_predictions)
            else:
                # Fall back to standard predictor if ML models aren't available
                predictor = TeamPredictor(team1_id, team2_id, venue_id, pitch_type)
        except Exception as e:
            logging.warning(f"ML predictions unavailable: {str(e)}. Using standard predictor.")
            predictor = TeamPredictor(team1_id, team2_id, venue_id, pitch_type)
            
        predictions = predictor.predict_teams()
        
        # Save predictions to database
        for pred_type, players_data in predictions.items():
            prediction = Prediction.objects.create(
                user=request.user,
                team1=team1,
                team2=team2,
                venue=venue,
                pitch_type=pitch_type,
                prediction_type=pred_type
            )
            
            # Save the individual players in the prediction
            for player_data in players_data:
                PredictionPlayer.objects.create(
                    prediction=prediction,
                    player=player_data['player'],
                    is_captain=player_data['is_captain'],
                    is_vice_captain=player_data['is_vice_captain'],
                    expected_points=player_data['expected_points']
                )
        
        # Generate response with prediction details
        response_data = {
            "message": "Prediction successful",
            "predictions": {
                "AGG": PredictionDetailSerializer(
                    Prediction.objects.filter(user=request.user, team1=team1, team2=team2, prediction_type='AGG')
                    .order_by('-created_at').first()
                ).data,
                "BAL": PredictionDetailSerializer(
                    Prediction.objects.filter(user=request.user, team1=team1, team2=team2, prediction_type='BAL')
                    .order_by('-created_at').first()
                ).data,
                "RISK": PredictionDetailSerializer(
                    Prediction.objects.filter(user=request.user, team1=team1, team2=team2, prediction_type='RISK')
                    .order_by('-created_at').first()
                ).data
            },
            "graphs": generate_mock_graphs(team1, team2)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Mock data generation helpers
def generate_mock_predictions(all_players, team1, team2, venue, pitch_type):
    """Generate mock predictions for demo purposes"""
    import random
    
    # Random seed for reproducibility
    random.seed(hash(f"{team1.id}_{team2.id}_{venue.id}_{pitch_type}"))
    
    # Assign random "fantasy points" based on role and pitch type
    for player in all_players:
        base_points = random.uniform(20, 80)
        
        # Role-based adjustment
        if player.role == 'BAT' and pitch_type == 'BAT':
            base_points *= 1.3
        elif player.role == 'BWL' and pitch_type == 'BWL':
            base_points *= 1.3
        elif player.role == 'AR':
            base_points *= 1.1
        
        player.expected_points = round(base_points, 1)
    
    # Sort players by expected points
    all_players.sort(key=lambda p: p.expected_points, reverse=True)
    
    # Select different players for different strategies
    predictions = {}
    
    # Aggressive Strategy (more batsmen)
    agg_players = select_players(all_players, strategy='AGG')
    predictions['AGG'] = [
        {
            'player': player,
            'is_captain': i == 0,
            'is_vice_captain': i == 1,
            'expected_points': player.expected_points
        }
        for i, player in enumerate(agg_players)
    ]
    
    # Balanced Strategy
    bal_players = select_players(all_players, strategy='BAL')
    predictions['BAL'] = [
        {
            'player': player,
            'is_captain': i == 0,
            'is_vice_captain': i == 1,
            'expected_points': player.expected_points
        }
        for i, player in enumerate(bal_players)
    ]
    
    # Risk-averse Strategy (more bowlers)
    risk_players = select_players(all_players, strategy='RISK')
    predictions['RISK'] = [
        {
            'player': player,
            'is_captain': i == 0,
            'is_vice_captain': i == 1,
            'expected_points': player.expected_points
        }
        for i, player in enumerate(risk_players)
    ]
    
    return predictions


def select_players(all_players, strategy='BAL'):
    """Select 11 players based on strategy"""
    import random
    
    # Create a copy to avoid modifying the original list
    available_players = all_players.copy()
    
    # Set target counts based on strategy
    if strategy == 'AGG':
        targets = {'BAT': 5, 'BWL': 3, 'AR': 2, 'WK': 1}
    elif strategy == 'BAL':
        targets = {'BAT': 4, 'BWL': 4, 'AR': 2, 'WK': 1}
    else:  # RISK
        targets = {'BAT': 3, 'BWL': 5, 'AR': 2, 'WK': 1}
    
    selected = []
    counts = {'BAT': 0, 'BWL': 0, 'AR': 0, 'WK': 0}
    
    # First pass: select top players by role to meet minimum requirements
    for role, target in targets.items():
        role_players = [p for p in available_players if p.role == role]
        role_players.sort(key=lambda p: p.expected_points, reverse=True)
        
        for player in role_players[:target]:
            selected.append(player)
            available_players.remove(player)
            counts[role] += 1
    
    # Fill remaining slots with highest expected points
    remaining_slots = 11 - len(selected)
    remaining_players = sorted(available_players, key=lambda p: p.expected_points, reverse=True)
    selected.extend(remaining_players[:remaining_slots])
    
    # Sort selected players by expected points for captain selection
    selected.sort(key=lambda p: p.expected_points, reverse=True)
    return selected


def generate_mock_graphs(team1, team2):
    """Generate mock graphs for visualization"""
    # In a real app, these would be generated from actual data and predictions
    
    # For demo, we'll return empty placeholder URLs
    # In production, you'd generate actual graphs using matplotlib/seaborn
    # and return the image URLs or base64 encoded images
    
    return {
        "role_distribution": "/media/graphs/role_distribution.png",
        "team_composition": "/media/graphs/team_composition.png",
        "success_rate": "/media/graphs/success_rate.png",
    }


# ESPNCricinfo Scraper API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_match(request, match_id):
    """
    Scrape a specific match by its Cricinfo ID or URL.
    
    Args:
        match_id: The Cricinfo match ID or a full URL
    
    Returns:
        Response with match details or error
    """
    if not SCRAPER_ENABLED:
        return Response(
            {"error": "Scraper functionality is disabled"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Initialize scraper
        scraper = ESPNCricinfoScraper(base_dir=DEFAULT_SCRAPER_DIR)
        
        # Check if input is a full URL or just an ID
        if match_id.startswith('http'):
            match_url = match_id
        else:
            match_url = f"https://www.espncricinfo.com/matches/engine/match/{match_id}.html"
        
        # Scrape match data
        batting_df, bowling_df = scraper.scrape_match_scorecard(match_url)
        
        if batting_df.empty and bowling_df.empty:
            return Response(
                {"error": "Failed to scrape match data"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Process the result
        result = {
            "match_id": match_id,
            "url": match_url,
            "batting_performances": len(batting_df),
            "bowling_performances": len(bowling_df),
            "teams": list(batting_df['team'].unique()) if not batting_df.empty else [],
            "top_scorer": batting_df.loc[batting_df['runs'].idxmax()]['player_name'] if not batting_df.empty else None,
            "top_wicket_taker": bowling_df.loc[bowling_df['wickets'].idxmax()]['player_name'] if not bowling_df.empty else None,
        }
        
        # Check if we should update player stats
        update_stats = request.data.get('update_stats', False)
        if update_stats:
            # Import to Django DB
            success = scraper.import_data_to_django()
            result["data_imported"] = success
            
            if success:
                # Update player stats
                update_command = UpdateStatsCommand()
                update_command.handle(dry_run=False, days=90)
                result["player_stats_updated"] = True
        
        return Response(result)
    
    except Exception as e:
        logging.error(f"Error in scrape_match view: {str(e)}")
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_player(request, player_id):
    """
    Scrape a specific player's profile by their Cricinfo ID.
    
    Args:
        player_id: The Cricinfo player ID
    
    Returns:
        Response with player details or error
    """
    if not SCRAPER_ENABLED:
        return Response(
            {"error": "Scraper functionality is disabled"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Initialize scraper
        scraper = ESPNCricinfoScraper(base_dir=DEFAULT_SCRAPER_DIR)
        
        # Scrape player data
        player_data = scraper.scrape_player_profile(player_id)
        
        if not player_data:
            return Response(
                {"error": "Failed to scrape player data"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if we should update player stats
        update_stats = request.data.get('update_stats', False)
        if update_stats:
            # Import to Django DB
            success = scraper.import_data_to_django()
            player_data["data_imported"] = success
        
        return Response(player_data)
    
    except Exception as e:
        logging.error(f"Error in scrape_player view: {str(e)}")
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scrape_season(request, year):
    """
    Scrape all matches for a specific IPL season.
    
    Args:
        year: The year of the IPL season
    
    Returns:
        Response with season details or error
    """
    if not SCRAPER_ENABLED:
        return Response(
            {"error": "Scraper functionality is disabled"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Initialize scraper
        scraper = ESPNCricinfoScraper(base_dir=DEFAULT_SCRAPER_DIR)
        
        # Get custom series ID if provided
        series_id = request.data.get('series_id', None)
        
        # Scrape season matches
        matches_df = scraper.scrape_ipl_matches(year, series_id)
        
        if matches_df.empty:
            return Response(
                {"error": f"Failed to scrape matches for IPL {year}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Process the result
        result = {
            "season": year,
            "matches_found": len(matches_df),
            "series_id": series_id,
            "teams": list(set(list(matches_df['team1'].unique()) + list(matches_df['team2'].unique()))),
            "venues": list(matches_df['venue'].unique()),
        }
        
        # Check if we should also scrape match details
        scrape_matches = request.data.get('scrape_matches', False)
        if scrape_matches:
            result["match_details_scraped"] = 0
            
            # Limit to first 5 matches if there are many
            max_matches = min(5, len(matches_df)) if request.data.get('limit_matches', True) else len(matches_df)
            
            for i in range(max_matches):
                match_url = matches_df.iloc[i]['match_url']
                batting_df, bowling_df = scraper.scrape_match_scorecard(match_url)
                
                if not batting_df.empty or not bowling_df.empty:
                    result["match_details_scraped"] += 1
        
        # Check if we should update player stats
        update_stats = request.data.get('update_stats', False)
        if update_stats:
            # Import to Django DB
            success = scraper.import_data_to_django()
            result["data_imported"] = success
            
            if success:
                # Update player stats
                update_command = UpdateStatsCommand()
                update_command.handle(dry_run=False, days=90)
                result["player_stats_updated"] = True
        
        return Response(result)
    
    except Exception as e:
        logging.error(f"Error in scrape_season view: {str(e)}")
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_player_stats(request):
    """
    Update player statistics based on scraped data.
    
    Args:
        request: May contain 'dry_run' and 'days' parameters
    
    Returns:
        Response with update results or error
    """
    if not SCRAPER_ENABLED:
        return Response(
            {"error": "Scraper functionality is disabled"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Get parameters
        dry_run = request.data.get('dry_run', False)
        days = request.data.get('days', 90)
        
        # Update player stats
        update_command = UpdateStatsCommand()
        
        # Use internal tracking to get stats before and after
        players_before = {}
        for player in Player.objects.all():
            players_before[player.id] = {
                'name': player.name,
                'batting_average': player.batting_average,
                'bowling_average': player.bowling_average,
                'recent_form': player.recent_form
            }
        
        # Run the update
        updated_count = update_command.handle(dry_run=dry_run, days=days)
        
        # Get stats after update
        players_after = {}
        changes = []
        
        for player in Player.objects.all():
            players_after[player.id] = {
                'name': player.name,
                'batting_average': player.batting_average,
                'bowling_average': player.bowling_average,
                'recent_form': player.recent_form
            }
            
            # Check for changes
            if player.id in players_before:
                before = players_before[player.id]
                change = {}
                
                for stat in ['batting_average', 'bowling_average', 'recent_form']:
                    if before[stat] != players_after[player.id][stat]:
                        change[f'old_{stat}'] = before[stat]
                        change[f'new_{stat}'] = players_after[player.id][stat]
                
                if change:
                    change['player_id'] = player.id
                    change['player_name'] = player.name
                    changes.append(change)
        
        result = {
            "dry_run": dry_run,
            "days_considered": days,
            "players_updated": len(changes),
            "updated_players": changes[:10] if changes else []  # Limit to first 10 for brevity
        }
        
        if len(changes) > 10:
            result["note"] = f"Showing only the first 10 of {len(changes)} updated players"
        
        return Response(result)
    
    except Exception as e:
        logging.error(f"Error in update_player_stats view: {str(e)}")
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enhance_player_stats(request):
    """
    Process player statistics to generate enhanced metrics.
    
    Args:
        request: May contain 'player', 'dry_run', and 'export_format' parameters
    
    Returns:
        Response with enhancement results or error
    """
    if not SCRAPER_ENABLED:
        return Response(
            {"error": "Stats enhancement is disabled"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Import player stats processor
        from .management.commands.process_player_stats import PlayerStatsProcessor
        from django.core.management import call_command
        
        # Get parameters
        player_name = request.data.get('player', None)
        dry_run = request.data.get('dry_run', True)
        export_format = request.data.get('export_format', 'json')
        generate_plots = request.data.get('generate_plots', False)
        
        # Initialize processor
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'management', 'commands', 'cricket_data')
        processor = PlayerStatsProcessor(data_dir)
        
        # Load and clean data
        success = processor.load_data()
        if not success:
            return Response(
                {"error": "Failed to load player data. Ensure scraped data exists."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        processor.clean_data()
        
        # Process data based on request
        result = {
            "status": "success",
            "dry_run": dry_run,
            "generated_files": []
        }
        
        # Process specific player if requested
        if player_name:
            profile = processor.player_profile(player_name)
            result["player"] = player_name
            result["profile"] = profile
            
            # Generate plots if requested
            if generate_plots:
                form_plot = processor.plot_recent_form(player_name)
                if form_plot:
                    result["generated_files"].append({"type": "form_plot", "path": form_plot})
                
                opposition_plot = processor.plot_opposition_performance(player_name)
                if opposition_plot:
                    result["generated_files"].append({"type": "opposition_plot", "path": opposition_plot})
        
        else:
            # Export profiles in requested format
            if export_format in ['json', 'both']:
                json_path = processor.export_player_profiles('json')
                if json_path:
                    result["generated_files"].append({"type": "json_profiles", "path": json_path})
            
            if export_format in ['csv', 'both']:
                csv_path = processor.export_player_profiles('csv')
                if csv_path:
                    result["generated_files"].append({"type": "csv_profiles", "path": csv_path})
        
            # Generate top player plots if requested
            if generate_plots:
                # Get top players by runs
                top_players = []
                if not processor.batting_df.empty and 'player_name' in processor.batting_df.columns:
                    top_players = processor.batting_df.groupby('player_name')['runs'].sum().nlargest(5).index.tolist()
                
                plots_generated = []
                for player in top_players:
                    form_plot = processor.plot_recent_form(player)
                    if form_plot:
                        plots_generated.append({"player": player, "type": "form", "path": form_plot})
                
                result["top_player_plots"] = plots_generated
        
        # Update database if requested
        if not dry_run:
            # Use Django management command to update database
            call_command('enhance_player_stats', 
                        player=player_name,
                        update_db=True,
                        dry_run=False,
                        verbosity=0)
            
            result["database_updated"] = True
        
        return Response(result)
    
    except Exception as e:
        logging.error(f"Error in enhance_player_stats view: {str(e)}")
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
