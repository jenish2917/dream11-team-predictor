"""
Player Statistics Update Management Command

This module provides a Django management command to update player statistics
based on data scraped from ESPNCricinfo.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
import os
import logging
import pandas as pd
from datetime import datetime, timedelta

from predictor.models import Player, Team

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_player_stats.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update player statistics based on scraped ESPNCricinfo data'
    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Run without updating the database')
        parser.add_argument('--days', type=int, default=90, help='Number of days to consider for recent form')
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        recent_days = options['days']
        
        if dry_run:
            self.stdout.write('Running in dry-run mode - no database changes will be made')
        
        # Get the data directory
        data_dir = self.get_data_dir()
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f'Data directory not found: {data_dir}'))
            return
        
        # Load scraped match data
        batting_df, bowling_df = self.load_match_data(data_dir)
        if batting_df.empty and bowling_df.empty:
            self.stdout.write(self.style.WARNING('No match data found. Nothing to update.'))
            return
        
        # Update player statistics
        updated_count = self.update_player_statistics(batting_df, bowling_df, recent_days, dry_run)
        
        self.stdout.write(self.style.SUCCESS(f'Updated statistics for {updated_count} players'))
    
    def get_data_dir(self):
        """Get the directory where scraped data is stored."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, 'cricket_data')
    
    def load_match_data(self, data_dir):
        """
        Load batting and bowling data from all scraped match files.
        
        Args:
            data_dir: Directory where data files are stored
            
        Returns:
            Tuple of (batting_df, bowling_df) with all match data
        """
        batting_files = []
        bowling_files = []
        
        # Find all match data files
        for filename in os.listdir(data_dir):
            if filename.startswith('match_') and '_batting_' in filename and filename.endswith('.csv'):
                batting_files.append(os.path.join(data_dir, filename))
            elif filename.startswith('match_') and '_bowling_' in filename and filename.endswith('.csv'):
                bowling_files.append(os.path.join(data_dir, filename))
        
        self.stdout.write(f'Found {len(batting_files)} batting files and {len(bowling_files)} bowling files')
        
        # Load and concatenate all batting data
        batting_dfs = []
        for file_path in batting_files:
            try:
                df = pd.read_csv(file_path)
                # Extract date from filename: match_12345_batting_20230515.csv
                date_str = os.path.basename(file_path).split('_')[-1].replace('.csv', '')
                df['match_date'] = datetime.strptime(date_str, '%Y%m%d')
                batting_dfs.append(df)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error loading batting data from {file_path}: {e}'))
        
        # Load and concatenate all bowling data
        bowling_dfs = []
        for file_path in bowling_files:
            try:
                df = pd.read_csv(file_path)
                # Extract date from filename: match_12345_bowling_20230515.csv
                date_str = os.path.basename(file_path).split('_')[-1].replace('.csv', '')
                df['match_date'] = datetime.strptime(date_str, '%Y%m%d')
                bowling_dfs.append(df)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error loading bowling data from {file_path}: {e}'))
        
        # Combine all data
        batting_df = pd.concat(batting_dfs) if batting_dfs else pd.DataFrame()
        bowling_df = pd.concat(bowling_dfs) if bowling_dfs else pd.DataFrame()
        
        self.stdout.write(f'Loaded {len(batting_df)} batting and {len(bowling_df)} bowling performances')
        return batting_df, bowling_df
    
    def calculate_player_stats(self, player_name, batting_df, bowling_df, recent_days=90):
        """
        Calculate statistics for a specific player.
        
        Args:
            player_name: Name of the player
            batting_df: DataFrame with batting performances
            bowling_df: DataFrame with bowling performances
            recent_days: Number of days to consider for recent form
            
        Returns:
            Dict with calculated statistics
        """
        stats = {
            'batting_average': 0.0,
            'bowling_average': 0.0,
            'recent_form': 0.0
        }
        
        # Filter data for this player
        player_batting = batting_df[batting_df['player_name'] == player_name]
        player_bowling = bowling_df[bowling_df['player_name'] == player_name]
        
        # Calculate batting statistics
        if not player_batting.empty:
            total_runs = player_batting['runs'].sum()
            total_innings = len(player_batting)
            stats['batting_average'] = round(total_runs / max(1, total_innings), 2)
            
            # Calculate recent form (batting)
            cutoff_date = datetime.now() - timedelta(days=recent_days)
            recent_batting = player_batting[player_batting['match_date'] >= cutoff_date]
            if not recent_batting.empty:
                recent_runs = recent_batting['runs'].sum()
                recent_innings = len(recent_batting)
                stats['recent_form'] = round(recent_runs / max(1, recent_innings), 2)
        
        # Calculate bowling statistics
        if not player_bowling.empty:
            total_wickets = player_bowling['wickets'].sum()
            total_runs = player_bowling['runs'].sum()
            if total_wickets > 0:
                stats['bowling_average'] = round(total_runs / max(1, total_wickets), 2)
            
            # Update recent form with bowling data if it's better than batting
            cutoff_date = datetime.now() - timedelta(days=recent_days)
            recent_bowling = player_bowling[player_bowling['match_date'] >= cutoff_date]
            if not recent_bowling.empty:
                recent_bowling_points = recent_bowling['fantasy_points'].mean()
                recent_batting_points = recent_batting['fantasy_points'].mean() if not recent_batting.empty else 0
                
                # Use the better of the two for recent form
                if recent_bowling_points > recent_batting_points:
                    stats['recent_form'] = round(recent_bowling_points / 10, 2)  # Scale down bowling points
        
        return stats
    
    def update_player_statistics(self, batting_df, bowling_df, recent_days=90, dry_run=False):
        """
        Update player statistics in the database.
        
        Args:
            batting_df: DataFrame with batting performances
            bowling_df: DataFrame with bowling performances
            recent_days: Number of days to consider for recent form
            dry_run: If True, don't actually update the database
            
        Returns:
            Number of players updated
        """
        # Get all players from database
        players = Player.objects.all()
        self.stdout.write(f'Found {len(players)} players in the database')
        
        # Update each player's statistics
        updated_count = 0
        with transaction.atomic():
            for player in players:
                # Find player in scraped data (check for exact and partial matches)
                exact_matches = batting_df[batting_df['player_name'] == player.name]
                
                if exact_matches.empty and not batting_df.empty:
                    # Try partial matching for players with multiple name variations
                    name_parts = player.name.split()
                    if len(name_parts) > 1:
                        # Try matching on first name + last name
                        first_name = name_parts[0]
                        last_name = name_parts[-1]
                        pattern = f".*{first_name}.*{last_name}.*"
                        partial_matches = batting_df[batting_df['player_name'].str.contains(pattern, regex=True)]
                        
                        if not partial_matches.empty:
                            # Use the most common name variation for this player
                            most_common_name = partial_matches['player_name'].mode()[0]
                            self.stdout.write(f'Found partial match for {player.name}: {most_common_name}')
                            
                            # Calculate stats with the matched name
                            stats = self.calculate_player_stats(most_common_name, batting_df, bowling_df, recent_days)
                            
                            if not dry_run:
                                player.batting_average = stats['batting_average'] or player.batting_average
                                player.bowling_average = stats['bowling_average'] or player.bowling_average
                                player.recent_form = stats['recent_form'] or player.recent_form
                                player.save()
                            
                            updated_count += 1
                            self.stdout.write(f'Updated {player.name} stats: {stats}')
                elif not exact_matches.empty:
                    # Calculate stats with the exact name match
                    stats = self.calculate_player_stats(player.name, batting_df, bowling_df, recent_days)
                    
                    if not dry_run:
                        player.batting_average = stats['batting_average'] or player.batting_average
                        player.bowling_average = stats['bowling_average'] or player.bowling_average
                        player.recent_form = stats['recent_form'] or player.recent_form
                        player.save()
                    
                    updated_count += 1
                    self.stdout.write(f'Updated {player.name} stats: {stats}')
        
        return updated_count
