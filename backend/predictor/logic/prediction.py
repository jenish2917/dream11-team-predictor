"""
Dream11 Team Predictor - Core Prediction Logic

This module contains the main prediction algorithm for Dream11 teams.
It can work in standalone mode or as part of the Django application.
"""
import os
import logging
import csv
import random
import sys
import time
import json
from pathlib import Path
import functools

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Try to use pandas and numpy, but provide fallbacks if not available
try:
    import pandas as pd
    import numpy as np
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False
    logging.warning("pandas and/or numpy not available. Using CSV reader fallback.")

# Cache decorator for expensive operations
def cached_result(expires_after=3600):  # Default cache expiry: 1 hour
    """
    Cache decorator for expensive operations
    
    Args:
        expires_after: Cache expiry time in seconds
    """
    def decorator(func):
        # Cache for storing results
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function arguments
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # Check if result is in cache and not expired
            if key in cache and (current_time - cache[key]['timestamp']) < expires_after:
                logging.debug(f"Using cached result for {func.__name__}")
                return cache[key]['result']
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[key] = {
                'result': result,
                'timestamp': current_time
            }
            return result
            
        # Add function to clear the cache
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
        
    return decorator

class Dream11TeamPredictor:
    """
    Class to predict the best Dream11 team for a given match
    """
    
    def __init__(self, data_folder_path=None):
        """
        Initialize the predictor with the path to the data folder
        
        Args:
            data_folder_path: Path to the folder containing IPL data files
                              If None, will look in default locations
        """
        if data_folder_path is None:
            # Try multiple locations to find the data
            this_dir = os.path.dirname(os.path.abspath(__file__))
            possible_paths = [
                Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(this_dir)))), 'IPL-DATASET')),
                Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(this_dir)))), 'data', 'IPL-DATASET')),
                Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(this_dir))), 'data', 'IPL-DATASET'))
            ]
            
            for path in possible_paths:
                if path.exists():
                    self.data_folder_path = path
                    break
            else:
                raise FileNotFoundError(f"Could not find IPL-DATASET folder in any of the expected locations: {possible_paths}")
        else:
            self.data_folder_path = Path(data_folder_path)
        
        logging.info(f"Using data folder: {self.data_folder_path}")
        
        # Data frames/dicts
        self.teams = {}
        self.batting_data = None
        self.bowling_data = None
        self.auction_data = None
        self.match_results = None
        self.catches_data = None
        self.dismissals_data = None
        
        # Stats dictionaries (initialized for CSV fallback)
        self.batting_stats = {}
        self.bowling_stats = {}
        
        # Load all data
        self._load_all_data()
    
    def _load_all_data(self):
        """
        Load all available data from the data folder
        """
        if HAS_DEPENDENCIES:
            self._load_data_pandas()
        else:
            self._load_data_csv()
    
    def _load_data_pandas(self):
        """
        Load data using pandas
        """
        try:            # Load batting data
            batting_path = self.data_folder_path / 'ipl data - most_runs.csv'
            if batting_path.exists():
                self.batting_data = pd.read_csv(batting_path)
                logging.info(f"Loaded batting data: {len(self.batting_data)} records")
                self._process_batting_data_pandas()
            
            # Load bowling data
            bowling_path = self.data_folder_path / 'ipl data - most_wickets.csv'
            if bowling_path.exists():
                self.bowling_data = pd.read_csv(bowling_path)
                logging.info(f"Loaded bowling data: {len(self.bowling_data)} records")
                self._process_bowling_data_pandas()
            
            # Load auction data
            auction_path = self.data_folder_path / 'ipl data - auction_2025.csv'
            if auction_path.exists():
                self.auction_data = pd.read_csv(auction_path)
                logging.info(f"Loaded auction data: {len(self.auction_data)} records")
                # Process teams from auction data
                self._process_auction_data()
            
            # Load match results
            match_path = self.data_folder_path / 'ipl data - match_results.csv'
            if match_path.exists():
                self.match_results = pd.read_csv(match_path)
                logging.info(f"Loaded match results: {len(self.match_results)} records")
            
            # Load catches data
            catches_path = self.data_folder_path / 'ipl data - most_cactches.csv'
            if catches_path.exists():
                self.catches_data = pd.read_csv(catches_path)
                logging.info(f"Loaded catches data: {len(self.catches_data)} records")
            
            # Load dismissals data
            dismissals_path = self.data_folder_path / 'ipl data - most_dismissals.csv'
            if dismissals_path.exists():
                self.dismissals_data = pd.read_csv(dismissals_path)
                logging.info(f"Loaded dismissals data: {len(self.dismissals_data)} records")
                
            # Process batting and bowling stats into dictionaries
            self._process_batting_data_pandas()
            self._process_bowling_data_pandas()
            
        except Exception as e:
            logging.error(f"Error loading data with pandas: {str(e)}")
            # Fall back to CSV reader if pandas fails
            self._load_data_csv()
    
    def _load_data_csv(self):
        """
        Load data using CSV reader (fallback if pandas is not available)
        """
        try:
            # Load team data from auction CSV
            self._load_team_data_csv()
            
            # Load batting and bowling stats
            self._load_batting_stats_csv()
            self._load_bowling_stats_csv()
            
        except Exception as e:
            logging.error(f"Error loading data with CSV: {str(e)}")
            raise
    
    def _load_team_data_csv(self):
        """
        Load team data from the auction CSV file using standard csv module
        """
        auction_file = os.path.join(self.data_folder_path, 'ipl data - auction_2025.csv')
        logging.info(f"Loading team data from {auction_file}")
        
        try:
            current_team = None
            
            with open(auction_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row or len(row) < 1:
                        continue
                        
                    # Team headers have the format "Team Name,,,,"
                    if row[0].strip() and (len(row) < 2 or not row[1].strip()):
                        team_name = row[0].strip()
                        if team_name != "team names":  # Skip the header row
                            current_team = team_name
                            self.teams[current_team] = []
                            logging.info(f"Found team: {current_team}")
                    elif current_team and len(row) >= 4:
                        # Check if this is a player row (has index and name)
                        if row[1].strip():
                            player_name = row[1].strip()
                            # Use the Capped/Uncapped field to determine role
                            capped = row[4].strip() if len(row) > 4 else "Unknown"
                            
                            # Attempt to determine role based on name patterns and other data
                            # This is a simplistic approach - in a real-world scenario,
                            # you'd have a database with player roles
                            role = self._determine_player_role(player_name)
                            
                            # Extract price from the 'Winning Bid' field and convert to numeric
                            price_str = row[3].strip() if len(row) > 3 else "₹0"
                            # Remove the ₹ symbol and commas, then convert to float
                            price_numeric = float(price_str.replace('₹', '').replace(',', ''))
                            # Convert price to crores for easier budget calculations
                            price_crores = price_numeric / 10000000 if price_numeric > 0 else 0.1
                            
                            self.teams[current_team].append({
                                "name": player_name,
                                "role": role,
                                "price": price_crores,
                                "capped": capped == "Capped",
                                "team": current_team
                            })
            
            logging.info(f"Loaded {len(self.teams)} teams with {sum(len(players) for players in self.teams.values())} players")
        except Exception as e:
            logging.error(f"Error loading team data: {str(e)}")
            raise
    
    def _load_batting_stats_csv(self):
        """
        Load batting stats from the most_runs CSV file using standard csv module
        """
        batting_file = os.path.join(self.data_folder_path, 'ipl data - most_runs.csv')
        self.batting_stats = {}
        
        try:
            with open(batting_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header
                
                for row in reader:
                    if len(row) < 5:  # Ensure row has name and stats
                        continue
                    
                    player_name = row[0].strip()
                    matches = int(row[1]) if row[1].strip().isdigit() else 0
                    runs = int(row[2]) if row[2].strip().isdigit() else 0
                    avg = float(row[3].replace('-', '0')) if row[3].strip() else 0
                    sr = float(row[4].replace('-', '0')) if row[4].strip() else 0
                    
                    self.batting_stats[player_name] = {
                        "matches": matches,
                        "runs": runs,
                        "average": avg,
                        "strike_rate": sr
                    }
            
            logging.info(f"Loaded batting stats for {len(self.batting_stats)} players")
            
        except Exception as e:
            logging.error(f"Error loading batting stats: {str(e)}")
            raise
    
    def _load_bowling_stats_csv(self):
        """
        Load bowling stats from the most_wickets CSV file using standard csv module
        """
        bowling_file = os.path.join(self.data_folder_path, 'ipl data - most_wickets.csv')
        self.bowling_stats = {}
        
        try:
            with open(bowling_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header
                
                for row in reader:
                    if len(row) < 5:  # Ensure row has name and stats
                        continue
                    
                    player_name = row[0].strip()
                    matches = int(row[1]) if row[1].strip().isdigit() else 0
                    wickets = int(row[2]) if row[2].strip().isdigit() else 0
                    economy = float(row[3].replace('-', '0')) if row[3].strip() else 0
                    avg = float(row[4].replace('-', '0')) if row[4].strip() else 0
                    
                    self.bowling_stats[player_name] = {
                        "matches": matches,
                        "wickets": wickets,
                        "economy": economy,
                        "average": avg
                    }
            
            logging.info(f"Loaded bowling stats for {len(self.bowling_stats)} players")
            
        except Exception as e:
            logging.error(f"Error loading bowling stats: {str(e)}")
            raise
    
    def _process_auction_data(self):
        """
        Process auction data to get team information when using pandas
        """
        if self.auction_data is None:
            logging.warning("No auction data available")
            return None, None
            
        # Extract team names and players
        team_names = []
        team_players = {}
        
        # Find rows where only the first column has a value (team headers)
        for i, row in self.auction_data.iterrows():
            if pd.notna(row[0]) and (len(row) < 2 or pd.isna(row[1])):
                # This is a team header
                team_name = row[0].strip()
                team_names.append(team_name)
                team_players[team_name] = []
            elif len(team_names) > 0:
                # This is a player row
                team_name = team_names[-1]
                if len(row) > 1 and pd.notna(row[1]):
                    player_name = row[1].strip()
                    player_role = row[2].strip() if len(row) > 2 and pd.notna(row[2]) else "Unknown"
                    
                    # Handle price parsing with currency symbols
                    price_str = str(row[3]) if len(row) > 3 and pd.notna(row[3]) else "0"
                    # Remove currency symbols and commas, then convert to float
                    price_cleaned = price_str.replace('₹', '').replace(',', '').strip()
                    try:
                        player_price = float(price_cleaned) / 10000000  # Convert to crores
                    except ValueError:
                        player_price = 0.1  # Default price if parsing fails
                    
                    player_data = {
                        "name": player_name,
                        "role": player_role,
                        "price": player_price,
                        "team": team_name
                    }
                    
                    team_players[team_name].append(player_data)
        
        # Store teams in the class variable
        self.teams = team_players
        
        return team_names, team_players
    
    def get_all_teams(self):
        """
        Get all teams in the dataset
        
        Returns:
            list: Names of all teams
        """
        return list(self.teams.keys())
    
    def get_team_players(self, team_name):
        """
        Get all players for a given team
        
        Args:
            team_name: Name of the team
            
        Returns:
            list: Players in the team
        """
        return self.teams.get(team_name, [])    
    
    def _normalize_team_name(self, team_name):
        """
        Normalize team names to handle variations
        """
        if not team_name:
            return ""
            
        team_name = team_name.upper()
        
        # Team name mappings
        mappings = {
            "MI": ["MUMBAI", "MUMBAI INDIANS"],
            "CSK": ["CHENNAI", "CHENNAI SUPER KINGS"],
            "RCB": ["BANGALORE", "ROYAL CHALLENGERS BANGALORE"],
            "KKR": ["KOLKATA", "KOLKATA KNIGHT RIDERS"],
            "DC": ["DELHI", "DELHI CAPITALS", "DELHI DAREDEVILS"],
            "SRH": ["HYDERABAD", "SUNRISERS HYDERABAD"],
            "PBKS": ["PUNJAB", "PUNJAB KINGS", "KINGS XI PUNJAB"],
            "RR": ["RAJASTHAN", "RAJASTHAN ROYALS"],
            "GT": ["GUJARAT", "GUJARAT TITANS"],
            "LSG": ["LUCKNOW", "LUCKNOW SUPER GIANTS"]
        }
        
        # Check if team_name matches any known variant
        for canonical, variants in mappings.items():
            if team_name in variants or canonical == team_name:
                return canonical
                
        return team_name
        
    def _normalize_role(self, role):
        """
        Normalize player role names to standard categories
        
        Args:
            role: Original role name
            
        Returns:
            str: Normalized role name
        """
        role = role.lower()
        
        if "wicket" in role or "keeper" in role or "wk" in role:
            return "Wicket-Keeper"
        elif "bowl" in role:
            return "Bowler"
        elif "bat" in role:
            return "Batsman"
        elif "all" in role or "round" in role or "ar" in role:
            return "All-Rounder"
        else:
            # Default to batsman if unknown
            return "Batsman"
    
    def _determine_player_role(self, player_name):
        """
        Attempt to determine a player's role based on their name and available data
        
        Args:
            player_name: Name of the player
            
        Returns:
            str: Determined role (Batsman, Bowler, All-Rounder, or Wicket-Keeper)
        """
        # Initialize with unknown role
        role = "Unknown"
        
        # Check if player is in batting data with high runs
        if player_name in self.batting_stats:
            batting = self.batting_stats[player_name]
            matches = batting.get("matches", 0)
            runs = batting.get("runs", 0)
            
            if matches > 0:
                runs_per_match = runs / matches
                
                if runs_per_match > 30:
                    role = "Batsman"
                
        # Check if player is in bowling data with good wickets
        if player_name in self.bowling_stats:
            bowling = self.bowling_stats[player_name]
            matches = bowling.get("matches", 0)
            wickets = bowling.get("wickets", 0)
            
            if matches > 0:
                wickets_per_match = wickets / matches
                
                if wickets_per_match > 1.0:
                    if role == "Batsman" and runs_per_match > 20:
                        role = "All-Rounder"  # Good at both batting and bowling
                    else:
                        role = "Bowler"
                        
        # Look for wicket keeper indicators in name
        wicketkeeper_keywords = ["dhoni", "pant", "karthik", "buttler", "de kock", "kishan", "rahul"]
        if any(keyword in player_name.lower() for keyword in wicketkeeper_keywords):
            role = "Wicket-Keeper"
            
        # If still unknown, default to batsman
        if role == "Unknown":
            role = "Batsman"
            
        return role

    def calculate_player_scores(self, team1, team2):
        """
        Calculate fantasy scores for all players in the two teams based on Dream11 scoring rules
        
        Args:
            team1: First team name
            team2: Second team name
            
        Returns:
            dict: Player fantasy scores
        """
        player_scores = {}
        
        # Get players from both teams
        players_team1 = self.get_team_players(team1)
        players_team2 = self.get_team_players(team2)
        all_players = players_team1 + players_team2
        
        for player in all_players:
            player_name = player["name"]
            player_role = self._normalize_role(player["role"])
            player_team = player["team"]
            
            # Start with lineup bonus (4 points)
            fantasy_points = 4.0
            
            # Calculate fantasy points from batting stats
            batting_points = 0
            if player_name in self.batting_stats:
                batting = self.batting_stats[player_name]
                matches = batting.get("matches", 0)
                
                if matches > 0:
                    runs = batting.get("runs", 0)
                    avg_runs_per_match = runs / matches
                    
                    # Points for runs (1 per run)
                    batting_points += avg_runs_per_match
                    
                    # Boundary bonus (estimated from average)
                    if avg_runs_per_match >= 20:
                        boundaries_estimate = avg_runs_per_match * 0.15  # ~15% of runs from boundaries
                        batting_points += boundaries_estimate
                        
                        # Six bonus (estimated)
                        sixes_estimate = avg_runs_per_match * 0.05  # ~5% of runs from sixes
                        batting_points += sixes_estimate * 2  # 2 points per six
                    
                    # Run milestone bonuses
                    milestone_points = 0
                    if avg_runs_per_match >= 100:
                        milestone_points = 16  # Century bonus (replacing lower bonuses)
                    elif avg_runs_per_match >= 75:
                        milestone_points = 4 + 8 + 12  # All lower milestones
                    elif avg_runs_per_match >= 50:
                        milestone_points = 4 + 8  # 25-run and 50-run bonuses
                    elif avg_runs_per_match >= 25:
                        milestone_points = 4  # 25-run bonus
                    
                    batting_points += milestone_points
                    
                    # Strike rate impact
                    strike_rate = batting.get("strike_rate", 0)
                    if strike_rate > 170:
                        batting_points += 6
                    elif strike_rate > 150:
                        batting_points += 4
                    elif strike_rate > 130:
                        batting_points += 2
                    elif strike_rate < 70 and strike_rate >= 60:
                        batting_points -= 2
                    elif strike_rate < 60 and strike_rate >= 50:
                        batting_points -= 4
                    elif strike_rate < 50 and avg_runs_per_match >= 10:  # Only penalize if player actually batted
                        batting_points -= 6
            
            # Add batting points to total
            fantasy_points += batting_points
            
            # Calculate fantasy points from bowling stats
            bowling_points = 0
            if player_name in self.bowling_stats:
                bowling = self.bowling_stats[player_name]
                matches = bowling.get("matches", 0)
                
                if matches > 0:
                    wickets = bowling.get("wickets", 0)
                    avg_wickets_per_match = wickets / matches
                    
                    # Points for wickets (30 per wicket)
                    bowling_points += avg_wickets_per_match * 30
                    
                    # LBW/Bowled bonus (estimated as 60% of wickets)
                    lbw_bowled_estimate = avg_wickets_per_match * 0.6
                    bowling_points += lbw_bowled_estimate * 8
                    
                    # Wicket milestone bonuses
                    wicket_milestone_points = 0
                    if avg_wickets_per_match >= 5:
                        wicket_milestone_points = 4 + 8 + 12  # All wicket bonuses
                    elif avg_wickets_per_match >= 4:
                        wicket_milestone_points = 4 + 8  # 3 and 4 wicket bonuses
                    elif avg_wickets_per_match >= 3:
                        wicket_milestone_points = 4  # 3-wicket bonus
                        
                    bowling_points += wicket_milestone_points
                    
                    # Dot ball points (estimated)
                    overs_per_match = 4  # Assuming T20 format
                    economy = bowling.get("economy", 10)
                    dots_per_over = (6 - economy) if economy < 6 else (6 - economy) * 0.5
                    if dots_per_over > 0:
                        total_dots = dots_per_over * overs_per_match
                        bowling_points += total_dots  # 1 point per dot ball
                    
                    # Maiden over bonus
                    if economy < 4:
                        bowling_points += 12 * 0.2  # ~20% chance of a maiden per match for economical bowlers
                    
                    # Economy rate impact
                    if economy < 5:
                        bowling_points += 6
                    elif economy < 6:
                        bowling_points += 4
                    elif economy < 7:
                        bowling_points += 2
                    elif economy > 10 and economy <= 11:
                        bowling_points -= 2
                    elif economy > 11 and economy <= 12:
                        bowling_points -= 4
                    elif economy > 12:
                        bowling_points -= 6
            
            # Add bowling points to total            
            fantasy_points += bowling_points
            
            # Add fielding points (estimated)
            fielding_points = 0
            matches = max(
                self.batting_stats.get(player_name, {}).get("matches", 0),
                self.bowling_stats.get(player_name, {}).get("matches", 0)
            )
            
            if matches > 0:
                # Catches (8 points each)
                if player_role == "Wicket-Keeper":
                    catches_per_match = 1.2  # WKs typically take more catches
                elif player_role == "Bowler":
                    catches_per_match = 0.5  # Bowlers usually take fewer catches
                else:
                    catches_per_match = 0.8  # Batsmen and all-rounders
                
                fielding_points += catches_per_match * 8
                
                # 3 catch bonus (less common)
                three_catch_chance = 0.05  # 5% chance per match
                fielding_points += three_catch_chance * 4
                
                # Stumping points (wicket-keepers only)
                if player_role == "Wicket-Keeper":
                    stumpings_per_match = 0.3
                    fielding_points += stumpings_per_match * 12
                
                # Run-out points
                direct_runout_per_match = 0.1
                fielding_points += direct_runout_per_match * 12  # Direct hit
                
                indirect_runout_per_match = 0.15
                fielding_points += indirect_runout_per_match * 6  # Not direct hit
            
            # Add fielding points to total
            fantasy_points += fielding_points
            
            # Form adjustment based on recent performance (simulated)
            # In a real implementation, this would use recent match data
            import random
            form_factor = random.uniform(0.9, 1.1)
            fantasy_points *= form_factor
            
            # Home ground advantage (small bonus)
            if player_team == team1:
                fantasy_points *= 1.02
            
            player_scores[player_name] = {
                "fantasy_points": fantasy_points,
                "player": player,
                "batting_points": batting_points,
                "bowling_points": bowling_points,
                "fielding_points": fielding_points
            }
                
        return player_scores

    @cached_result(expires_after=300)  # Cache team predictions for 5 minutes
    def predict_team(self, team1, team2, budget=100, team_size=11, advanced_selection=True):
        """
        Predict the best Dream11 team for a match between team1 and team2
        
        Args:
            team1: First team name
            team2: Second team name
            budget: Total budget for creating the team (in crores)
            team_size: Number of players in the team
            advanced_selection: Use advanced selection algorithm (knapsack-like)
            
        Returns:
            dict: Selected team and metadata
        """
        # Ensure team names are standardized
        team1 = self._normalize_team_name(team1)
        team2 = self._normalize_team_name(team2)
        logging.info(f"Predicting team for match between {team1} and {team2}")
        
        if team1 not in self.teams:
            raise ValueError(f"Team '{team1}' not found in dataset")
        if team2 not in self.teams:
            raise ValueError(f"Team '{team2}' not found in dataset")
            
        # Calculate scores for all players
        player_scores = self.calculate_player_scores(team1, team2)
          
        if advanced_selection:
            # Use advanced selection algorithm (knapsack-like approach)
            selected_team = self._select_team_advanced(
                player_scores=player_scores,
                team1=team1,
                team2=team2,
                budget=budget,
                team_size=team_size
            )
        else:
            # Use simple greedy algorithm for team selection
            selected_team = self._select_team_greedy(
                player_scores=player_scores,
                team1=team1,
                team2=team2,
                budget=budget,
                team_size=team_size
            )
        
        # If no team could be selected, return empty result
        if not selected_team:
            return {
                "team": [],
                "score": 0,
                "budget_used": 0,
                "budget_remaining": budget,
                "roles": {"Batsman": 0, "Bowler": 0, "All-Rounder": 0, "Wicket-Keeper": 0},
                "team_distribution": {team1: 0, team2: 0},
                "captain": None,
                "vice_captain": None
            }
        
        # Calculate team composition statistics
        team_roles = {"Batsman": 0, "Bowler": 0, "All-Rounder": 0, "Wicket-Keeper": 0}
        team_counts = {team1: 0, team2: 0}
        spent_budget = 0
        
        for player in selected_team:
            team_roles[player["role"]] += 1
            team_counts[player["team"]] += 1
            spent_budget += player["price"]
        
        # Select captain and vice-captain (highest scoring players)
        if selected_team:
            team_with_scores = [(p, player_scores[p["name"]]["fantasy_points"]) for p in selected_team]
            team_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            captain = team_with_scores[0][0] if len(team_with_scores) > 0 else None
            vice_captain = team_with_scores[1][0] if len(team_with_scores) > 1 else None
            
            # Mark captain and vice-captain in the player dictionaries
            if captain:
                captain["is_captain"] = True
                for p in selected_team:
                    if p["name"] == captain["name"]:
                        p["is_captain"] = True
                    else:
                        p["is_captain"] = False
            
            if vice_captain:
                vice_captain["is_vice_captain"] = True
                for p in selected_team:
                    if p["name"] == vice_captain["name"]:
                        p["is_vice_captain"] = True
                    else:
                        p["is_vice_captain"] = False
            
            # Calculate team score with captain (2x) and vice-captain (1.5x) multipliers
            team_score = 0
            for p in selected_team:
                player_points = player_scores[p["name"]]["fantasy_points"]
                
                if p.get("is_captain", False):
                    player_points *= 2.0  # Captain gets 2x points
                elif p.get("is_vice_captain", False):
                    player_points *= 1.5  # Vice-captain gets 1.5x points
                
                team_score += player_points
        else:
            team_score = 0
            captain = None
            vice_captain = None
        
        # Prepare detailed player stats for UI display
        detailed_players = []
        for p in selected_team:
            player_stats = player_scores[p["name"]]
            detailed_players.append({
                "name": p["name"],
                "role": p["role"],
                "team": p["team"],
                "price": p["price"],
                "is_captain": p.get("is_captain", False),
                "is_vice_captain": p.get("is_vice_captain", False),
                "fantasy_points": player_stats["fantasy_points"],
                "batting_points": player_stats["batting_points"],
                "bowling_points": player_stats["bowling_points"],
                "fielding_points": player_stats["fielding_points"],
            })
        
        result = {
            "team": selected_team,
            "detailed_players": detailed_players,
            "score": team_score,
            "budget_used": spent_budget,
            "budget_remaining": budget - spent_budget,
            "roles": team_roles,
            "team_distribution": team_counts,
            "captain": captain["name"] if captain else None,
            "vice_captain": vice_captain["name"] if vice_captain else None
        }
        
        return result

    def _select_team_greedy(self, player_scores, team1, team2, budget=100, team_size=11):
        """
        Select team using simple greedy algorithm
        
        Args:
            player_scores: Dictionary of player scores
            team1: First team name
            team2: Second team name
            budget: Total budget
            team_size: Number of players in the team
            
        Returns:
            list: Selected team
        """
        # Sort players by score
        sorted_players = sorted(
            player_scores.items(),
            key=lambda item: item[1]["fantasy_points"],
            reverse=True
        )
        
        # Select the best team within budget constraints
        selected_team = []
        spent_budget = 0
        team_roles = {
            "Batsman": 0,
            "Bowler": 0,
            "All-Rounder": 0,
            "Wicket-Keeper": 0
        }
        team_counts = {team1: 0, team2: 0}
        
        # Team constraints
        max_players_per_team = 7
        min_batsmen = 3
        min_bowlers = 3
        min_all_rounders = 1
        min_wicket_keepers = 1
        
        # Prioritize selecting at least one wicket keeper
        for name, data in sorted_players:
            player = data["player"]
            if player["role"] == "Wicket-Keeper" and team_roles["Wicket-Keeper"] < min_wicket_keepers:
                if spent_budget + player["price"] <= budget:
                    selected_team.append(player)
                    spent_budget += player["price"]
                    team_roles["Wicket-Keeper"] += 1
                    team_counts[player["team"]] += 1
                    
                    if len(selected_team) >= team_size:
                        break
        
        # Select the rest of the players using greedy algorithm
        for name, data in sorted_players:
            player = data["player"]
            
            # Skip if player is already selected
            if any(p["name"] == player["name"] for p in selected_team):
                continue
            
            # Check if player's team already has max players
            if team_counts.get(player["team"], 0) >= max_players_per_team:
                continue
                
            # Check if we can afford the player
            if spent_budget + player["price"] > budget:
                continue
                
            # Check if we've reached team size
            if len(selected_team) >= team_size:
                break
                
            selected_team.append(player)
            spent_budget += player["price"]
            team_roles[player["role"]] += 1
            team_counts[player["team"]] += 1
        
        return selected_team
        
    def _select_team_advanced(self, player_scores, team1, team2, budget=100, team_size=11):
        """
        Select team using an advanced knapsack-like algorithm that considers role constraints
        
        Args:
            player_scores: Dictionary of player scores
            team1: First team name
            team2: Second team name
            budget: Total budget
            team_size: Number of players in the team
            
        Returns:
            list: Selected team
        """
        # Team constraints
        max_players_per_team = 7
        min_batsmen = 3
        max_batsmen = 5
        min_bowlers = 3
        max_bowlers = 5
        min_all_rounders = 1
        max_all_rounders = 4
        min_wicket_keepers = 1
        max_wicket_keepers = 2
        
        # Get all available players from both teams
        players_team1 = self.get_team_players(team1)
        players_team2 = self.get_team_players(team2)
        all_players = players_team1 + players_team2
        
        # Group players by role
        players_by_role = {
            "Batsman": [],
            "Bowler": [],
            "All-Rounder": [],
            "Wicket-Keeper": []
        }
        
        for player in all_players:
            role = player["role"]
            name = player["name"]
            if name in player_scores:
                players_by_role[role].append({
                    **player,
                    "score": player_scores[name]["fantasy_points"],
                    "value": player_scores[name]["fantasy_points"] / player["price"] if player["price"] > 0 else 0
                })
        
        # Sort each role group by value (points per crore)
        for role in players_by_role:
            players_by_role[role].sort(key=lambda p: p["value"], reverse=True)
        
        # Generate multiple team combinations
        best_team = None
        best_team_score = 0
        
        # Try different combinations of role counts
        role_combinations = []
        
        # Generate valid role combinations
        for wk_count in range(min_wicket_keepers, max_wicket_keepers + 1):
            for bat_count in range(min_batsmen, max_batsmen + 1):
                for bowl_count in range(min_bowlers, max_bowlers + 1):
                    for all_count in range(min_all_rounders, max_all_rounders + 1):
                        total = wk_count + bat_count + bowl_count + all_count
                        if total == team_size:
                            role_combinations.append({
                                "Wicket-Keeper": wk_count,
                                "Batsman": bat_count,
                                "Bowler": bowl_count,
                                "All-Rounder": all_count
                            })
        
        # Try each role combination
        for role_combo in role_combinations:
            # Select best players for each role based on the combo
            selected_players = []
            spent_budget = 0
            team_counts = {team1: 0, team2: 0}
            
            # Track if we're able to meet constraints
            is_valid = True
            
            # Select players for each role
            for role, count in role_combo.items():
                players = players_by_role[role]
                selected_count = 0
                
                for player in players:
                    # Skip if already selected somehow
                    if any(p["name"] == player["name"] for p in selected_players):
                        continue
                    
                    # Check team count constraint
                    if team_counts.get(player["team"], 0) >= max_players_per_team:
                        continue
                    
                    # Check budget
                    if spent_budget + player["price"] > budget:
                        continue
                    
                    # Add player to selection
                    selected_players.append(player)
                    spent_budget += player["price"]
                    team_counts[player["team"]] += 1
                    selected_count += 1
                    
                    # Stop if we've selected enough for this role
                    if selected_count >= count:
                        break
                
                # If we couldn't select enough players for this role, this combo is invalid
                if selected_count < count:
                    is_valid = False
                    break
            
            # Verify team constraints are met
            if is_valid and len(selected_players) == team_size:
                # Calculate team score
                team_score = sum(p["score"] for p in selected_players)
                
                # Update best team if this one is better
                if team_score > best_team_score:
                    best_team = selected_players
                    best_team_score = team_score
        
        # If no valid team found, fall back to greedy approach
        if best_team is None:
            logging.warning("Advanced team selection failed to find a valid team. Falling back to greedy algorithm.")
            return self._select_team_greedy(player_scores, team1, team2, budget, team_size)
        
        # Remove extra keys added for selection algorithm
        for player in best_team:
            if "score" in player:
                del player["score"]
            if "value" in player:
                del player["value"]
        
        return best_team

# Module-level functions for use in the Django application

# Global predictor instance
_predictor = None

def get_predictor():
    """
    Get or create the predictor instance
    """
    global _predictor
    if _predictor is None:
        _predictor = Dream11TeamPredictor()
    return _predictor

def load_player_data(data_dir='data/IPL-DATASET'):
    """
    Load player data from CSV files
    
    Args:
        data_dir: Path to data directory containing CSV files
        
    Returns:
        int: Number of players loaded
    """
    predictor = get_predictor()
    predictor._load_batting_stats_csv()
    predictor._load_bowling_stats_csv()
    
    # Count players by combining batting and bowling statistics
    total_players = len(set(list(predictor.batting_stats.keys()) + list(predictor.bowling_stats.keys())))
    return total_players

def load_match_data(data_dir='data/IPL-DATASET'):
    """
    Load match data from CSV files
    
    Args:
        data_dir: Path to data directory containing CSV files
        
    Returns:
        int: Number of matches loaded
    """
    predictor = get_predictor()
    predictor._load_team_data_csv()
    
    # Count the total number of teams loaded
    total_teams = len(predictor.teams)
    return total_teams

def update_player_data(data_dir='data/IPL-DATASET'):
    """
    Update player data from CSV files
    
    Args:
        data_dir: Path to data directory containing CSV files
        
    Returns:
        int: Number of players updated
    """
    # For now, just reload all data
    predictor = get_predictor()
    
    # Reset data
    predictor.teams = {}
    predictor.batting_stats = {}
    predictor.bowling_stats = {}
    
    # Reload all data
    players_loaded = load_player_data(data_dir)
    load_match_data(data_dir)
    
    return players_loaded

def predict_team(team1_name, team2_name, venue_name=None, budget=100, team_size=11, update_data=False):
    """
    Predict the best Dream11 team for a match
    
    Args:
        team1_name: Name of the first team
        team2_name: Name of the second team
        venue_name: Name of the venue (optional)
        budget: Total budget for creating the team (in crores)
        team_size: Number of players in the team
        update_data: Whether to update data before prediction
        
    Returns:
        dict: Selected team and metadata
    """
    predictor = get_predictor()
    
    # Load data if needed
    if update_data:
        update_player_data()
    
    # Predict team
    return predictor.predict_team(team1_name, team2_name, budget, team_size)
