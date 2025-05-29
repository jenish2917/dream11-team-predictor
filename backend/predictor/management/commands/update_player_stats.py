#!/usr/bin/env python
"""
Player Statistics Updater

This script updates player statistics in the Dream11 Team Predictor database
based on data scraped from ESPNCricinfo. It calculates recent form and 
updates batting/bowling averages.

Usage:
    python update_player_stats.py [--dry-run]
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("player_stats_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Set up Django environment
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dream11_backend.settings')
django.setup()

# Import Django models
from django.db import transaction
from predictor.models import Player, Team

def get_scraped_data_dir():
    """Get the directory where scraped data is stored."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'cricket_data')

def load_match_data(data_dir):
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
            logger.error(f"Error loading batting data from {file_path}: {e}")
    
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
            logger.error(f"Error loading bowling data from {file_path}: {e}")
    
    # Combine all data
    batting_df = pd.concat(batting_dfs) if batting_dfs else pd.DataFrame()
    bowling_df = pd.concat(bowling_dfs) if bowling_dfs else pd.DataFrame()
    
    logger.info(f"Loaded {len(batting_df)} batting and {len(bowling_df)} bowling performances")
    return batting_df, bowling_df

def calculate_player_stats(player_name, batting_df, bowling_df, recent_days=90):
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

def update_player_statistics(dry_run=False):
    """
    Update player statistics in the database.
    
    Args:
        dry_run: If True, don't actually update the database
        
    Returns:
        Number of players updated
    """
    data_dir = get_scraped_data_dir()
    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return 0
    
    # Load scraped match data
    batting_df, bowling_df = load_match_data(data_dir)
    if batting_df.empty and bowling_df.empty:
        logger.warning("No match data found. Nothing to update.")
        return 0
    
    # Get all players from database
    players = Player.objects.all()
    logger.info(f"Found {len(players)} players in the database")
    
    # Update each player's statistics
    updated_count = 0
    with transaction.atomic():
        for player in players:
            # Find player in scraped data (check for exact and partial matches)
            exact_matches = batting_df[batting_df['player_name'] == player.name]
            
            if exact_matches.empty:
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
                        logger.info(f"Found partial match for {player.name}: {most_common_name}")
                        
                        # Calculate stats with the matched name
                        stats = calculate_player_stats(most_common_name, batting_df, bowling_df)
                        
                        if not dry_run:
                            player.batting_average = stats['batting_average'] or player.batting_average
                            player.bowling_average = stats['bowling_average'] or player.bowling_average
                            player.recent_form = stats['recent_form'] or player.recent_form
                            player.save()
                        
                        updated_count += 1
                        logger.info(f"Updated {player.name} stats: {stats}")
            else:
                # Calculate stats with the exact name match
                stats = calculate_player_stats(player.name, batting_df, bowling_df)
                
                if not dry_run:
                    player.batting_average = stats['batting_average'] or player.batting_average
                    player.bowling_average = stats['bowling_average'] or player.bowling_average
                    player.recent_form = stats['recent_form'] or player.recent_form
                    player.save()
                
                updated_count += 1
                logger.info(f"Updated {player.name} stats: {stats}")
    
    logger.info(f"Updated statistics for {updated_count} players")
    return updated_count

def main():
    parser = argparse.ArgumentParser(description='Update player statistics from scraped data')
    parser.add_argument('--dry-run', action='store_true', help='Run without updating the database')
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("Running in dry-run mode - no database changes will be made")
    
    count = update_player_statistics(args.dry_run)
    print(f"Updated statistics for {count} players")

if __name__ == "__main__":
    main()
