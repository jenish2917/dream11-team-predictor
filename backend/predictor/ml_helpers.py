# Helper functions for machine learning prediction
# Add default values for necessary features when making predictions
def prepare_player_input_features(player_input, prediction_type):
    """
    Add necessary default values to player input data based on prediction type.
    
    Args:
        player_input: Dictionary with player and match details
        prediction_type: 'batting' or 'bowling'
        
    Returns:
        dict: Enhanced player input with default values for missing features
    """
    enhanced_input = player_input.copy()
    
    # Get player name
    player_name = player_input.get('player_name', 'Unknown')
    
    if prediction_type == 'batting':
        # Add batting-specific features
        if 'recent_avg_runs' not in enhanced_input:
            enhanced_input['recent_avg_runs'] = 25.0  # Default average runs value
        
        if 'recent_form_runs' not in enhanced_input:
            enhanced_input['recent_form_runs'] = 20.0  # Default recent form value
            
        if 'avg_runs_vs_opposition' not in enhanced_input:
            enhanced_input['avg_runs_vs_opposition'] = 30.0  # Default value against opposition
            
        if 'avg_runs_at_venue' not in enhanced_input:
            enhanced_input['avg_runs_at_venue'] = 28.0  # Default value at venue
            
        if 'strike_rate' not in enhanced_input:
            enhanced_input['strike_rate'] = 120.0  # Default strike rate
    
    elif prediction_type == 'bowling':
        # Add bowling-specific features
        if 'recent_avg_wickets' not in enhanced_input:
            enhanced_input['recent_avg_wickets'] = 1.5  # Default average wickets
        
        if 'recent_form_wickets' not in enhanced_input:
            enhanced_input['recent_form_wickets'] = 1.0  # Default recent form
            
        if 'avg_wickets_vs_opposition' not in enhanced_input:
            enhanced_input['avg_wickets_vs_opposition'] = 1.2  # Default value against opposition
            
        if 'avg_wickets_at_venue' not in enhanced_input:
            enhanced_input['avg_wickets_at_venue'] = 1.3  # Default value at venue
            
        if 'economy' not in enhanced_input:
            enhanced_input['economy'] = 8.0  # Default economy rate
    
    return enhanced_input
