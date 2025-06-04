"""
Dream11 Team Predictor - Data Validation Module

This module provides validation functions for the Dream11 team predictor.
It ensures that input data meets the required format and constraints.
"""
import os
import logging
from pathlib import Path

# Try to use pandas if available
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    import csv
    HAS_PANDAS = False
    logging.warning("pandas not available. Using CSV reader fallback.")


class DataValidator:
    """
    Validator class for Dream11 team predictor data
    Validates data formats, team compositions, and prediction constraints
    """
    
    def __init__(self):
        """
        Initialize the validator
        """
        self.role_constraints = {
            'Batsman': {'min': 3, 'max': 5},
            'Bowler': {'min': 3, 'max': 5},
            'All-Rounder': {'min': 1, 'max': 4},
            'Wicket Keeper': {'min': 1, 'max': 2},
            'Unknown': {'min': 0, 'max': 2},
        }
        
        # Budget and team size constraints
        self.min_budget = 80
        self.max_budget = 120
        self.min_team_size = 11
        self.max_team_size = 11
        self.max_players_per_team = 7
    
    def validate_data_files(self, data_folder_path):
        """
        Validate that all required data files exist and have the correct format
        
        Args:
            data_folder_path: Path to the folder containing IPL data files
            
        Returns:
            tuple: (is_valid, issues)
                is_valid: Boolean indicating if all files are valid
                issues: List of validation issues found
        """
        required_files = [
            'ipl data - auction_2025.csv',
            'ipl data - most_runs.csv',
            'ipl data - most_wickets.csv'
        ]
        
        optional_files = [
            'ipl data - match_results.csv',
            'ipl data - most_cactches.csv',
            'ipl data - most_dismissals.csv'
        ]
        
        issues = []
        folder_path = Path(data_folder_path)
        
        # Check if folder exists
        if not folder_path.exists():
            issues.append(f"Data folder not found: {folder_path}")
            return False, issues
        
        # Check required files
        for filename in required_files:
            file_path = folder_path / filename
            if not file_path.exists():
                issues.append(f"Required file not found: {filename}")
                continue
                
            # Check if file is a valid CSV
            if not self._is_valid_csv(file_path):
                issues.append(f"Invalid CSV format: {filename}")
        
        # Check optional files if they exist
        for filename in optional_files:
            file_path = folder_path / filename
            if file_path.exists() and not self._is_valid_csv(file_path):
                issues.append(f"Invalid CSV format: {filename}")
        
        return len(issues) == 0, issues
    
    def _is_valid_csv(self, file_path):
        """
        Check if a file is a valid CSV
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if valid CSV, False otherwise
        """
        try:
            if HAS_PANDAS:
                # Try to read with pandas
                df = pd.read_csv(file_path, nrows=5)
                return True
            else:
                # Fallback to CSV module
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    row = next(reader)
                    # Check if CSV has at least one header and one data row
                    return len(header) > 0 and len(row) > 0
        except Exception as e:
            logging.error(f"Error validating CSV: {str(e)}")
            return False
    
    def validate_team_selection(self, team_data):
        """
        Validate that a selected team meets all the requirements
        
        Args:
            team_data: Dict with team data including players and their roles
            
        Returns:
            tuple: (is_valid, issues)
                is_valid: Boolean indicating if the team is valid
                issues: List of validation issues found
        """
        issues = []
        
        # Check team size
        if len(team_data['team']) < self.min_team_size:
            issues.append(f"Team has too few players: {len(team_data['team'])}. Minimum: {self.min_team_size}")
        
        if len(team_data['team']) > self.max_team_size:
            issues.append(f"Team has too many players: {len(team_data['team'])}. Maximum: {self.max_team_size}")
        
        # Check role counts
        for role, constraints in self.role_constraints.items():
            role_count = team_data['roles'].get(role, 0)
            if role_count < constraints['min']:
                issues.append(f"Not enough {role}s: {role_count}. Minimum: {constraints['min']}")
            if role_count > constraints['max']:
                issues.append(f"Too many {role}s: {role_count}. Maximum: {constraints['max']}")
        
        # Check players per team
        for team, count in team_data.get('team_distribution', {}).items():
            if count > self.max_players_per_team:
                issues.append(f"Too many players from {team}: {count}. Maximum: {self.max_players_per_team}")
        
        return len(issues) == 0, issues
    
    def validate_prediction_params(self, team1, team2, budget=100, team_size=11):
        """
        Validate prediction parameters
        
        Args:
            team1: First team name
            team2: Second team name
            budget: Total budget for creating the team
            team_size: Number of players in the team
            
        Returns:
            tuple: (is_valid, issues)
                is_valid: Boolean indicating if parameters are valid
                issues: List of validation issues found
        """
        issues = []
        
        # Validate teams
        if not team1 or not isinstance(team1, str):
            issues.append("Team1 must be a non-empty string")
        
        if not team2 or not isinstance(team2, str):
            issues.append("Team2 must be a non-empty string")
        
        if team1 == team2:
            issues.append("Teams must be different")
        
        # Validate budget
        if not isinstance(budget, (int, float)):
            issues.append("Budget must be a number")
        elif budget < self.min_budget:
            issues.append(f"Budget too low: {budget}. Minimum: {self.min_budget}")
        elif budget > self.max_budget:
            issues.append(f"Budget too high: {budget}. Maximum: {self.max_budget}")
        
        # Validate team size
        if not isinstance(team_size, int):
            issues.append("Team size must be an integer")
        elif team_size < self.min_team_size:
            issues.append(f"Team size too small: {team_size}. Minimum: {self.min_team_size}")
        elif team_size > self.max_team_size:
            issues.append(f"Team size too large: {team_size}. Maximum: {self.max_team_size}")
        
        return len(issues) == 0, issues

