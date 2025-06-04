"""
Dream11 Team Predictor - Core Prediction Logic

This module contains the main prediction algorithm for Dream11 teams.
It can work in standalone mode or as part of the Django application.
"""
import os
import logging
from pathlib import Path

# Try to use pandas and numpy, but provide fallbacks if not available
try:
    import pandas as pd
    import numpy as np
    HAS_DEPENDENCIES = True
except ImportError:
    import csv
    import random
    HAS_DEPENDENCIES = False
    logging.warning("pandas and/or numpy not available. Using CSV reader fallback.")

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
        try:
            # Load batting data
            batting_path = self.data_folder_path / 'ipl data - most_runs.csv'
            if batting_path.exists():
                self.batting_data = pd.read_csv(batting_path)
                logging.info(f"Loaded batting data: {len(self.batting_data)} records")
            
            # Load bowling data
            bowling_path = self.data_folder_path / 'ipl data - most_wickets.csv'
            if bowling_path.exists():
                self.bowling_data = pd.read_csv(bowling_path)
                logging.info(f"Loaded bowling data: {len(self.bowling_data)} records")
            
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
                    if len(row) < 2:
                        continue
                    
                    # If first column has a value but second is empty, it's a team header
                    if row[0].strip() and not row[1].strip():
                        current_team = row[0].strip()
                        self.teams[current_team] = []
                    elif current_team and row[1].strip():
                        player_name = row[1].strip()
                        player_role = row[2].strip() if len(row) > 2 and row[2].strip() else "Unknown"
                        player_price = float(row[3].strip()) if len(row) > 3 and row[3].strip() else 0.0
                        
                        self.teams[current_team].append({
                            "name": player_name,
                            "role": player_role,
                            "price": player_price,
                            "team": current_team
                        })
            
            logging.info(f"Loaded {len(self.teams)} teams")
            
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
                    player_price = float(row[3]) if len(row) > 3 and pd.notna(row[3]) else 0.0
                    
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
            if player_name in self.batting_stats:
                batting = self.batting_stats[player_name]
                matches = batting.get("matches", 0)
                
                if matches > 0:
                    runs = batting.get("runs", 0)
                    avg_runs_per_match = runs / matches
                    
                    # Points for runs (1 per run)
                    fantasy_points += avg_runs_per_match
                    
                    # Boundary bonus (estimated from average)
                    if avg_runs_per_match >= 20:
                        boundaries_estimate = avg_runs_per_match * 0.15  # ~15% of runs from boundaries
                        fantasy_points += boundaries_estimate
                        
                        # Six bonus (estimated)
                        sixes_estimate = avg_runs_per_match * 0.05  # ~5% of runs from sixes
                        fantasy_points += sixes_estimate * 2  # 2 points per six
                    
                    # Run milestone bonuses
                    if avg_runs_per_match >= 25:
                        fantasy_points += 4  # 25-run bonus
                    if avg_runs_per_match >= 50:
                        fantasy_points += 8  # Half-century bonus
                    if avg_runs_per_match >= 75:
                        fantasy_points += 12  # 75-run bonus
                    if avg_runs_per_match >= 100:
                        fantasy_points += 16  # Century bonus (replacing lower bonuses)
                        # No points for lower run milestones if century scored
                        fantasy_points -= (4 + 8 + 12)
                    
                    # Strike rate impact
                    strike_rate = batting.get("strike_rate", 0)
                    if strike_rate > 170:
                        fantasy_points += 6
                    elif strike_rate > 150:
                        fantasy_points += 4
                    elif strike_rate > 130:
                        fantasy_points += 2
                    elif strike_rate < 70 and strike_rate >= 60:
                        fantasy_points -= 2
                    elif strike_rate < 60 and strike_rate >= 50:
                        fantasy_points -= 4
                    elif strike_rate < 50 and avg_runs_per_match >= 10:  # Only penalize if player actually batted
                        fantasy_points -= 6
            
            # Calculate fantasy points from bowling stats
            if player_name in self.bowling_stats:
                bowling = self.bowling_stats[player_name]
                matches = bowling.get("matches", 0)
                
                if matches > 0:
                    wickets = bowling.get("wickets", 0)
                    avg_wickets_per_match = wickets / matches
                    
                    # Points for wickets (30 per wicket)
                    fantasy_points += avg_wickets_per_match * 30
                    
                    # LBW/Bowled bonus (estimated as 60% of wickets)
                    lbw_bowled_estimate = avg_wickets_per_match * 0.6
                    fantasy_points += lbw_bowled_estimate * 8
                    
                    # Wicket milestone bonuses
                    if avg_wickets_per_match >= 3:
                        fantasy_points += 4  # 3-wicket bonus
                    if avg_wickets_per_match >= 4:
                        fantasy_points += 8  # 4-wicket bonus
                    if avg_wickets_per_match >= 5:
                        fantasy_points += 12  # 5-wicket bonus
                    
                    # Dot ball points (estimated)
                    overs_per_match = 4  # Assuming T20 format
                    economy = bowling.get("economy", 10)
                    dots_per_over = (6 - economy) if economy < 6 else (6 - economy) * 0.5
                    if dots_per_over > 0:
                        total_dots = dots_per_over * overs_per_match
                        fantasy_points += total_dots  # 1 point per dot ball
                    
                    # Maiden over bonus
                    if economy < 4:
                        fantasy_points += 12 * 0.2  # ~20% chance of a maiden per match for economical bowlers
                    
                    # Economy rate impact
                    if economy < 5:
                        fantasy_points += 6
                    elif economy < 6:
                        fantasy_points += 4
                    elif economy < 7:
                        fantasy_points += 2
                    elif economy > 10 and economy <= 11:
                        fantasy_points -= 2
                    elif economy > 11 and economy <= 12:
                        fantasy_points -= 4
                    elif economy > 12:
                        fantasy_points -= 6
              # Add fielding points (estimated)
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
                
                fantasy_points += catches_per_match * 8
                
                # 3 catch bonus (less common)
                three_catch_chance = 0.05  # 5% chance per match
                fantasy_points += three_catch_chance * 4
                
                # Stumping points (wicket-keepers only)
                if player_role == "Wicket-Keeper":
                    stumpings_per_match = 0.3
                    fantasy_points += stumpings_per_match * 12
                
                # Run-out points
                direct_runout_per_match = 0.1
                fantasy_points += direct_runout_per_match * 12  # Direct hit
                
                indirect_runout_per_match = 0.15
                fantasy_points += indirect_runout_per_match * 6  # Not direct hit
            
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
                "player": player
            }
                
        return player_scores
    
def predict_team(self, team1, team2, budget=100, team_size=11):
        """
        Predict the best Dream11 team for a match between team1 and team2
        
        Args:
            team1: First team name
            team2: Second team name
            budget: Total budget for creating the team (in crores)
            team_size: Number of players in the team
            
        Returns:
            dict: Selected team and metadata
        """
        logging.info(f"Predicting team for match between {team1} and {team2}")
        
        if team1 not in self.teams:
            raise ValueError(f"Team '{team1}' not found in dataset")
        if team2 not in self.teams:
            raise ValueError(f"Team '{team2}' not found in dataset")
            
        # Calculate scores for all players
        player_scores = self.calculate_player_scores(team1, team2)
        
        # Sort players by score
        sorted_players = sorted(
            player_scores.items(),
            key=lambda item: item[1]["score"],
            reverse=True
        )
        
        # Select the best team within budget constraints
        selected_team = []
        spent_budget = 0
        team_roles = {
            "Batsman": 0,
            "Bowler": 0,
            "All-Rounder": 0,
            "Wicket Keeper": 0
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
            if player["role"] == "Wicket Keeper" and team_roles["Wicket Keeper"] < min_wicket_keepers:
                if spent_budget + player["price"] <= budget:
                    selected_team.append(player)
                    spent_budget += player["price"]
                    team_roles["Wicket Keeper"] += 1
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
                
            # Check role constraints
            if len(selected_team) >= team_size:
                break
                
            selected_team.append(player)
            spent_budget += player["price"]
            team_roles[player["role"]] += 1
            team_counts[player["team"]] += 1
        
        # Check if team satisfies minimum role requirements
        if (team_roles["Batsman"] < min_batsmen or
            team_roles["Bowler"] < min_bowlers or
            team_roles["All-Rounder"] < min_all_rounders or
            team_roles["Wicket Keeper"] < min_wicket_keepers):
            logging.warning("Could not satisfy minimum role requirements")
            
        # Calculate team score
        team_score = sum(player_scores[p["name"]]["score"] for p in selected_team)
        
        result = {
            "team": selected_team,
            "score": team_score,
            "budget_used": spent_budget,
            "budget_remaining": budget - spent_budget,
            "roles": team_roles,
            "team_distribution": team_counts
        }
        
        return result
