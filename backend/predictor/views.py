"""
Dream11 Team Predictor - Consolidated Views

This module contains all API views for the Dream11 team prediction application.
Combines authentication, team/player management, and prediction functionality.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from django.core.management import call_command
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    UserProfile, Team, Venue, Player, 
    Prediction, PredictionPlayer, PlayerComment, PredictionLike
)
from .serializers import (
    UserSerializer, UserProfileSerializer, TeamSerializer, 
    VenueSerializer, PlayerSerializer, PlayerDetailSerializer,
    PredictionSerializer, PredictionDetailSerializer,
    PlayerCommentSerializer,UserRegistrationSerializer
)
from .logic.prediction import predict_team as predict_team_logic, load_player_data, load_match_data, update_player_data

import os
import logging
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Feature flags
SCRAPER_ENABLED = False  # No scraping functionality - using preprocessed data only


# ===== AUTHENTICATION VIEWS =====
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


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view that allows login with email or username
    """
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if username and password:
            # Use Django's authenticate function which will use our custom backend
            user = authenticate(request, username=username, password=password)
            if user:
                # Create tokens for the authenticated user
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data,
                })
            else:
                return Response({
                    'detail': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Fallback to default behavior
        return super().post(request, *args, **kwargs)


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return get_object_or_404(UserProfile, user=self.request.user)


# ===== TEAM AND VENUE VIEWS =====
class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [AllowAny]  # Allow public access for demo

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
    permission_classes = [AllowAny]  # Allow public access for demo


# ===== PLAYER VIEWS =====
class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Player.objects.all()
    permission_classes = [AllowAny]  # Allow public access for demo
    
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
                status=status.HTTP_500_INTERNAL_SERVER_ERROR            )


# ===== PREDICTION VIEWS =====
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


# ===== MAIN PREDICTION API =====

@api_view(['GET'])
@permission_classes([AllowAny])
def api_status(request):
    """
    Simple API status endpoint for testing connectivity.
    """
    return Response({
        "status": "success",
        "message": "Dream11 Team Predictor API is running",
        "version": "1.0.0",
        "endpoints": {
            "teams": "/api/teams/",
            "venues": "/api/venues/",
            "players": "/api/players/",
            "predict_team": "/api/predict/team/",
            "load_data": "/api/load/csv-data/",
            "register": "/api/register/",
            "login": "/api/login/"
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_player_performance(request):
    """
    Predict player performance and return results.
    Consolidated endpoint for player-level predictions.
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
        try:
            team1 = Team.objects.get(id=team1_id)
            team2 = Team.objects.get(id=team2_id)
            venue = Venue.objects.get(id=venue_id)
        except (Team.DoesNotExist, Venue.DoesNotExist) as e:
            return Response(
                {"error": f"Object not found: {str(e)}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Make predictions using the logic module
        prediction_results = predict_team_logic(
            team1_name=team1.name,
            team2_name=team2.name,
            venue_name=venue.name,
            update_data=False  # Don't force data update every prediction
        )
        
        return Response(prediction_results, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in predict_player_performance: {str(e)}")
        return Response(
            {"error": f"Prediction failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow public access for demo
def predict_team(request):
    """
    API endpoint that predicts Dream11 teams based on input parameters.
    
    Parameters:
    - team1: ID or name of the first team
    - team2: ID or name of the second team
    - venue: Venue ID or name (optional)
    - pitchCondition: Pitch condition (optional)
    - date: Match date (optional)
    - budget: Total budget in crores (optional, default: 100)
    
    Returns:
    - The best predicted team composition
    """
    try:
        # Extract parameters
        team1_raw = request.data.get('team1')
        team2_raw = request.data.get('team2')
        venue_raw = request.data.get('venue')
        pitch_condition = request.data.get('pitchCondition')
        match_date = request.data.get('date')
        
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
              # Create a prediction record for tracking
            prediction = Prediction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                team1_name=team1_name,
                team2_name=team2_name,
                venue_name=venue_raw if venue_raw else '',
                prediction_type=pitch_condition if pitch_condition else 'BAL',
                match_date=match_date if match_date else None
            )
            
            # Format for response
            response_data = {
                "id": prediction.id,
                "message": "Prediction successful",
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
            user=request.user if request.user.is_authenticated else None,
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


# Removed all ESPNCricinfo Scraper API Views (scrape_match, scrape_player, scrape_season)
# The application now relies solely on preloaded CSV data

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_player_stats(request):
    """
    Update player statistics based on CSV data.
    This endpoint is kept for compatibility but performs the same function as load_csv_data.
    
    Args:
        request: Not used
    
    Returns:
        Response with status message
    """
    return Response(
        {"message": "Player stats update from external sources is disabled. Please use CSV data loading instead."},
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enhance_player_stats(request):
    """
    Process player statistics to generate enhanced metrics.
    This endpoint is kept for compatibility but is disabled.
    
    Args:
        request: Not used
    
    Returns:
        Response with status message
    """
    return Response(
        {"message": "Stats enhancement is disabled. Using only CSV data."},
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow public access for demo
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
