"""
Dream11 Team Predictor Model - Legacy Adapter

This module serves as an adapter for backwards compatibility.
It uses the new prediction module but maintains the old interface.
"""
import os
from pathlib import Path
from predictor.logic.prediction import Dream11TeamPredictor as NewPredictor
from predictor.logic.validator import DataValidator

class Dream11TeamPredictor:
    """
    Legacy adapter class for the Dream11 team predictor
    """
    
    def __init__(self):
        """
        Initialize the predictor using the new unified module
        """
        # Use the data folder in the project root by default
        base_dir = Path(__file__).parent.parent.parent
        data_folder_path = base_dir.parent / 'data' / 'IPL-DATASET'
        
        # Fall back to old location if new one doesn't exist
        if not data_folder_path.exists():
            data_folder_path = base_dir.parent / 'IPL-DATASET'
            
        self.predictor = NewPredictor(data_folder_path=data_folder_path)
        self.validator = DataValidator()
        
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
        # Use the new predictor but transform to old format if needed
        result = self.predictor.predict_team(team1, team2, budget, team_size)
        return result
    def get_team_players(self, team_name):
        """
        Get all players for a given team
        
        Args:
            team_name: The name of the team
        
        Returns:
            list: Players in the team
        """
        # Use the new predictor to get team players
        return self.predictor.get_team_players(team_name)
    
    def get_all_teams(self):
        """
        Get a list of all teams in the dataset
        
        Returns:
            list: All team names
        """
        # Use the new predictor to get all teams
        return self.predictor.get_all_teams()
    
    def get_player_details(self, player_name):
        """
        Get detailed statistics for a player
        
        Args:
            player_name: The name of the player
        
        Returns:
            dict: Player statistics
        """
        player_stats = {}
        
        # Use batting and bowling stats from the new predictor
        if hasattr(self.predictor, 'batting_stats') and player_name in self.predictor.batting_stats:
            player_stats['batting'] = self.predictor.batting_stats[player_name]
        
        if hasattr(self.predictor, 'bowling_stats') and player_name in self.predictor.bowling_stats:
            player_stats['bowling'] = self.predictor.bowling_stats[player_name]
        
        # Get team information
        for team_name, players in self.predictor.teams.items():
            for player in players:
                if isinstance(player, dict) and player["name"] == player_name:
                    player_stats['team'] = team_name
                    player_stats['cost'] = player.get("price", 0)
                    break
                elif player == player_name:
                    player_stats['team'] = team_name
                    break
        
        return player_stats
