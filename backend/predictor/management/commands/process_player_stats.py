"""
Player Statistics Processor for Dream11 Team Predictor

This module processes raw cricket data from scraper and generates:
1. Cleaned player statistics
2. Feature engineering for prediction
3. Player profile generation
4. Performance visualization
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class PlayerStatsProcessor:
    """
    Process player statistics from raw data.
    Handles data cleaning, feature engineering, and profile generation.
    """
    
    def __init__(self, data_dir=None):
        """
        Initialize the processor with data directory.
        
        Args:
            data_dir: Directory to save/load player data and plots
        """
        self.data_dir = data_dir if data_dir else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cricket_data')
        self.plots_dir = os.path.join(self.data_dir, 'plots')
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.plots_dir, exist_ok=True)
        
        # Initialize dataframes
        self.batting_df = pd.DataFrame()
        self.bowling_df = pd.DataFrame()
        self.players_df = pd.DataFrame()
        
    def load_data(self, batting_file=None, bowling_file=None):
        """
        Load batting and bowling data from CSV files.
        
        Args:
            batting_file: Path to batting CSV file
            bowling_file: Path to bowling CSV file
            
        Returns:
            Boolean indicating success
        """
        try:
            # If specific files are provided, load them
            if batting_file and os.path.exists(batting_file):
                self.batting_df = pd.read_csv(batting_file)
                logging.info(f"Loaded batting data from {batting_file}: {len(self.batting_df)} records")
            
            if bowling_file and os.path.exists(bowling_file):
                self.bowling_df = pd.read_csv(bowling_file)
                logging.info(f"Loaded bowling data from {bowling_file}: {len(self.bowling_df)} records")
            
            # If no specific files, try to load all data from directory
            if not batting_file and not bowling_file:
                # Find all batting and bowling files
                batting_files = [os.path.join(self.data_dir, f) for f in os.listdir(self.data_dir) 
                               if f.endswith('.csv') and 'batting' in f]
                bowling_files = [os.path.join(self.data_dir, f) for f in os.listdir(self.data_dir) 
                                if f.endswith('.csv') and 'bowling' in f]
                
                # Load and concatenate all batting data
                batting_dfs = []
                for file in batting_files:
                    try:
                        df = pd.read_csv(file)
                        batting_dfs.append(df)
                    except Exception as e:
                        logging.error(f"Error loading {file}: {str(e)}")
                
                if batting_dfs:
                    self.batting_df = pd.concat(batting_dfs, ignore_index=True)
                    logging.info(f"Loaded {len(batting_dfs)} batting files: {len(self.batting_df)} total records")
                
                # Load and concatenate all bowling data
                bowling_dfs = []
                for file in bowling_files:
                    try:
                        df = pd.read_csv(file)
                        bowling_dfs.append(df)
                    except Exception as e:
                        logging.error(f"Error loading {file}: {str(e)}")
                
                if bowling_dfs:
                    self.bowling_df = pd.concat(bowling_dfs, ignore_index=True)
                    logging.info(f"Loaded {len(bowling_dfs)} bowling files: {len(self.bowling_df)} total records")
            
            return not (self.batting_df.empty and self.bowling_df.empty)
            
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            return False
    
    def clean_data(self):
        """
        Clean and prepare the data for analysis.
        
        Returns:
            Boolean indicating success
        """
        if self.batting_df.empty and self.bowling_df.empty:
            logging.error("No data to clean. Load data first.")
            return False
        
        try:
            # Clean batting data
            if not self.batting_df.empty:
                # Clean column names
                self.batting_df.columns = self.batting_df.columns.str.strip().str.lower()
                
                # Add match_date column if not present
                if 'match_date' not in self.batting_df.columns:
                    # Try to extract date from match_id or filename
                    if 'match_id' in self.batting_df.columns:
                        # Default to today if no date available
                        self.batting_df['match_date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Convert match_date to datetime
                if 'match_date' in self.batting_df.columns:
                    self.batting_df['match_date'] = pd.to_datetime(self.batting_df['match_date'], errors='coerce')
                
                # Convert numeric columns
                numeric_cols = ['runs', 'balls', 'fours', 'sixes', 'strike_rate']
                for col in numeric_cols:
                    if col in self.batting_df.columns:
                        self.batting_df[col] = pd.to_numeric(self.batting_df[col], errors='coerce').fillna(0)
                
                # Handle missing values
                self.batting_df.fillna(0, inplace=True)
            
            # Clean bowling data
            if not self.bowling_df.empty:
                # Clean column names
                self.bowling_df.columns = self.bowling_df.columns.str.strip().str.lower()
                
                # Add match_date column if not present
                if 'match_date' not in self.bowling_df.columns:
                    # Try to extract date from match_id or filename
                    if 'match_id' in self.bowling_df.columns:
                        # Default to today if no date available
                        self.bowling_df['match_date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Convert match_date to datetime
                if 'match_date' in self.bowling_df.columns:
                    self.bowling_df['match_date'] = pd.to_datetime(self.bowling_df['match_date'], errors='coerce')
                
                # Convert numeric columns
                numeric_cols = ['overs', 'maidens', 'runs', 'wickets', 'economy', 'dots']
                for col in numeric_cols:
                    if col in self.bowling_df.columns:
                        self.bowling_df[col] = pd.to_numeric(self.bowling_df[col], errors='coerce').fillna(0)
                
                # Handle missing values
                self.bowling_df.fillna(0, inplace=True)
            
            # Sort by date
            if not self.batting_df.empty and 'match_date' in self.batting_df.columns:
                self.batting_df.sort_values(by='match_date', ascending=False, inplace=True)
                
            if not self.bowling_df.empty and 'match_date' in self.bowling_df.columns:
                self.bowling_df.sort_values(by='match_date', ascending=False, inplace=True)
            
            logging.info("Data cleaning completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error cleaning data: {str(e)}")
            return False
    
    def compute_recent_form(self, player_name, matches=5):
        """
        Compute a player's recent form based on last N matches.
        
        Args:
            player_name: Name of the player
            matches: Number of recent matches to consider (default: 5)
            
        Returns:
            Tuple of (avg_runs, avg_wickets)
        """
        avg_runs, avg_wickets = 0, 0
        
        # Get batting data
        if not self.batting_df.empty and 'player_name' in self.batting_df.columns:
            player_data = self.batting_df[self.batting_df['player_name'] == player_name].head(matches)
            if not player_data.empty and 'runs' in player_data.columns:
                avg_runs = player_data['runs'].mean()
        
        # Get bowling data
        if not self.bowling_df.empty and 'player_name' in self.bowling_df.columns:
            player_data = self.bowling_df[self.bowling_df['player_name'] == player_name].head(matches)
            if not player_data.empty and 'wickets' in player_data.columns:
                avg_wickets = player_data['wickets'].mean()
        
        return round(avg_runs, 2), round(avg_wickets, 2)
    
    def consistency_index(self, player_name, stat_type='batting'):
        """
        Calculate consistency index for a player.
        Higher values indicate more consistent performance.
        
        Args:
            player_name: Name of the player
            stat_type: 'batting' or 'bowling'
            
        Returns:
            Consistency index (float)
        """
        if stat_type == 'batting':
            if self.batting_df.empty or 'player_name' not in self.batting_df.columns:
                return 0
            
            scores = self.batting_df[self.batting_df['player_name'] == player_name]['runs']
            if len(scores) == 0:
                return 0
            
            # Higher mean / lower std deviation = more consistent
            return round((scores.mean() / (scores.std() + 1)) * 10, 2)
            
        elif stat_type == 'bowling':
            if self.bowling_df.empty or 'player_name' not in self.bowling_df.columns:
                return 0
            
            wickets = self.bowling_df[self.bowling_df['player_name'] == player_name]['wickets']
            if len(wickets) == 0:
                return 0
            
            # Higher mean / lower std deviation = more consistent
            return round((wickets.mean() / (wickets.std() + 1)) * 10, 2)
            
        return 0
    
    def player_profile(self, player_name):
        """
        Generate a comprehensive player profile with performance metrics.
        
        Args:
            player_name: Name of the player
            
        Returns:
            Dictionary with player profile data
        """
        profile = {
            "name": player_name,
            "role": "Unknown",
            "team": "Unknown"
        }
        
        # Get player role and team
        if not self.batting_df.empty and 'player_name' in self.batting_df.columns:
            player_row = self.batting_df[self.batting_df['player_name'] == player_name]
            if not player_row.empty:
                if 'role' in player_row.columns:
                    profile["role"] = player_row['role'].iloc[0]
                if 'team' in player_row.columns:
                    profile["team"] = player_row['team'].iloc[0]
        
        # Recent performance
        avg_runs, avg_wickets = self.compute_recent_form(player_name)
        profile["average_runs_last_5"] = avg_runs
        profile["average_wickets_last_5"] = avg_wickets
        
        # Consistency
        profile["batting_consistency_index"] = self.consistency_index(player_name, 'batting')
        profile["bowling_consistency_index"] = self.consistency_index(player_name, 'bowling')
        
        # Performance vs opposition
        opposition_stats = {}
        if not self.batting_df.empty and 'player_name' in self.batting_df.columns:
            player_matches = self.batting_df[self.batting_df['player_name'] == player_name]
            if not player_matches.empty and 'opposing_team' in player_matches.columns:
                # Group by opposition
                opposition_data = player_matches.groupby('opposing_team').agg(
                    matches=pd.NamedAgg(column='match_id', aggfunc='nunique'),
                    avg_runs=pd.NamedAgg(column='runs', aggfunc='mean')
                ).reset_index()
                
                for _, row in opposition_data.iterrows():
                    opposition_stats[row['opposing_team']] = {
                        "matches": int(row['matches']),
                        "avg_runs": round(row['avg_runs'], 2)
                    }
        
        profile["performance_vs_opposition"] = opposition_stats
        
        # Venue stats
        venue_stats = {}
        if not self.batting_df.empty and 'player_name' in self.batting_df.columns:
            player_matches = self.batting_df[self.batting_df['player_name'] == player_name]
            if not player_matches.empty and 'venue' in player_matches.columns:
                # Group by venue
                venue_data = player_matches.groupby('venue').agg(
                    matches=pd.NamedAgg(column='match_id', aggfunc='nunique'),
                    avg_runs=pd.NamedAgg(column='runs', aggfunc='mean')
                ).reset_index()
                
                for _, row in venue_data.iterrows():
                    venue_stats[row['venue']] = {
                        "matches": int(row['matches']),
                        "avg_runs": round(row['avg_runs'], 2)
                    }
        
        profile["venue_stats"] = venue_stats
        
        # Fantasy points
        fantasy_points = 0
        if not self.batting_df.empty and 'player_name' in self.batting_df.columns:
            player_batting = self.batting_df[self.batting_df['player_name'] == player_name]
            if not player_batting.empty and 'fantasy_points' in player_batting.columns:
                batting_points = player_batting['fantasy_points'].mean()
                fantasy_points += batting_points
        
        if not self.bowling_df.empty and 'player_name' in self.bowling_df.columns:
            player_bowling = self.bowling_df[self.bowling_df['player_name'] == player_name]
            if not player_bowling.empty and 'fantasy_points' in player_bowling.columns:
                bowling_points = player_bowling['fantasy_points'].mean()
                fantasy_points += bowling_points
        
        profile["avg_fantasy_points"] = round(fantasy_points, 2)
        
        return profile
    
    def plot_recent_form(self, player_name, matches=5):
        """
        Generate a plot of player's recent performance.
        
        Args:
            player_name: Name of the player
            matches: Number of recent matches to plot (default: 5)
            
        Returns:
            Path to the saved plot or None if failed
        """
        try:
            if self.batting_df.empty or 'player_name' not in self.batting_df.columns:
                logging.error("No batting data available for plotting")
                return None
            
            player_data = self.batting_df[self.batting_df['player_name'] == player_name].head(matches)
            if player_data.empty:
                logging.error(f"No data found for player {player_name}")
                return None
            
            plt.figure(figsize=(10, 6))
            sns.set_style("whitegrid")
            
            # Plot runs
            if 'match_date' in player_data.columns and 'runs' in player_data.columns:
                ax = sns.lineplot(x='match_date', y='runs', data=player_data, marker='o', 
                                 color='royalblue', linewidth=2.5)
                ax.set_title(f"{player_name} - Recent Performance (Last {matches} Matches)", fontsize=16)
                ax.set_ylabel("Runs Scored", fontsize=14)
                ax.set_xlabel("Match Date", fontsize=14)
            
                # Format dates on x-axis
                plt.xticks(rotation=45)
                plt.tight_layout()
            
                # Generate filename
                safe_name = player_name.replace(" ", "_").lower()
                filename = f"{safe_name}_recent_form.png"
                filepath = os.path.join(self.plots_dir, filename)
            
                # Save the plot
                plt.savefig(filepath, dpi=100, bbox_inches='tight')
                plt.close()
            
                logging.info(f"Saved performance plot to {filepath}")
                return filepath
            else:
                logging.error("Required columns not found in player data")
                return None
        
        except Exception as e:
            logging.error(f"Error generating plot: {str(e)}")
            plt.close()
            return None
    
    def plot_opposition_performance(self, player_name):
        """
        Generate a bar plot of player's performance against different teams.
        
        Args:
            player_name: Name of the player
            
        Returns:
            Path to the saved plot or None if failed
        """
        try:
            if self.batting_df.empty or 'player_name' not in self.batting_df.columns:
                logging.error("No batting data available for plotting")
                return None
            
            player_data = self.batting_df[self.batting_df['player_name'] == player_name]
            if player_data.empty or 'opposing_team' not in player_data.columns:
                logging.error(f"No opposition data found for player {player_name}")
                return None
            
            # Group by opposition
            opposition_data = player_data.groupby('opposing_team').agg(
                avg_runs=pd.NamedAgg(column='runs', aggfunc='mean')
            ).reset_index()
            
            if opposition_data.empty:
                logging.error(f"No opposition data to plot for player {player_name}")
                return None
            
            plt.figure(figsize=(12, 7))
            sns.set_style("whitegrid")
            
            # Sort by average runs
            opposition_data = opposition_data.sort_values('avg_runs', ascending=False)
            
            # Plot bar chart
            ax = sns.barplot(x='opposing_team', y='avg_runs', data=opposition_data, 
                           palette='viridis')
            
            ax.set_title(f"{player_name} - Average Runs vs Opposition", fontsize=16)
            ax.set_ylabel("Average Runs", fontsize=14)
            ax.set_xlabel("Opposition Team", fontsize=14)
            
            # Add value labels
            for p in ax.patches:
                ax.annotate(f'{p.get_height():.1f}', 
                           (p.get_x() + p.get_width() / 2., p.get_height()), 
                           ha='center', va='bottom', fontsize=10, color='black')
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Generate filename
            safe_name = player_name.replace(" ", "_").lower()
            filename = f"{safe_name}_opposition_performance.png"
            filepath = os.path.join(self.plots_dir, filename)
            
            # Save the plot
            plt.savefig(filepath, dpi=100, bbox_inches='tight')
            plt.close()
            
            logging.info(f"Saved opposition performance plot to {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"Error generating opposition plot: {str(e)}")
            plt.close()
            return None
    
    def export_player_profiles(self, output_format='json'):
        """
        Export all player profiles to a file.
        
        Args:
            output_format: 'json' or 'csv'
            
        Returns:
            Path to the output file
        """
        try:
            if self.batting_df.empty and self.bowling_df.empty:
                logging.error("No data available to generate profiles")
                return None
            
            # Get unique player names
            player_names = set()
            
            if not self.batting_df.empty and 'player_name' in self.batting_df.columns:
                player_names.update(self.batting_df['player_name'].unique())
            
            if not self.bowling_df.empty and 'player_name' in self.bowling_df.columns:
                player_names.update(self.bowling_df['player_name'].unique())
            
            player_profiles = []
            for player in player_names:
                profile = self.player_profile(player)
                player_profiles.append(profile)
            
            # Generate output filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if output_format.lower() == 'json':
                filename = f"player_profiles_{timestamp}.json"
                filepath = os.path.join(self.data_dir, filename)
                
                with open(filepath, 'w') as f:
                    json.dump(player_profiles, f, indent=2)
                
            elif output_format.lower() == 'csv':
                filename = f"player_profiles_{timestamp}.csv"
                filepath = os.path.join(self.data_dir, filename)
                
                # Convert to flat DataFrame
                profiles_df = pd.DataFrame()
                
                for profile in player_profiles:
                    # Extract basic stats
                    flat_profile = {
                        'name': profile['name'],
                        'role': profile['role'],
                        'team': profile['team'],
                        'average_runs_last_5': profile['average_runs_last_5'],
                        'average_wickets_last_5': profile['average_wickets_last_5'],
                        'batting_consistency_index': profile['batting_consistency_index'],
                        'bowling_consistency_index': profile['bowling_consistency_index'],
                        'avg_fantasy_points': profile['avg_fantasy_points']
                    }
                    
                    profiles_df = pd.concat([profiles_df, pd.DataFrame([flat_profile])], ignore_index=True)
                
                profiles_df.to_csv(filepath, index=False)
            
            else:
                logging.error(f"Unsupported output format: {output_format}")
                return None
            
            logging.info(f"Exported {len(player_profiles)} player profiles to {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"Error exporting player profiles: {str(e)}")
            return None


# Function to demonstrate the use of PlayerStatsProcessor
def process_player_stats(data_dir=None):
    """
    Process player statistics and generate profiles.
    
    Args:
        data_dir: Directory containing cricket data files
        
    Returns:
        Boolean indicating success
    """
    try:
        # Initialize processor
        processor = PlayerStatsProcessor(data_dir)
        
        # Load data
        success = processor.load_data()
        if not success:
            logging.error("Failed to load data")
            return False
        
        # Clean data
        success = processor.clean_data()
        if not success:
            logging.error("Failed to clean data")
            return False
        
        # Generate example player profile
        sample_player = None
        if not processor.batting_df.empty and 'player_name' in processor.batting_df.columns:
            sample_player = processor.batting_df['player_name'].iloc[0]
        
        if sample_player:
            # Generate and display profile
            profile = processor.player_profile(sample_player)
            logging.info(f"Sample player profile for {sample_player}:")
            logging.info(json.dumps(profile, indent=2))
            
            # Generate plots
            processor.plot_recent_form(sample_player)
            processor.plot_opposition_performance(sample_player)
        
        # Export all player profiles
        processor.export_player_profiles('json')
        processor.export_player_profiles('csv')
        
        return True
        
    except Exception as e:
        logging.error(f"Error in process_player_stats: {str(e)}")
        return False


if __name__ == "__main__":
    # Example usage
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cricket_data')
    process_player_stats(data_dir)
