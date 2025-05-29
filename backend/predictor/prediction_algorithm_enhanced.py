import numpy as np
from .models import Player, Prediction, PredictionPlayer

class TeamPredictor:
    """
    A class that implements the prediction algorithm for Dream11 team selection.  
    """
    def __init__(self, team1_id, team2_id, venue_id, pitch_type, ml_predictions=None):
        """
        Initialize the predictor with match details.
        Args:
            team1_id: ID of the first team
            team2_id: ID of the second team
            venue_id: ID of the match venue
            pitch_type: Type of pitch (batting/bowling friendly)
            ml_predictions: Optional dict of ML predictions by player_id
        """
        self.team1_id = team1_id
        self.team2_id = team2_id
        self.venue_id = venue_id
        self.pitch_type = pitch_type
        self.ml_predictions = ml_predictions or {}
        
        # Weights for different player attributes
        self.weights = {
            'BAT': {
                'batting_average': 0.7,
                'recent_form': 0.3,
                'bowling_average': 0
            },
            'BWL': {
                'batting_average': 0.1,
                'recent_form': 0.3,
                'bowling_average': 0.6
            },
            'AR': {
                'batting_average': 0.4,
                'recent_form': 0.3,
                'bowling_average': 0.3
            },
            'WK': {
                'batting_average': 0.6,
                'recent_form': 0.4,
                'bowling_average': 0
            }
        }
        # Pitch factor adjustments
        self.pitch_factors = {
            'BAT': {'BAT': 1.2, 'BWL': 0.8, 'AR': 1.1, 'WK': 1.2},
            'BWL': {'BAT': 0.8, 'BWL': 1.2, 'AR': 0.9, 'WK': 0.8},
            'BAL': {'BAT': 1.0, 'BWL': 1.0, 'AR': 1.1, 'WK': 1.0},
            'SPIN': {'BAT': 0.9, 'BWL': 1.1, 'AR': 1.0, 'WK': 0.9}
        }
        
        # ML prediction weight
        self.ml_prediction_weight = 0.3  # How much the ML prediction affects the score
        
    def calculate_player_score(self, player):
        """
        Calculate a player's score based on their stats and the match conditions. 
        Args:
            player: Player object
        Returns:
            float: The calculated score for the player
        """
        weights = self.weights[player.role]
        pitch_factor = self.pitch_factors[self.pitch_type][player.role]
        # Basic score calculation
        score = (
            weights['batting_average'] * player.batting_average +
            weights['recent_form'] * player.recent_form +
            weights['bowling_average'] * (50 - player.bowling_average if player.bowling_average > 0 else 0)
        )
        # Apply enhanced statistics if available
        enhanced_factors = 0
        enhanced_score_bonus = 0
        # Add consistency factor (more consistent players get a bonus)
        if hasattr(player, 'consistency_index') and player.consistency_index > 0: 
            enhanced_score_bonus += player.consistency_index * 10  # Scale factor 
            enhanced_factors += 1
        # Add recent form factor (last 5 matches)
        if hasattr(player, 'last_5_matches_form') and player.last_5_matches_form > 0:
            enhanced_score_bonus += player.last_5_matches_form * 15  # Stronger weight for very recent form
            enhanced_factors += 1
        # Add venue-specific performance if available
        if hasattr(player, 'venue_performance') and player.venue_performance and str(self.venue_id) in player.venue_performance:
            venue_score = player.venue_performance[str(self.venue_id)]["rating"] * 20
            enhanced_score_bonus += venue_score
            enhanced_factors += 1
        # Add opposition-specific performance if available
        opponent_id = self.team2_id if player.team_id == self.team1_id else self.team1_id
        if hasattr(player, 'opposition_performance') and player.opposition_performance and str(opponent_id) in player.opposition_performance:
            opposition_score = player.opposition_performance[str(opponent_id)]["rating"] * 25
            enhanced_score_bonus += opposition_score
            enhanced_factors += 1
        # Apply enhanced statistics bonus (with normalization)
        if enhanced_factors > 0:
            score += (enhanced_score_bonus / enhanced_factors)        # Apply pitch factor
        score *= pitch_factor
        
        # Incorporate ML prediction if available
        if hasattr(self, 'ml_predictions') and player.id in self.ml_predictions:
            ml_pred = self.ml_predictions[player.id]
            
            # Process batting prediction
            if player.role in ['BAT', 'AR', 'WK'] and 'batting_prediction' in ml_pred:
                batting_score = 0
                      # Get direct runs prediction if available
                if ml_pred['batting_prediction'] and 'predicted_runs' in ml_pred['batting_prediction']:
                    batting_score += float(ml_pred['batting_prediction']['predicted_runs'])
                
                # Use classification probabilities if available
                if ml_pred['batting_prediction'] and 'performance_class_probabilities' in ml_pred['batting_prediction']:
                    probs = ml_pred['batting_prediction']['performance_class_probabilities']
                    if 'High' in probs:
                        batting_score += float(probs['High']) * 50  # High performance weight
                    if 'Medium' in probs:
                        batting_score += float(probs['Medium']) * 25  # Medium performance weight
                
                # Scale and add to score
                score += (batting_score * self.ml_prediction_weight)
            
            # Process bowling prediction
            if player.role in ['BWL', 'AR'] and 'bowling_prediction' in ml_pred:
                bowling_score = 0
                  # Get direct wickets prediction if available
                if ml_pred['bowling_prediction'] and 'predicted_wickets' in ml_pred['bowling_prediction']:
                    bowling_score += float(ml_pred['bowling_prediction']['predicted_wickets']) * 20
                
                # Use classification probabilities if available
                if ml_pred['bowling_prediction'] and 'performance_class_probabilities' in ml_pred['bowling_prediction']:
                    probs = ml_pred['bowling_prediction']['performance_class_probabilities']
                    if 'High' in probs:
                        bowling_score += float(probs['High']) * 60  # High performance weight
                    if 'Medium' in probs:
                        bowling_score += float(probs['Medium']) * 30  # Medium performance weight
                
                # Scale and add to score
                score += (bowling_score * self.ml_prediction_weight)
        ml_prediction = self.ml_predictions.get(player.id)
        if ml_prediction:
            score = score * (1 - self.ml_prediction_weight) + ml_prediction * self.ml_prediction_weight
        # Add some randomness (to simulate unpredictability of performances)      
        # Less randomness for players with high consistency index
        randomness_factor = 0.1
        if hasattr(player, 'consistency_index') and player.consistency_index > 0:
            randomness_factor = max(0.03, 0.1 - (player.consistency_index / 10))  
        random_factor = np.random.normal(1, randomness_factor)
        score *= random_factor
        return score
        
    def predict_teams(self):
        """
        Generate three different team compositions based on different strategies. 
        Returns:
            dict: A dictionary containing three team predictions (aggressive, balanced, risk-averse)
        """
        # Get all players from both teams
        players = Player.objects.filter(team_id__in=[self.team1_id, self.team2_id])
        # Calculate scores for each player
        player_scores = [(player, self.calculate_player_score(player)) for player in players]
        # Sort players by score (descending)
        player_scores.sort(key=lambda x: x[1], reverse=True)
        # Generate aggressive team (more focus on top performers)
        aggressive_team = self._select_dream11_team(player_scores, strategy='aggressive')
        # Generate balanced team (mix of roles)
        balanced_team = self._select_dream11_team(player_scores, strategy='balanced')
        # Generate risk-averse team (more consistent players)
        risk_averse_team = self._select_dream11_team(player_scores, strategy='risk-averse')
        return {
            'AGG': aggressive_team,
            'BAL': balanced_team,
            'RISK': risk_averse_team
        }
        
    def _select_dream11_team(self, player_scores, strategy='balanced'):
        """
        Select a Dream11 team based on the given strategy.
        Args:
            player_scores: List of (player, score) tuples
            strategy: Either 'aggressive', 'balanced', or 'risk-averse'
        Returns:
            list: A list of (player, score, role) tuples representing the selected team
        """
        # Apply strategy modifiers
        if strategy == 'aggressive':
            # Aggressive: Boost high-scorers, penalize low-scorers
            modified_scores = [(p, s * (1 + 0.2 * i/len(player_scores))) 
                            for i, (p, s) in enumerate(player_scores)]
        elif strategy == 'risk-averse':
            # Risk-averse: Reduce variance, boost consistent players
            # If the player has consistency_index, use it to make more informed decisions
            modified_scores = []
            for p, s in player_scores:
                if hasattr(p, 'consistency_index') and p.consistency_index > 0:
                    # Boost consistent players
                    modified_scores.append((p, s * (1 + 0.2 * p.consistency_index / 10)))
                else:
                    # Use the old heuristic for players without consistency data
                    factor = (1 - 0.1 * (p.recent_form / p.batting_average if p.batting_average > 0 else 0))
                    modified_scores.append((p, s * factor))
        else:  # balanced
            modified_scores = player_scores
            
        # Sort again based on modified scores
        modified_scores.sort(key=lambda x: x[1], reverse=True)
        # Pick players by role requirements (4-3-2-2 formation)
        # 4 batsmen, 3 all-rounders, 2 bowlers, 2 wicketkeepers
        selected_players = []
        role_counts = {'BAT': 0, 'AR': 0, 'BWL': 0, 'WK': 0}
        role_limits = {'BAT': 4, 'AR': 3, 'BWL': 2, 'WK': 2}
        # First pass: select by role until limits are reached
        for player, score in modified_scores:
            if len(selected_players) >= 11:
                break
            if role_counts[player.role] < role_limits[player.role]:
                selected_players.append((player, score, player.role))
                role_counts[player.role] += 1
        # If we still need more players, pick the highest scorers regardless of role
        if len(selected_players) < 11:
            remaining_slots = 11 - len(selected_players)
            already_selected_ids = [p[0].id for p in selected_players]
            for player, score in modified_scores:
                if player.id not in already_selected_ids:
                    selected_players.append((player, score, player.role))
                    remaining_slots -= 1
                if remaining_slots <= 0:
                    break
        # Sort the final team by score for easier processing
        selected_players.sort(key=lambda x: x[1], reverse=True)
        # Assign captain and vice-captain (top 2 scoring players)
        final_team = []
        for i, (player, score, role) in enumerate(selected_players):
            is_captain = (i == 0)
            is_vice_captain = (i == 1)
            expected_points = score * 2 if is_captain else score * 1.5 if is_vice_captain else score
            final_team.append({
                'player': player,
                'is_captain': is_captain,
                'is_vice_captain': is_vice_captain,
                'expected_points': expected_points
            })
        return final_team
