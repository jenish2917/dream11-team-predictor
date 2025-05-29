"""
Django management command to train and apply machine learning models for player performance prediction.
"""

import os
import json
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from predictor.models import Player, Team, Venue
from django.conf import settings

# Import the fixed player performance predictor
from ...player_performance_predictor_fixed import PlayerPerformancePredictor
from ...ml_prediction_helpers import prepare_player_input_features

class Command(BaseCommand):
    help = 'Train machine learning models for player performance prediction'
    
    def add_arguments(self, parser):
        parser.add_argument('--data-dir', type=str, help='Directory containing cricket data files')
        parser.add_argument('--train', action='store_true', help='Train new models')
        parser.add_argument('--predict', action='store_true', help='Generate predictions for upcoming matches')
        parser.add_argument('--team1', type=str, help='First team for match prediction')
        parser.add_argument('--team2', type=str, help='Second team for match prediction')
        parser.add_argument('--venue', type=str, help='Venue for match prediction')
        parser.add_argument('--export', type=str, choices=['json', 'csv', 'both'], 
                            default='json', help='Export format for predictions')
        parser.add_argument('--update-db', action='store_true', help='Update Django database with predicted stats')
    
    def handle(self, *args, **options):
        data_dir = options.get('data_dir')
        train_models = options.get('train', False)
        make_predictions = options.get('predict', False)
        team1 = options.get('team1')
        team2 = options.get('team2')
        venue = options.get('venue')
        export_format = options.get('export', 'json')
        update_db = options.get('update_db', False)
        
        # Set data directory to default if not provided
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cricket_data')
            self.stdout.write(f"Using default data directory: {data_dir}")
        
        # Initialize predictor
        predictor = PlayerPerformancePredictor(data_dir)
        
        if train_models:
            self.stdout.write(self.style.MIGRATE_HEADING('Training ML models for player performance prediction...'))
            
            # Load data
            success = predictor.load_data()
            if not success:
                self.stdout.write(self.style.ERROR('Failed to load data. Please check the data directory.'))
                return
            
            # Train models
            success = predictor.train_models()
            if success:
                self.stdout.write(self.style.SUCCESS('Successfully trained models!'))
            else:
                self.stdout.write(self.style.ERROR('Error training models.'))
        
        elif make_predictions:
            if not all([team1, team2, venue]):
                self.stdout.write(self.style.ERROR('To make predictions, you must provide --team1, --team2, and --venue.'))
                return
            
            self.stdout.write(self.style.MIGRATE_HEADING(f'Predicting performance for {team1} vs {team2} at {venue}...'))
            
            # Try to load existing models first
            success = predictor.load_models()
            if not success:
                # If can't load models, try to train new ones
                self.stdout.write('No pre-trained models found. Training new models...')
                
                # Load data
                success = predictor.load_data()
                if not success:
                    self.stdout.write(self.style.ERROR('Failed to load data. Please check the data directory.'))
                    return
                
                # Train models
                success = predictor.train_models()
                if not success:
                    self.stdout.write(self.style.ERROR('Failed to train models.'))
                    return
            
            # Generate predictions
            predictions = predictor.generate_match_predictions(team1, team2, venue)
            
            if not predictions:
                self.stdout.write(self.style.ERROR('Failed to generate predictions.'))
                return
            
            # Export predictions
            if export_format in ['json', 'both']:
                json_path = predictor.export_predictions(predictions, 'json')
                if json_path:
                    self.stdout.write(self.style.SUCCESS(f'Exported predictions to {json_path}'))
            
            if export_format in ['csv', 'both']:
                csv_path = predictor.export_predictions(predictions, 'csv')
                if csv_path:
                    self.stdout.write(self.style.SUCCESS(f'Exported predictions to {csv_path}'))
            
            # Print summary
            self.stdout.write(self.style.MIGRATE_HEADING('Prediction Summary:'))
            self.stdout.write(f"Match: {team1} vs {team2} at {venue}")
            
            # Team 1 players
            self.stdout.write(f"\n{team1} Players:")
            team1_players = predictions['team1']['players']
            for player, pred in team1_players.items():
                output = f"- {player}: "
                if 'batting' in pred:
                    output += f"Runs {pred['batting'].get('predicted_runs', 'N/A')} ({pred['batting'].get('performance_class', 'N/A')}) "
                if 'bowling' in pred:
                    output += f"Wickets {pred['bowling'].get('predicted_wickets', 'N/A')} ({pred['bowling'].get('performance_class', 'N/A')})"
                self.stdout.write(output)
            
            # Team 2 players
            self.stdout.write(f"\n{team2} Players:")
            team2_players = predictions['team2']['players']
            for player, pred in team2_players.items():
                output = f"- {player}: "
                if 'batting' in pred:
                    output += f"Runs {pred['batting'].get('predicted_runs', 'N/A')} ({pred['batting'].get('performance_class', 'N/A')}) "
                if 'bowling' in pred:
                    output += f"Wickets {pred['bowling'].get('predicted_wickets', 'N/A')} ({pred['bowling'].get('performance_class', 'N/A')})"
                self.stdout.write(output)
            
            # Update database if requested
            if update_db:
                self.update_player_predictions(predictions)
        
        else:
            self.stdout.write(self.style.WARNING(
                'Please specify an action: --train to train models or --predict to make predictions.'
            ))
    
    @transaction.atomic
    def update_player_predictions(self, predictions):
        """
        Update the database with the predicted player stats.
        
        Args:
            predictions: Dictionary of predictions from the ML model
        """
        self.stdout.write(self.style.MIGRATE_HEADING('Updating player predictions in database...'))
        
        teams_updated = set()
        players_updated = 0
        
        # Process Team 1 players
        team1_name = predictions['team1']['name']
        team1_obj, _ = Team.objects.get_or_create(name=team1_name)
        teams_updated.add(team1_name)
        
        for player_name, pred in predictions['team1']['players'].items():
            player, created = Player.objects.get_or_create(
                name=player_name,
                team=team1_obj,
                defaults={
                    'role': self._get_role_from_prediction(pred)
                }
            )
            
            # Update prediction fields
            self._update_player_prediction(player, pred)
            players_updated += 1
        
        # Process Team 2 players
        team2_name = predictions['team2']['name']
        team2_obj, _ = Team.objects.get_or_create(name=team2_name)
        teams_updated.add(team2_name)
        
        for player_name, pred in predictions['team2']['players'].items():
            player, created = Player.objects.get_or_create(
                name=player_name,
                team=team2_obj,
                defaults={
                    'role': self._get_role_from_prediction(pred)
                }
            )
            
            # Update prediction fields
            self._update_player_prediction(player, pred)
            players_updated += 1
        
        # Also create venue if it doesn't exist
        venue_name = predictions['match_details']['venue']
        Venue.objects.get_or_create(name=venue_name)
        
        self.stdout.write(self.style.SUCCESS(
            f'Updated {players_updated} players from {len(teams_updated)} teams in the database.'
        ))
    
    def _get_role_from_prediction(self, prediction):
        """
        Determine player role from prediction data.
        
        Args:
            prediction: Player prediction dictionary
            
        Returns:
            str: Player role (BAT, BWL, AR, WK)
        """
        # Default to batsman
        role = 'BAT'
        
        # Check if both batting and bowling predictions exist
        if 'batting' in prediction and 'bowling' in prediction:
            return 'AR'  # All-rounder
        
        # Check if only bowling prediction exists
        elif 'bowling' in prediction and 'batting' not in prediction:
            return 'BWL'  # Bowler
        
        # Otherwise use role from the prediction if available
        if 'batting' in prediction and 'role' in prediction['batting']:
            role = prediction['batting']['role']
            
        return role
    
    def _update_player_prediction(self, player, prediction):
        """
        Update player model with ML predictions.
        
        Args:
            player: Player model instance
            prediction: Prediction dictionary
        """
        # Update batting predictions
        if 'batting' in prediction:
            if 'predicted_runs' in prediction['batting']:
                # Store predicted runs in recent_form field
                player.recent_form = prediction['batting']['predicted_runs']
                
            if 'performance_class' in prediction['batting']:
                perf_class = prediction['batting']['performance_class']
                
                # Store predictions in JSON fields
                if player.opposition_performance is None:
                    player.opposition_performance = {}
                    
                player.opposition_performance['ml_prediction'] = {
                    'predicted_runs': prediction['batting'].get('predicted_runs', 0),
                    'performance_class': perf_class,
                    'probabilities': prediction['batting'].get('class_probabilities', {})
                }
        
        # Update bowling predictions
        if 'bowling' in prediction:
            if player.venue_performance is None:
                player.venue_performance = {}
                
            player.venue_performance['ml_prediction'] = {
                'predicted_wickets': prediction['bowling'].get('predicted_wickets', 0),
                'performance_class': prediction['bowling'].get('performance_class', 'Medium'),
                'probabilities': prediction['bowling'].get('class_probabilities', {})
            }
        
        player.save()
