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
def predict_team(request):
    """
    API endpoint that predicts Dream11 teams based on input parameters.
    
    Parameters:
    - team1: Name of the first team
    - team2: Name of the second team
    - budget: Total budget in crores (optional, default: 100)
    
    Returns:
    - The best predicted team composition
    """
    try:
        # Extract parameters
        team1_raw = request.data.get('team1')
        team2_raw = request.data.get('team2')
        
        # Normalise to string for later comparisons
        team1_name, team2_name = str(team1_raw).strip(), str(team2_raw).strip()
        
        try:
            budget = float(request.data.get('budget', 100))
        except (TypeError, ValueError):
            return Response({"error": "Budget must be a number"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate parameters
        if not all([team1_name, team2_name]):
            return Response({"error": "Both team names are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get team objects from database if they exist
        team1 = None
        team2 = None
        
        try:
            # First try to get by ID if numeric
            if team1_name.isdigit():
                team1 = Team.objects.get(id=int(team1_name))
            if team2_name.isdigit():
                team2 = Team.objects.get(id=int(team2_name))
        except (Team.DoesNotExist, ValueError, AttributeError):
            # Added AttributeError to the exceptions we catch
            pass
        
        # If not found by ID, try by name
        if not team1:
            try:
                team1 = Team.objects.get(name__iexact=team1_name)
            except Team.DoesNotExist:
                pass
                
        if not team2:
            try:
                team2 = Team.objects.get(name__iexact=team2_name)
            except Team.DoesNotExist:
                pass
        
        # Use direct prediction from our logic module if teams not in database
        if not team1 or not team2:
            # Use the prediction logic directly
            from .logic.prediction import Dream11TeamPredictor
            
            # Initialize predictor with the data folder
            data_folder = os.path.join(os.path.dirname(settings.BASE_DIR), 'data', 'IPL-DATASET')
            predictor = Dream11TeamPredictor(data_folder)
            
            # Make prediction
            team_prediction = predictor.predict_team(team1_name, team2_name, budget=budget)
            
            # Format for response
            response_data = {
                "message": "Prediction successful using direct prediction logic",
                "prediction": {
                    "team": [
                        {
                            "name": player["name"],
                            "role": player["role"],
                            "fantasy_points": player.get("fantasy_points", 0),
                            "team": player["team"]
                        } for player in team_prediction["team"]
                    ],
                    "score": team_prediction["score"],
                    "budget_used": team_prediction["budget_used"],
                    "budget_remaining": team_prediction["budget_remaining"],
                    "roles": team_prediction["roles"],
                    "team_distribution": team_prediction["team_distribution"]
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        # If we have the teams in the database, use the database approach
        # Get players from both teams
        team1_players = Player.objects.filter(team=team1)
        team2_players = Player.objects.filter(team=team2)
        all_players = list(team1_players) + list(team2_players)
        
        # Create a new prediction record
        prediction = Prediction.objects.create(
            user=request.user,
            team1=team1,
            team2=team2,
            prediction_type='BAL'  # Balanced prediction
        )
        
        # Sort players by fantasy points
        sorted_players = sorted(all_players, key=lambda p: p.fantasy_points, reverse=True)
        
        # Define role mapping to normalize between DB abbreviations and full names
        role_map = {
            "BAT": "Batsman", 
            "BWL": "Bowler", 
            "AR": "All-Rounder", 
            "WK": "Wicket-Keeper"
        }
        
        # Select top 11 players ensuring at least one wicket keeper
        selected_players = []
        roles = {"Batsman": 0, "Bowler": 0, "All-Rounder": 0, "Wicket-Keeper": 0}
        team_counts = {team1.name: 0, team2.name: 0}
        
        # First, select one wicket keeper
        wks = [p for p in sorted_players if role_map.get(p.role, p.role) == "Wicket-Keeper"]
        if wks:
            selected_players.append(wks[0])
            roles["Wicket-Keeper"] += 1
            team_counts[wks[0].team.name] += 1
        
        # Then select the rest based on fantasy points
        for player in sorted_players:
            if len(selected_players) >= 11:
                break
                
            if player in selected_players:
                continue
                  # Check team limit (max 7 players per team)
            if team_counts.get(player.team.name, 0) >= 7:
                continue
                
            # Add player
            selected_players.append(player)
            canonical_role = role_map.get(player.role, player.role)
            roles[canonical_role] += 1
            team_counts[player.team.name] = team_counts.get(player.team.name, 0) + 1
        
        # Save the selected players to the prediction
        total_points = 0
        for player in selected_players:
            # Randomly assign captain and vice-captain for now
            is_captain = False
            is_vice_captain = False
            
            if player == selected_players[0]:  # Top player is captain
                is_captain = True
            elif player == selected_players[1]:  # Second best player is vice-captain
                is_vice_captain = True
                
            pp = PredictionPlayer.objects.create(
                prediction=prediction,
                player=player,
                is_captain=is_captain,
                is_vice_captain=is_vice_captain,
                expected_points=player.fantasy_points
            )
            
            # Add to total points (captain gets 2x, vice-captain 1.5x)
            if is_captain:
                total_points += player.fantasy_points * 2
            elif is_vice_captain:
                total_points += player.fantasy_points * 1.5
            else:
                total_points += player.fantasy_points
        
        # Generate response with prediction details
        response_data = {
            "message": "Prediction successful",
            "prediction": PredictionDetailSerializer(prediction).data,
            "team_summary": {
                "total_points": total_points,
                "roles": roles,
                "team_distribution": team_counts
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logging.error(f"Error in predict_team: {str(e)}")
        import traceback
        return Response({
            "error": str(e), 
            "traceback": traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def load_csv_data(request):
    """
    Load data from all CSV files in the data directory.
    This will parse the files and store the data in the database.
    """
    try:
        from .logic.prediction import Dream11TeamPredictor
        import os
        from django.conf import settings
        
        # Determine the data folder path
        data_folder = os.path.join(os.path.dirname(settings.BASE_DIR), 'data', 'IPL-DATASET')
        if not os.path.exists(data_folder):
            return Response(
                {"error": f"Data folder not found at {data_folder}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Initialize the predictor with the data folder
        predictor = Dream11TeamPredictor(data_folder)
        
        # Get teams and player data
        teams = predictor.get_all_teams()
        
        # Create or update team records in database
        for team_name in teams:
            team, created = Team.objects.get_or_create(
                name=team_name,
                defaults={
                    'short_name': team_name[:3].upper(),
                    'location': team_name.split(' ')[0] if ' ' in team_name else team_name
                }
            )
            
            # Get players for this team
            players = predictor.get_team_players(team_name)
            
            # Create or update player records
            for player_data in players:
                player_name = player_data["name"]
                player_role = player_data["role"]
                
                player, created = Player.objects.get_or_create(
                    name=player_name,
                    defaults={
                        'team': team,
                        'role': player_role,
                        'fantasy_points': 0,
                        'recent_form': 0
                    }
                )
                
                if not created:
                    # Update existing player's team and role
                    player.team = team
                    player.role = player_role
                    player.save()
        
        # Calculate player fantasy points and update the database
        for team1 in teams:
            for team2 in teams:
                if team1 != team2:
                    player_scores = predictor.calculate_player_scores(team1, team2)
                    
                    # Update fantasy points for players
                    for player_name, data in player_scores.items():
                        try:
                            player = Player.objects.get(name=player_name)
                            player.fantasy_points = data["fantasy_points"]
                            player.recent_form = data["fantasy_points"] * 0.8  # Simulating recent form
                            player.save()
                        except Player.DoesNotExist:
                            pass  # Skip players not found in the database
        
        return Response({
            "message": "Data loaded successfully",
            "teams_loaded": len(teams),
            "players_loaded": Player.objects.count()
        })
    
    except Exception as e:
        import traceback
        return Response(
            {
                "error": f"Failed to load data: {str(e)}",
                "traceback": traceback.format_exc()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
