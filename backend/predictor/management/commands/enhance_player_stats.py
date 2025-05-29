"""
Django management command to process player statistics from scraped cricket data.
This enhances player profiles with advanced statistics and visualization.
"""

import os
import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from predictor.models import Player, Team, Venue

# Import the player statistics processor
from .process_player_stats import PlayerStatsProcessor

class Command(BaseCommand):
    help = 'Process player statistics from scraped cricket data'
    
    def add_arguments(self, parser):
        parser.add_argument('--data-dir', type=str, help='Directory containing cricket data files')
        parser.add_argument('--player', type=str, help='Process data for a specific player')
        parser.add_argument('--export', type=str, choices=['json', 'csv', 'both'], 
                            default='json', help='Export format for player profiles')
        parser.add_argument('--plots', action='store_true', help='Generate performance plots')
        parser.add_argument('--update-db', action='store_true', help='Update Django database with processed stats')
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving to database')
    
    def handle(self, *args, **options):
        data_dir = options.get('data_dir')
        player_name = options.get('player')
        export_format = options.get('export', 'json')
        generate_plots = options.get('plots', False)
        update_db = options.get('update_db', False)
        dry_run = options.get('dry_run', False)
        
        # Default data directory if not specified
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cricket_data')
        
        self.stdout.write(self.style.SUCCESS(f"Processing player statistics from {data_dir}"))
        
        # Initialize the processor
        processor = PlayerStatsProcessor(data_dir)
        
        # Load and clean data
        success = processor.load_data()
        if not success:
            raise CommandError("Failed to load data. Ensure data files exist in the specified directory.")
        
        success = processor.clean_data()
        if not success:
            raise CommandError("Failed to clean data. Check the data format and log for details.")
        
        # Process specific player if requested
        if player_name:
            self.stdout.write(f"Processing data for player: {player_name}")
            # Generate player profile
            profile = processor.player_profile(player_name)
            self.stdout.write(json.dumps(profile, indent=2))
            
            # Generate plots if requested
            if generate_plots:
                self.stdout.write(f"Generating performance plots for {player_name}")
                form_plot = processor.plot_recent_form(player_name)
                if form_plot:
                    self.stdout.write(self.style.SUCCESS(f"Recent form plot saved to: {form_plot}"))
                
                opposition_plot = processor.plot_opposition_performance(player_name)
                if opposition_plot:
                    self.stdout.write(self.style.SUCCESS(f"Opposition performance plot saved to: {opposition_plot}"))
        else:
            # Process all players
            self.stdout.write("Processing data for all players")
            
            # Export player profiles
            if export_format == 'json' or export_format == 'both':
                json_path = processor.export_player_profiles('json')
                if json_path:
                    self.stdout.write(self.style.SUCCESS(f"Player profiles exported to JSON: {json_path}"))
            
            if export_format == 'csv' or export_format == 'both':
                csv_path = processor.export_player_profiles('csv')
                if csv_path:
                    self.stdout.write(self.style.SUCCESS(f"Player profiles exported to CSV: {csv_path}"))
                    
            # Generate plots for top players if requested
            if generate_plots:
                self.stdout.write("Generating performance plots for top players")
                # Get top 10 players by runs
                top_batters = []
                if not processor.batting_df.empty and 'player_name' in processor.batting_df.columns:
                    top_batters = processor.batting_df.groupby('player_name')['runs'].sum().nlargest(10).index.tolist()
                
                for player in top_batters:
                    form_plot = processor.plot_recent_form(player)
                    if form_plot:
                        self.stdout.write(f"Plot for {player} saved to: {form_plot}")
        
        # Update database if requested
        if update_db and not dry_run:
            self.update_database(processor)
        elif update_db and dry_run:
            self.preview_database_updates(processor)
            
        self.stdout.write(self.style.SUCCESS("Player statistics processing completed successfully"))
    
    def update_database(self, processor):
        """Update Django database with processed player statistics"""
        self.stdout.write("Updating database with processed statistics...")
        
        try:
            with transaction.atomic():
                # Get unique player names from the processor
                player_names = set()
                
                if not processor.batting_df.empty and 'player_name' in processor.batting_df.columns:
                    player_names.update(processor.batting_df['player_name'].unique())
                
                if not processor.bowling_df.empty and 'player_name' in processor.bowling_df.columns:
                    player_names.update(processor.bowling_df['player_name'].unique())
                
                # Track updates
                players_updated = 0
                players_not_found = 0
                
                for player_name in player_names:
                    # Get player profile with advanced metrics
                    profile = processor.player_profile(player_name)
                    
                    # Try to find player in database
                    try:
                        player = Player.objects.get(name__iexact=player_name)
                        
                        # Update player statistics
                        player.batting_average = profile.get('average_runs_last_5', player.batting_average)
                        player.bowling_average = profile.get('average_wickets_last_5', player.bowling_average)
                        player.recent_form = profile.get('avg_fantasy_points', player.recent_form)
                        
                        # Add additional fields if they exist in the model
                        if hasattr(player, 'consistency_index'):
                            player.consistency_index = profile.get('batting_consistency_index', 0)
                            
                        if hasattr(player, 'matches_played'):
                            # Calculate total matches from the data
                            matches = 0
                            if not processor.batting_df.empty and 'player_name' in processor.batting_df.columns:
                                matches = len(processor.batting_df[processor.batting_df['player_name'] == player_name]['match_id'].unique())
                            player.matches_played = matches
                            
                        # Save the updated player
                        player.save()
                        players_updated += 1
                        self.stdout.write(f"Updated player: {player_name}")
                        
                    except Player.DoesNotExist:
                        players_not_found += 1
                        self.stdout.write(self.style.WARNING(f"Player not found in database: {player_name}"))
                        # Could automatically create players here if desired
                        
                self.stdout.write(self.style.SUCCESS(
                    f"Database update completed: {players_updated} players updated, {players_not_found} players not found"
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating database: {str(e)}"))
            raise CommandError(f"Database update failed: {str(e)}")
    
    def preview_database_updates(self, processor):
        """Preview database updates without saving (dry run)"""
        self.stdout.write("Previewing database updates (dry run)...")
        
        # Get unique player names from the processor
        player_names = set()
        
        if not processor.batting_df.empty and 'player_name' in processor.batting_df.columns:
            player_names.update(processor.batting_df['player_name'].unique())
        
        if not processor.bowling_df.empty and 'player_name' in processor.bowling_df.columns:
            player_names.update(processor.bowling_df['player_name'].unique())
        
        # Track potential updates
        players_found = 0
        players_not_found = 0
        
        for player_name in player_names:
            # Get player profile with advanced metrics
            profile = processor.player_profile(player_name)
            
            # Try to find player in database
            try:
                player = Player.objects.get(name__iexact=player_name)
                players_found += 1
                
                # Show what would change
                updates = []
                
                if player.batting_average != profile.get('average_runs_last_5'):
                    updates.append(f"Batting avg: {player.batting_average} → {profile.get('average_runs_last_5')}")
                
                if player.bowling_average != profile.get('average_wickets_last_5'):
                    updates.append(f"Bowling avg: {player.bowling_average} → {profile.get('average_wickets_last_5')}")
                
                if player.recent_form != profile.get('avg_fantasy_points'):
                    updates.append(f"Recent form: {player.recent_form} → {profile.get('avg_fantasy_points')}")
                
                # Display changes
                if updates:
                    self.stdout.write(f"Player: {player_name} ({player.role})")
                    for update in updates:
                        self.stdout.write(f"  {update}")
                else:
                    self.stdout.write(f"No changes needed for {player_name}")
                
            except Player.DoesNotExist:
                players_not_found += 1
                self.stdout.write(self.style.WARNING(f"Player would be created: {player_name}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"Dry run completed: {players_found} players would be updated, {players_not_found} players not found"
        ))
