"""
Test script for the player statistics update functionality.
This script allows quick testing of the stats update without running the Django server.
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set up Django environment
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dream11_backend.settings')
django.setup()

# Import Django models and relevant functions
from django.db import transaction
from predictor.models import Player, Team, Venue
from predictor.management.commands.update_stats import Command as UpdateStatsCommand

def create_dummy_data():
    """Create some dummy data for testing if no data exists."""
    # Check if we already have data
    if Team.objects.count() > 0 and Player.objects.count() > 0:
        print("Data already exists in the database. Skipping dummy data creation.")
        return
    
    print("Creating dummy data for testing...")
    
    with transaction.atomic():
        # Create teams
        csk = Team.objects.create(name="Chennai Super Kings", short_name="CSK")
        mi = Team.objects.create(name="Mumbai Indians", short_name="MI")
        
        # Create venue
        venue = Venue.objects.create(name="Wankhede Stadium", city="Mumbai", country="India")
        
        # Create players
        Player.objects.create(
            name="MS Dhoni",
            team=csk,
            role="WK",
            batting_average=25.0,
            bowling_average=0.0,
            recent_form=30.0
        )
        
        Player.objects.create(
            name="Ravindra Jadeja",
            team=csk,
            role="AR",
            batting_average=22.0,
            bowling_average=28.5,
            recent_form=20.0
        )
        
        Player.objects.create(
            name="Rohit Sharma",
            team=mi,
            role="BAT",
            batting_average=32.0,
            bowling_average=0.0,
            recent_form=28.0
        )
        
    print("Created dummy data successfully.")

def create_sample_match_data():
    """Create sample match data CSV files for testing."""
    data_dir = os.path.join(os.path.dirname(__file__), 'predictor', 'management', 'commands', 'cricket_data')
    
    # Create the directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Create sample batting data
    batting_data = {
        'match_id': ['12345']*4,
        'player_name': ['MS Dhoni', 'Ravindra Jadeja', 'Rohit Sharma', 'Jasprit Bumrah'],
        'player_id': ['1', '2', '3', '4'],
        'team': ['Chennai Super Kings', 'Chennai Super Kings', 'Mumbai Indians', 'Mumbai Indians'],
        'opposing_team': ['Mumbai Indians', 'Mumbai Indians', 'Chennai Super Kings', 'Chennai Super Kings'],
        'runs': [45, 32, 55, 2],
        'balls': [28, 22, 40, 4],
        'fours': [3, 2, 4, 0],
        'sixes': [3, 1, 3, 0],
        'strike_rate': [160.71, 145.45, 137.50, 50.0],
        'dismissal': ['c Sharma b Bumrah', 'b Bumrah', 'c Dhoni b Jadeja', 'not out'],
        'fantasy_points': [69, 42, 79, 2]
    }
    
    # Create sample bowling data
    bowling_data = {
        'match_id': ['12345']*3,
        'player_name': ['Ravindra Jadeja', 'Jasprit Bumrah', 'Hardik Pandya'],
        'player_id': ['2', '4', '5'],
        'team': ['Chennai Super Kings', 'Mumbai Indians', 'Mumbai Indians'],
        'opposing_team': ['Mumbai Indians', 'Chennai Super Kings', 'Chennai Super Kings'],
        'overs': [4.0, 4.0, 3.0],
        'maidens': [0, 1, 0],
        'runs': [28, 22, 35],
        'wickets': [2, 3, 1],
        'economy': [7.00, 5.50, 11.67],
        'dots': [12, 15, 8],
        'fours': [3, 1, 5],
        'sixes': [1, 0, 2],
        'fantasy_points': [50, 75, 25]
    }
    
    # Convert to DataFrames
    batting_df = pd.DataFrame(batting_data)
    bowling_df = pd.DataFrame(bowling_data)
    
    # Get current date for filename
    date_str = datetime.now().strftime('%Y%m%d')
    
    # Save to CSV
    batting_df.to_csv(os.path.join(data_dir, f'match_12345_batting_{date_str}.csv'), index=False)
    bowling_df.to_csv(os.path.join(data_dir, f'match_12345_bowling_{date_str}.csv'), index=False)
    
    print(f"Created sample match data in {data_dir}")
    return data_dir

def test_player_stats_update():
    """Test updating player statistics."""
    print("Testing player statistics update...")
    
    # Get player data before update
    players_before = {}
    for player in Player.objects.all():
        players_before[player.name] = {
            'batting_average': player.batting_average,
            'bowling_average': player.bowling_average,
            'recent_form': player.recent_form
        }
    
    print("\nPlayer stats before update:")
    for name, stats in players_before.items():
        print(f"{name}: {stats}")
    
    # Create sample match data
    create_sample_match_data()
    
    # Run the update command in dry-run mode first
    print("\nRunning stats update (dry run)...")
    update_command = UpdateStatsCommand()
    update_command.handle(dry_run=True, days=90)
    
    # Now run the actual update
    print("\nRunning actual stats update...")
    update_command.handle(dry_run=False, days=90)
    
    # Get player data after update
    players_after = {}
    for player in Player.objects.all():
        players_after[player.name] = {
            'batting_average': player.batting_average,
            'bowling_average': player.bowling_average,
            'recent_form': player.recent_form
        }
    
    print("\nPlayer stats after update:")
    for name, stats in players_after.items():
        print(f"{name}: {stats}")
        
    # Compare before and after
    print("\nChanges in player stats:")
    for name in players_before:
        if name in players_after:
            before = players_before[name]
            after = players_after[name]
            
            changes = {}
            for stat in before:
                if before[stat] != after[stat]:
                    changes[stat] = f"{before[stat]} → {after[stat]}"
            
            if changes:
                print(f"{name}: {changes}")

def main():
    """Main function to run all tests."""
    print("=" * 50)
    print("PLAYER STATISTICS UPDATE TEST")
    print("=" * 50)
    
    create_dummy_data()
    test_player_stats_update()
    
    print("\n" + "=" * 50)
    print("TEST COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    main()
