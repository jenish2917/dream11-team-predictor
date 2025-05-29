"""
Test script for player statistics processing functionality.
This script tests the enhanced statistics and player profile generation.
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set up local environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dream11_backend.settings')

# Test the player stats processor
def test_player_stats_processor():
    print("=" * 60)
    print("TESTING PLAYER STATISTICS PROCESSOR")
    print("=" * 60)
    
    # Import the processor
    try:
        from predictor.management.commands.process_player_stats import PlayerStatsProcessor
        print("✅ Successfully imported PlayerStatsProcessor")
    except ImportError as e:
        print(f"❌ Failed to import PlayerStatsProcessor: {str(e)}")
        return False
    
    # Create sample data for testing
    data_dir = create_sample_data()
    if not data_dir:
        print("❌ Failed to create sample data")
        return False
    
    print(f"✅ Created sample data in {data_dir}")
    
    # Initialize processor
    processor = PlayerStatsProcessor(data_dir)
    
    # Test data loading
    success = processor.load_data()
    if not success:
        print("❌ Failed to load data")
        return False
    
    print(f"✅ Loaded data: {len(processor.batting_df)} batting records, {len(processor.bowling_df)} bowling records")
    
    # Test data cleaning
    success = processor.clean_data()
    if not success:
        print("❌ Failed to clean data")
        return False
        
    print("✅ Data cleaning successful")
    
    # Test player profile generation
    if not processor.batting_df.empty and 'player_name' in processor.batting_df.columns:
        sample_player = processor.batting_df['player_name'].iloc[0]
        print(f"\nGenerating profile for {sample_player}:")
        
        profile = processor.player_profile(sample_player)
        print(f"  Role: {profile.get('role', 'Unknown')}")
        print(f"  Avg runs (last 5): {profile.get('average_runs_last_5', 0)}")
        print(f"  Consistency index: {profile.get('batting_consistency_index', 0)}")
        
        # Test performance metrics
        print(f"\nPerformance vs opposition:")
        for team, stats in profile.get('performance_vs_opposition', {}).items():
            print(f"  {team}: {stats.get('avg_runs', 0)} runs in {stats.get('matches', 0)} matches")
        
        # Test venue stats
        print(f"\nPerformance by venue:")
        for venue, stats in profile.get('venue_stats', {}).items():
            print(f"  {venue}: {stats.get('avg_runs', 0)} runs in {stats.get('matches', 0)} matches")
        
        # Test plot generation
        print("\nGenerating performance plots:")
        form_plot = processor.plot_recent_form(sample_player)
        if form_plot:
            print(f"✅ Form plot generated: {form_plot}")
        else:
            print("❌ Failed to generate form plot")
        
        opposition_plot = processor.plot_opposition_performance(sample_player)
        if opposition_plot:
            print(f"✅ Opposition plot generated: {opposition_plot}")
        else:
            print("❌ Failed to generate opposition plot")
        
        # Test profile export
        json_file = processor.export_player_profiles('json')
        if json_file:
            print(f"✅ Exported profiles to JSON: {json_file}")
        else:
            print("❌ Failed to export profiles to JSON")
        
        csv_file = processor.export_player_profiles('csv')
        if csv_file:
            print(f"✅ Exported profiles to CSV: {csv_file}")
        else:
            print("❌ Failed to export profiles to CSV")
    else:
        print("❌ No player data available for testing")
        return False
    
    print("\n" + "=" * 60)
    print("PLAYER STATISTICS PROCESSOR TEST COMPLETE")
    print("=" * 60)
    return True

def create_sample_data():
    """Create sample cricket data for testing."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_cricket_data')
    
    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Sample batting data
    batting_data = {
        'match_id': ['12345']*4 + ['12346']*4 + ['12347']*4,
        'player_name': ['Virat Kohli', 'MS Dhoni', 'Rohit Sharma', 'Jasprit Bumrah'] * 3,
        'player_id': ['1', '2', '3', '4'] * 3,
        'team': ['Royal Challengers Bangalore', 'Chennai Super Kings', 'Mumbai Indians', 'Mumbai Indians'] * 3,
        'opposing_team': ['Chennai Super Kings', 'Royal Challengers Bangalore', 'Chennai Super Kings', 'Royal Challengers Bangalore'] * 3,
        'runs': [75, 42, 65, 2, 85, 35, 45, 0, 55, 60, 30, 5],
        'balls': [50, 30, 40, 6, 55, 25, 30, 0, 40, 45, 20, 4],
        'fours': [8, 3, 6, 0, 10, 2, 4, 0, 6, 7, 2, 1],
        'sixes': [3, 2, 4, 0, 4, 1, 2, 0, 2, 3, 1, 0],
        'strike_rate': [150.0, 140.0, 162.5, 33.3, 154.5, 140.0, 150.0, 0.0, 137.5, 133.3, 150.0, 125.0],
        'dismissal': ['c Dhoni b Jadeja', 'b Siraj', 'run out', 'not out', 'c Jadeja b Bravo', 'b Bumrah', 'c Kohli b Siraj', 'not out', 'lbw b Jadeja', 'c Sharma b Bumrah', 'b Jadeja', 'not out'],
        'fantasy_points': [95, 65, 85, 10, 110, 55, 65, 5, 75, 80, 45, 15],
        'role': ['BAT', 'WK', 'BAT', 'BWL'] * 3,
        'match_date': ['2024-05-10', '2024-05-10', '2024-05-10', '2024-05-10', '2024-05-15', '2024-05-15', '2024-05-15', '2024-05-15', '2024-05-20', '2024-05-20', '2024-05-20', '2024-05-20'],
        'venue': ['Wankhede Stadium', 'Wankhede Stadium', 'Wankhede Stadium', 'Wankhede Stadium', 'M. Chinnaswamy Stadium', 'M. Chinnaswamy Stadium', 'M. Chinnaswamy Stadium', 'M. Chinnaswamy Stadium', 'MA Chidambaram Stadium', 'MA Chidambaram Stadium', 'MA Chidambaram Stadium', 'MA Chidambaram Stadium']
    }
    
    # Sample bowling data
    bowling_data = {
        'match_id': ['12345']*3 + ['12346']*3 + ['12347']*3,
        'player_name': ['Jasprit Bumrah', 'Ravindra Jadeja', 'Yuzvendra Chahal'] * 3,
        'player_id': ['4', '5', '6'] * 3,
        'team': ['Mumbai Indians', 'Chennai Super Kings', 'Royal Challengers Bangalore'] * 3,
        'opposing_team': ['Royal Challengers Bangalore', 'Mumbai Indians', 'Chennai Super Kings'] * 3,
        'overs': [4.0, 4.0, 4.0, 3.5, 4.0, 4.0, 4.0, 4.0, 3.2],
        'maidens': [0, 0, 1, 0, 1, 0, 0, 0, 0],
        'runs': [32, 28, 25, 40, 22, 35, 30, 25, 38],
        'wickets': [3, 2, 2, 1, 3, 1, 2, 3, 0],
        'economy': [8.00, 7.00, 6.25, 10.43, 5.50, 8.75, 7.50, 6.25, 11.88],
        'dots': [12, 14, 10, 8, 16, 9, 10, 12, 6],
        'fours': [4, 3, 2, 5, 1, 4, 3, 2, 4],
        'sixes': [1, 0, 1, 2, 0, 2, 1, 0, 2],
        'fantasy_points': [75, 50, 50, 30, 80, 30, 55, 70, 10],
        'role': ['BWL', 'AR', 'BWL'] * 3,
        'match_date': ['2024-05-10', '2024-05-10', '2024-05-10', '2024-05-15', '2024-05-15', '2024-05-15', '2024-05-20', '2024-05-20', '2024-05-20'],
        'venue': ['Wankhede Stadium', 'Wankhede Stadium', 'Wankhede Stadium', 'M. Chinnaswamy Stadium', 'M. Chinnaswamy Stadium', 'M. Chinnaswamy Stadium', 'MA Chidambaram Stadium', 'MA Chidambaram Stadium', 'MA Chidambaram Stadium']
    }
    
    # Convert to DataFrames
    batting_df = pd.DataFrame(batting_data)
    bowling_df = pd.DataFrame(bowling_data)
    
    # Save to CSV
    try:
        batting_df.to_csv(os.path.join(data_dir, 'batting_data_test.csv'), index=False)
        bowling_df.to_csv(os.path.join(data_dir, 'bowling_data_test.csv'), index=False)
        return data_dir
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")
        return None

# Test the Django management command
def test_management_command():
    print("\n" + "=" * 60)
    print("TESTING ENHANCE PLAYER STATS MANAGEMENT COMMAND")
    print("=" * 60)
    
    try:
        import django
        django.setup()
        
        from django.core.management import call_command
        print("✅ Successfully imported Django management")
        
        # Create sample data
        data_dir = create_sample_data()
        if not data_dir:
            print("❌ Failed to create sample data")
            return False
            
        # Call management command in dry-run mode
        print("\nRunning management command (dry run):")
        call_command('enhance_player_stats', data_dir=data_dir, dry_run=True, plots=True)
        
        print("\n✅ Successfully executed management command")
        return True
    
    except ImportError as e:
        print(f"❌ Failed to import Django: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error in management command test: {str(e)}")
        return False

def test_ml_integration():
    """Test the integration with the ML prediction module."""
    print("\n" + "=" * 60)
    print("TESTING ML PREDICTION INTEGRATION")
    print("=" * 60)
    
    try:
        # Test importing the ML module
        from predictor.player_performance_predictor import PlayerPerformancePredictor
        print("✅ Successfully imported PlayerPerformancePredictor")
        
        # Test importing our Django management command
        try:
            from predictor.management.commands.predict_player_performance import Command
            print("✅ Successfully imported predict_player_performance command")
        except ImportError as e:
            print(f"❌ Failed to import predict_player_performance command: {str(e)}")
        
        print("\n✅ ML integration check complete")
        return True
    
    except ImportError as e:
        print(f"❌ Failed to import ML module: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error in ML integration test: {str(e)}")
        return False

if __name__ == "__main__":
    # Test processor directly
    test_result = test_player_stats_processor()
    
    # Test management command if processor test passed
    if test_result:
        test_management_command()
        
    # Test ML integration
    test_ml_integration()
