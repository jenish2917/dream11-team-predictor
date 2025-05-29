"""
Player Performance Predictor for Dream11 Team Predictor

This module implements machine learning models to predict player performance
in upcoming matches based on historical data, venue statistics, opposition, and more.
"""

import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime
import logging

# ML imports
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.svm import SVR, SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import mean_squared_error, accuracy_score, precision_score, classification_report

# Optional - try to import XGBoost, but don't fail if not installed
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class PlayerPerformancePredictor:
    """
    Class for predicting player performance using machine learning models.
    Supports both regression (predict exact runs/wickets) and classification
    (predict performance category).
    """
    def __init__(self, data_dir=None):
        """
        Initialize the predictor.
        
        Args:
            data_dir: Directory containing player statistics data files
        """
        self.data_dir = data_dir
        self.models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ml_models')
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Data frames
        self.batting_df = None
        self.bowling_df = None
        self.players_df = None
        
        # ML models and preprocessing
        self.batting_regression_model = None
        self.batting_classification_model = None
        self.bowling_regression_model = None
        self.bowling_classification_model = None
        self.batting_preprocessor = None
        self.bowling_preprocessor = None
        
        # Performance class thresholds
        self.batting_thresholds = {
            'High': 50,  # >= 50 runs is high
            'Medium': 20  # >= 20 runs is medium, below is low
        }
        
        self.bowling_thresholds = {
            'High': 3,    # >= 3 wickets is high
            'Medium': 1   # >= 1 wickets is medium, below is low
        }
        
    def load_data(self, batting_file=None, bowling_file=None):
        """
        Load player statistics data from CSV files.
        
        Args:
            batting_file: Path to batting statistics CSV
            bowling_file: Path to bowling statistics CSV
            
        Returns:
            bool: True if data was loaded successfully
        """
        try:
            if self.data_dir is None:
                logging.error("No data directory specified")
                return False
            
            # Use provided file paths or default to data_dir
            batting_path = batting_file or os.path.join(self.data_dir, 'batting_data.csv')
            bowling_path = bowling_file or os.path.join(self.data_dir, 'bowling_data.csv')
            
            if os.path.exists(batting_path):
                self.batting_df = pd.read_csv(batting_path)
                logging.info(f"Loaded batting data: {len(self.batting_df)} records")
            else:
                logging.warning(f"Batting data file not found: {batting_path}")
                
            if os.path.exists(bowling_path):
                self.bowling_df = pd.read_csv(bowling_path)
                logging.info(f"Loaded bowling data: {len(self.bowling_df)} records")
            else:
                logging.warning(f"Bowling data file not found: {bowling_path}")
            
            return len(self.batting_df) > 0 or len(self.bowling_df) > 0
        
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            return False
    
    def prepare_batting_features(self):
        """
        Prepare features for batting performance prediction.
        
        Returns:
            tuple: X (features), y_regression (runs), y_classification (performance class)
        """
        if self.batting_df is None or len(self.batting_df) == 0:
            logging.error("No batting data available")
            return None, None, None
        
        # Create a copy to avoid modifying original data
        df = self.batting_df.copy()
        
        # Convert match_date to datetime if it's a string
        if 'match_date' in df.columns and df['match_date'].dtype == 'object':
            df['match_date'] = pd.to_datetime(df['match_date'])
            
        # Feature engineering
        # 1. Calculate player's recent form (last 3 matches)
        recent_form = df.sort_values('match_date').groupby('player_name')['runs'].rolling(3).mean().reset_index(0, drop=True)
        df['recent_avg_runs'] = df['player_name'].map(df.groupby('player_name')['runs'].mean())
        df['recent_form_runs'] = recent_form
        
        # 2. Calculate player's performance against specific opposition
        opposition_avg = df.groupby(['player_name', 'opposing_team'])['runs'].mean().reset_index()
        opposition_avg.columns = ['player_name', 'opposing_team', 'avg_runs_vs_opposition']
        df = pd.merge(df, opposition_avg, on=['player_name', 'opposing_team'], how='left')
        
        # 3. Calculate player's performance at specific venues
        venue_avg = df.groupby(['player_name', 'venue'])['runs'].mean().reset_index()
        venue_avg.columns = ['player_name', 'venue', 'avg_runs_at_venue']
        df = pd.merge(df, venue_avg, on=['player_name', 'venue'], how='left')
        
        # 4. Calculate strike rate if not available
        if 'strike_rate' not in df.columns and 'balls' in df.columns and 'runs' in df.columns:
            df['strike_rate'] = (df['runs'] / df['balls'] * 100).fillna(0)
        
        # 5. Convert date features
        if 'match_date' in df.columns:
            df['match_year'] = df['match_date'].dt.year
            df['match_month'] = df['match_date'].dt.month
        
        # 6. Fill NaN values with appropriate defaults
        df = df.fillna({
            'recent_form_runs': df['runs'].mean(),
            'avg_runs_vs_opposition': df['runs'].mean(),
            'avg_runs_at_venue': df['runs'].mean(),
            'strike_rate': 0
        })
        
        # Create classification target
        df['performance_class'] = self._classify_batting_performance(df['runs'])
        
        # Select features for the model
        feature_columns = [
            'role', 'venue', 'opposing_team', 'recent_avg_runs',
            'recent_form_runs', 'avg_runs_vs_opposition', 'avg_runs_at_venue'
        ]
        
        # Only include columns that exist in the dataframe
        feature_columns = [col for col in feature_columns if col in df.columns]
        
        if not feature_columns:
            logging.error("No valid feature columns found in batting data")
            return None, None, None
        
        X = df[feature_columns]
        y_regression = df['runs']
        y_classification = df['performance_class']
        
        return X, y_regression, y_classification
    
    def prepare_bowling_features(self):
        """
        Prepare features for bowling performance prediction.
        
        Returns:
            tuple: X (features), y_regression (wickets), y_classification (performance class)
        """
        if self.bowling_df is None or len(self.bowling_df) == 0:
            logging.error("No bowling data available")
            return None, None, None
        
        # Create a copy to avoid modifying original data
        df = self.bowling_df.copy()
        
        # Convert match_date to datetime if it's a string
        if 'match_date' in df.columns and df['match_date'].dtype == 'object':
            df['match_date'] = pd.to_datetime(df['match_date'])
        
        # Feature engineering
        # 1. Calculate player's recent form (last 3 matches)
        recent_form = df.sort_values('match_date').groupby('player_name')['wickets'].rolling(3).mean().reset_index(0, drop=True)
        df['recent_avg_wickets'] = df['player_name'].map(df.groupby('player_name')['wickets'].mean())
        df['recent_form_wickets'] = recent_form
        
        # 2. Calculate player's performance against specific opposition
        opposition_avg = df.groupby(['player_name', 'opposing_team'])['wickets'].mean().reset_index()
        opposition_avg.columns = ['player_name', 'opposing_team', 'avg_wickets_vs_opposition']
        df = pd.merge(df, opposition_avg, on=['player_name', 'opposing_team'], how='left')
        
        # 3. Calculate player's performance at specific venues
        venue_avg = df.groupby(['player_name', 'venue'])['wickets'].mean().reset_index()
        venue_avg.columns = ['player_name', 'venue', 'avg_wickets_at_venue']
        df = pd.merge(df, venue_avg, on=['player_name', 'venue'], how='left')
        
        # 4. Convert date features
        if 'match_date' in df.columns:
            df['match_year'] = df['match_date'].dt.year
            df['match_month'] = df['match_date'].dt.month
        
        # 5. Fill NaN values with appropriate defaults
        df = df.fillna({
            'recent_form_wickets': df['wickets'].mean(),
            'avg_wickets_vs_opposition': df['wickets'].mean(),
            'avg_wickets_at_venue': df['wickets'].mean()
        })
        
        # Create classification target
        df['performance_class'] = self._classify_bowling_performance(df['wickets'])
        
        # Select features for the model
        feature_columns = [
            'role', 'venue', 'opposing_team', 'recent_avg_wickets',
            'recent_form_wickets', 'avg_wickets_vs_opposition', 'avg_wickets_at_venue',
            'economy'
        ]
        
        # Only include columns that exist in the dataframe
        feature_columns = [col for col in feature_columns if col in df.columns]
        
        if not feature_columns:
            logging.error("No valid feature columns found in bowling data")
            return None, None, None
        
        X = df[feature_columns]
        y_regression = df['wickets']
        y_classification = df['performance_class']
        
        return X, y_regression, y_classification
    
    def train_models(self):
        """
        Train machine learning models for both batting and bowling prediction.
        
        Returns:
            bool: True if all models were trained successfully
        """
        success = True
        
        # Train batting models if data is available
        if self.batting_df is not None and len(self.batting_df) > 0:
            success = success and self._train_batting_models()
        else:
            logging.warning("Skipping batting model training: No batting data available")
        
        # Train bowling models if data is available
        if self.bowling_df is not None and len(self.bowling_df) > 0:
            success = success and self._train_bowling_models()
        else:
            logging.warning("Skipping bowling model training: No bowling data available")
        
        return success
    
    def _train_batting_models(self):
        """
        Train batting performance prediction models.
        
        Returns:
            bool: True if models were trained successfully
        """
        try:
            # Prepare features
            X, y_regression, y_classification = self.prepare_batting_features()
            
            if X is None or y_regression is None:
                return False
            
            # Split data
            X_train, X_test, y_reg_train, y_reg_test = train_test_split(
                X, y_regression, test_size=0.2, random_state=42
            )
            
            # Create preprocessor
            categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
            numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
            preprocessor = ColumnTransformer([
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
                ('num', StandardScaler(), numeric_features)
            ])
            
            # Save preprocessor
            self.batting_preprocessor = preprocessor
            
            # Train and evaluate regression models
            reg_models = {
                'LinearRegression': LinearRegression(),
                'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42)
            }
            
            # Add XGBoost if available
            if XGBOOST_AVAILABLE:
                reg_models['XGBoost'] = xgb.XGBRegressor(random_state=42)
            
            best_reg_model = None
            best_reg_mse = float('inf')
            
            logging.info("Training batting regression models:")
            for name, model in reg_models.items():
                pipeline = Pipeline([
                    ('preprocessor', preprocessor),
                    ('model', model)
                ])
                
                pipeline.fit(X_train, y_reg_train)
                y_pred = pipeline.predict(X_test)
                mse = mean_squared_error(y_reg_test, y_pred)
                
                logging.info(f"  {name} MSE: {mse:.2f}")
                
                if mse < best_reg_mse:
                    best_reg_mse = mse
                    best_reg_model = pipeline
            
            self.batting_regression_model = best_reg_model
            logging.info(f"Best batting regression model: MSE = {best_reg_mse:.2f}")
            
            # For classification, we need to convert runs to classes
            if y_classification is not None:
                # Split data
                X_train, X_test, y_cls_train, y_cls_test = train_test_split(
                    X, y_classification, test_size=0.2, random_state=42, stratify=y_classification
                )
                
                # Train and evaluate classification models
                cls_models = {
                    'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
                    'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
                    'SVC': SVC(probability=True, random_state=42)
                }
                
                # Add XGBoost if available
                if XGBOOST_AVAILABLE:
                    cls_models['XGBoost'] = xgb.XGBClassifier(random_state=42)
                
                best_cls_model = None
                best_cls_score = -1
                
                logging.info("Training batting classification models:")
                for name, model in cls_models.items():
                    pipeline = Pipeline([
                        ('preprocessor', preprocessor),
                        ('model', model)
                    ])
                    
                    pipeline.fit(X_train, y_cls_train)
                    y_pred = pipeline.predict(X_test)
                    accuracy = accuracy_score(y_cls_test, y_pred)
                    precision = precision_score(y_cls_test, y_pred, average='weighted')
                    
                    # Combined score (accuracy + precision)
                    score = accuracy + precision
                    logging.info(f"  {name} - Accuracy: {accuracy:.2f}, Precision: {precision:.2f}")
                    
                    if score > best_cls_score:
                        best_cls_score = score
                        best_cls_model = pipeline
                
                self.batting_classification_model = best_cls_model
                logging.info(f"Best batting classification model selected (Accuracy + Precision = {best_cls_score:.2f})")
                
                # Save detailed report for the best model
                y_pred = best_cls_model.predict(X_test)
                logging.info("\nClassification Report:")
                logging.info(classification_report(y_cls_test, y_pred))
            
            # Save models
            self._save_models('batting')
            return True
            
        except Exception as e:
            logging.error(f"Error training batting models: {str(e)}")
            return False
    
    def _train_bowling_models(self):
        """
        Train bowling performance prediction models.
        
        Returns:
            bool: True if models were trained successfully
        """
        try:
            # Prepare features
            X, y_regression, y_classification = self.prepare_bowling_features()
            
            if X is None or y_regression is None:
                return False
            
            # Split data
            X_train, X_test, y_reg_train, y_reg_test = train_test_split(
                X, y_regression, test_size=0.2, random_state=42
            )
            
            # Create preprocessor
            categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
            numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
            preprocessor = ColumnTransformer([
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
                ('num', StandardScaler(), numeric_features)
            ])
            
            # Save preprocessor
            self.bowling_preprocessor = preprocessor
            
            # Train and evaluate regression models
            reg_models = {
                'LinearRegression': LinearRegression(),
                'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42)
            }
            
            # Add XGBoost if available
            if XGBOOST_AVAILABLE:
                reg_models['XGBoost'] = xgb.XGBRegressor(random_state=42)
            
            best_reg_model = None
            best_reg_mse = float('inf')
            
            logging.info("Training bowling regression models:")
            for name, model in reg_models.items():
                pipeline = Pipeline([
                    ('preprocessor', preprocessor),
                    ('model', model)
                ])
                
                pipeline.fit(X_train, y_reg_train)
                y_pred = pipeline.predict(X_test)
                mse = mean_squared_error(y_reg_test, y_pred)
                
                logging.info(f"  {name} MSE: {mse:.2f}")
                
                if mse < best_reg_mse:
                    best_reg_mse = mse
                    best_reg_model = pipeline
            
            self.bowling_regression_model = best_reg_model
            logging.info(f"Best bowling regression model: MSE = {best_reg_mse:.2f}")
            
            # For classification, we need to convert wickets to classes
            if y_classification is not None:
                # Split data
                X_train, X_test, y_cls_train, y_cls_test = train_test_split(
                    X, y_classification, test_size=0.2, random_state=42, stratify=y_classification
                )
                
                # Train and evaluate classification models
                cls_models = {
                    'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
                    'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
                    'SVC': SVC(probability=True, random_state=42)
                }
                
                # Add XGBoost if available
                if XGBOOST_AVAILABLE:
                    cls_models['XGBoost'] = xgb.XGBClassifier(random_state=42)
                
                best_cls_model = None
                best_cls_score = -1
                
                logging.info("Training bowling classification models:")
                for name, model in cls_models.items():
                    pipeline = Pipeline([
                        ('preprocessor', preprocessor),
                        ('model', model)
                    ])
                    
                    pipeline.fit(X_train, y_cls_train)
                    y_pred = pipeline.predict(X_test)
                    accuracy = accuracy_score(y_cls_test, y_pred)
                    precision = precision_score(y_cls_test, y_pred, average='weighted')
                    
                    # Combined score (accuracy + precision)
                    score = accuracy + precision
                    logging.info(f"  {name} - Accuracy: {accuracy:.2f}, Precision: {precision:.2f}")
                    
                    if score > best_cls_score:
                        best_cls_score = score
                        best_cls_model = pipeline
                
                self.bowling_classification_model = best_cls_model
                logging.info(f"Best bowling classification model selected (Accuracy + Precision = {best_cls_score:.2f})")
                
                # Save detailed report for the best model
                y_pred = best_cls_model.predict(X_test)
                logging.info("\nClassification Report:")
                logging.info(classification_report(y_cls_test, y_pred))
            
            # Save models
            self._save_models('bowling')
            return True
            
        except Exception as e:
            logging.error(f"Error training bowling models: {str(e)}")
            return False
    
    def _save_models(self, model_type):
        """
        Save trained models to disk.
        
        Args:
            model_type: Type of model ('batting' or 'bowling')
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if model_type == 'batting':
            if self.batting_regression_model is not None:
                joblib.dump(self.batting_regression_model, 
                           os.path.join(self.models_dir, f'batting_regression_{timestamp}.pkl'))
                
            if self.batting_classification_model is not None:
                joblib.dump(self.batting_classification_model,
                           os.path.join(self.models_dir, f'batting_classification_{timestamp}.pkl'))
                
            if self.batting_preprocessor is not None:
                joblib.dump(self.batting_preprocessor,
                           os.path.join(self.models_dir, f'batting_preprocessor_{timestamp}.pkl'))
        
        elif model_type == 'bowling':
            if self.bowling_regression_model is not None:
                joblib.dump(self.bowling_regression_model,
                           os.path.join(self.models_dir, f'bowling_regression_{timestamp}.pkl'))
                
            if self.bowling_classification_model is not None:
                joblib.dump(self.bowling_classification_model,
                           os.path.join(self.models_dir, f'bowling_classification_{timestamp}.pkl'))
                
            if self.bowling_preprocessor is not None:
                joblib.dump(self.bowling_preprocessor,
                           os.path.join(self.models_dir, f'bowling_preprocessor_{timestamp}.pkl'))
    
    def load_models(self, batting_reg_path=None, batting_cls_path=None, 
                    bowling_reg_path=None, bowling_cls_path=None):
        """
        Load previously trained models from disk.
        
        Args:
            batting_reg_path: Path to batting regression model
            batting_cls_path: Path to batting classification model
            bowling_reg_path: Path to bowling regression model
            bowling_cls_path: Path to bowling classification model
            
        Returns:
            bool: True if models were loaded successfully
        """
        try:
            # Find latest models if paths not provided
            if batting_reg_path is None:
                batting_reg_files = [f for f in os.listdir(self.models_dir) 
                                    if f.startswith('batting_regression_')]
                if batting_reg_files:
                    batting_reg_path = os.path.join(self.models_dir, sorted(batting_reg_files)[-1])
            
            if batting_cls_path is None:
                batting_cls_files = [f for f in os.listdir(self.models_dir) 
                                    if f.startswith('batting_classification_')]
                if batting_cls_files:
                    batting_cls_path = os.path.join(self.models_dir, sorted(batting_cls_files)[-1])
            
            if bowling_reg_path is None:
                bowling_reg_files = [f for f in os.listdir(self.models_dir) 
                                    if f.startswith('bowling_regression_')]
                if bowling_reg_files:
                    bowling_reg_path = os.path.join(self.models_dir, sorted(bowling_reg_files)[-1])
            
            if bowling_cls_path is None:
                bowling_cls_files = [f for f in os.listdir(self.models_dir) 
                                    if f.startswith('bowling_classification_')]
                if bowling_cls_files:
                    bowling_cls_path = os.path.join(self.models_dir, sorted(bowling_cls_files)[-1])
            
            # Load models if they exist
            if batting_reg_path and os.path.exists(batting_reg_path):
                self.batting_regression_model = joblib.load(batting_reg_path)
                logging.info(f"Loaded batting regression model: {batting_reg_path}")
            
            if batting_cls_path and os.path.exists(batting_cls_path):
                self.batting_classification_model = joblib.load(batting_cls_path)
                logging.info(f"Loaded batting classification model: {batting_cls_path}")
            
            if bowling_reg_path and os.path.exists(bowling_reg_path):
                self.bowling_regression_model = joblib.load(bowling_reg_path)
                logging.info(f"Loaded bowling regression model: {bowling_reg_path}")
            
            if bowling_cls_path and os.path.exists(bowling_cls_path):
                self.bowling_classification_model = joblib.load(bowling_cls_path)
                logging.info(f"Loaded bowling classification model: {bowling_cls_path}")
            
            # Also try to load preprocessors
            preprocessor_files = [f for f in os.listdir(self.models_dir) if 'preprocessor' in f]
            
            for file in preprocessor_files:
                if file.startswith('batting_preprocessor_') and self.batting_preprocessor is None:
                    self.batting_preprocessor = joblib.load(os.path.join(self.models_dir, file))
                    logging.info(f"Loaded batting preprocessor: {file}")
                
                if file.startswith('bowling_preprocessor_') and self.bowling_preprocessor is None:
                    self.bowling_preprocessor = joblib.load(os.path.join(self.models_dir, file))
                    logging.info(f"Loaded bowling preprocessor: {file}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error loading models: {str(e)}")
            return False
    
    def _classify_batting_performance(self, runs):
        """
        Classify batting performance into categories based on runs scored.
        
        Args:
            runs: Series of runs scored
            
        Returns:
            Series: Performance classification ('High', 'Medium', 'Low')
        """
        conditions = [
            runs >= self.batting_thresholds['High'],
            (runs >= self.batting_thresholds['Medium']) & (runs < self.batting_thresholds['High']),
            runs < self.batting_thresholds['Medium']
        ]
        choices = ['High', 'Medium', 'Low']
        return np.select(conditions, choices, default='Low')
    
    def _classify_bowling_performance(self, wickets):
        """
        Classify bowling performance into categories based on wickets taken.
        
        Args:
            wickets: Series of wickets taken
            
        Returns:
            Series: Performance classification ('High', 'Medium', 'Low')
        """
        conditions = [
            wickets >= self.bowling_thresholds['High'],
            (wickets >= self.bowling_thresholds['Medium']) & (wickets < self.bowling_thresholds['High']),
            wickets < self.bowling_thresholds['Medium']
        ]
        choices = ['High', 'Medium', 'Low']
        return np.select(conditions, choices, default='Low')
    def predict_performance(self, player_input, prediction_type, performance_type='both'):
        """
        Predict player performance for an upcoming match.
        
        Args:
            player_input: Dictionary with player and match features
            prediction_type: 'batting' or 'bowling'
            performance_type: 'regression', 'classification', or 'both'
            
        Returns:
            dict: Predicted performance metrics
        """
        try:
            if prediction_type not in ['batting', 'bowling']:
                logging.error(f"Invalid prediction type: {prediction_type}")
                return None
            
            # Add missing required features for prediction
            input_df_dict = dict(player_input)  # Make a copy
            
            # Add missing batting features if needed
            if prediction_type == 'batting':
                # Add required features if missing
                if 'recent_avg_runs' not in input_df_dict:
                    input_df_dict['recent_avg_runs'] = 25.0  # Default average runs
                if 'recent_form_runs' not in input_df_dict:
                    input_df_dict['recent_form_runs'] = input_df_dict.get('runs', 25.0)
                if 'avg_runs_vs_opposition' not in input_df_dict:
                    input_df_dict['avg_runs_vs_opposition'] = 25.0
                if 'avg_runs_at_venue' not in input_df_dict:
                    input_df_dict['avg_runs_at_venue'] = 25.0
            
            # Add missing bowling features if needed
            if prediction_type == 'bowling':
                # Add required features if missing
                if 'recent_avg_wickets' not in input_df_dict:
                    input_df_dict['recent_avg_wickets'] = 1.5  # Default average wickets
                if 'recent_form_wickets' not in input_df_dict:
                    input_df_dict['recent_form_wickets'] = input_df_dict.get('wickets', 1.5)
                if 'avg_wickets_vs_opposition' not in input_df_dict:
                    input_df_dict['avg_wickets_vs_opposition'] = 1.5
                if 'avg_wickets_at_venue' not in input_df_dict:
                    input_df_dict['avg_wickets_at_venue'] = 1.5
                if 'economy' not in input_df_dict:
                    input_df_dict['economy'] = 8.0  # Default economy rate
            
            # Convert input to DataFrame
            input_df = pd.DataFrame([input_df_dict])
            
            result = {
                'player_name': input_df_dict.get('player_name', 'Unknown'),
                'prediction_type': prediction_type
            }
            
            # Batting prediction
            if prediction_type == 'batting':
                if performance_type in ['regression', 'both'] and self.batting_regression_model is not None:
                    predicted_runs = self.batting_regression_model.predict(input_df)[0]
                    result['predicted_runs'] = max(0, round(predicted_runs, 1))
                
                if performance_type in ['classification', 'both'] and self.batting_classification_model is not None:
                    predicted_class = self.batting_classification_model.predict(input_df)[0]
                    result['performance_class'] = predicted_class
                    
                    # Get class probabilities if available
                    try:
                        probs = self.batting_classification_model.predict_proba(input_df)[0]
                        classes = self.batting_classification_model.classes_
                        result['class_probabilities'] = {cls: round(prob, 3) for cls, prob in zip(classes, probs)}
                    except:
                        pass
            
            # Bowling prediction
            elif prediction_type == 'bowling':
                if performance_type in ['regression', 'both'] and self.bowling_regression_model is not None:
                    predicted_wickets = self.bowling_regression_model.predict(input_df)[0]
                    result['predicted_wickets'] = max(0, round(predicted_wickets, 1))
                
                if performance_type in ['classification', 'both'] and self.bowling_classification_model is not None:
                    predicted_class = self.bowling_classification_model.predict(input_df)[0]
                    result['performance_class'] = predicted_class
                    
                    # Get class probabilities if available
                    try:
                        probs = self.bowling_classification_model.predict_proba(input_df)[0]
                        classes = self.bowling_classification_model.classes_
                        result['class_probabilities'] = {cls: round(prob, 3) for cls, prob in zip(classes, probs)}
                    except:
                        pass
            
            return result
            
        except Exception as e:
            logging.error(f"Error predicting performance: {str(e)}")
            return None
    
    def predict_next_match_performance(self, player_name, match_details):
        """
        Predict a player's performance in an upcoming match.
        
        Args:
            player_name: Name of the player
            match_details: Dictionary with match details (venue, opposing_team, etc.)
            
        Returns:
            dict: Predicted performance
        """
        # Find player data
        batting_data = None
        bowling_data = None
        
        if self.batting_df is not None and player_name in self.batting_df['player_name'].values:
            player_batting = self.batting_df[self.batting_df['player_name'] == player_name].iloc[-1].to_dict()
            
            # Combine player data with match details
            batting_data = {**player_batting, **match_details}
            
            # Remove output variables
            if 'runs' in batting_data:
                del batting_data['runs']
            if 'performance_class' in batting_data:
                del batting_data['performance_class']
        
        if self.bowling_df is not None and player_name in self.bowling_df['player_name'].values:
            player_bowling = self.bowling_df[self.bowling_df['player_name'] == player_name].iloc[-1].to_dict()
            
            # Combine player data with match details
            bowling_data = {**player_bowling, **match_details}
            
            # Remove output variables
            if 'wickets' in bowling_data:
                del bowling_data['wickets']
            if 'performance_class' in bowling_data:
                del bowling_data['performance_class']
        
        results = {}
        
        # Get batting prediction if data available
        if batting_data is not None and (self.batting_regression_model is not None or self.batting_classification_model is not None):
            batting_prediction = self.predict_performance(batting_data, 'batting')
            if batting_prediction:
                results['batting'] = batting_prediction
        
        # Get bowling prediction if data available
        if bowling_data is not None and (self.bowling_regression_model is not None or self.bowling_classification_model is not None):
            bowling_prediction = self.predict_performance(bowling_data, 'bowling')
            if bowling_prediction:
                results['bowling'] = bowling_prediction
                
        if not results:
            logging.warning(f"Could not make prediction for player {player_name}")
            return None
            
        results['player_name'] = player_name
        return results
    
    def generate_match_predictions(self, team1, team2, venue, date=None):
        """
        Generate performance predictions for all players in an upcoming match.
        
        Args:
            team1: First team name
            team2: Second team name
            venue: Match venue
            date: Match date (optional)
            
        Returns:
            dict: Predicted performance for all players
        """
        if self.batting_df is None or self.bowling_df is None:
            logging.error("Cannot generate predictions: No data loaded")
            return None
        
        match_details = {
            'venue': venue
        }
        
        if date:
            match_details['match_date'] = date
        
        # Get all players from both teams
        team1_players = set()
        team2_players = set()
        
        if self.batting_df is not None:
            team1_players.update(self.batting_df[self.batting_df['team'] == team1]['player_name'].unique())
            team2_players.update(self.batting_df[self.batting_df['team'] == team2]['player_name'].unique())
        
        if self.bowling_df is not None:
            team1_players.update(self.bowling_df[self.bowling_df['team'] == team1]['player_name'].unique())
            team2_players.update(self.bowling_df[self.bowling_df['team'] == team2]['player_name'].unique())
        
        predictions = {
            'team1': {'name': team1, 'players': {}},
            'team2': {'name': team2, 'players': {}},
            'match_details': {
                'venue': venue,
                'date': date,
                'prediction_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        # Predict for team1 players against team2
        for player in team1_players:
            player_match_details = {
                **match_details,
                'opposing_team': team2
            }
            player_prediction = self.predict_next_match_performance(player, player_match_details)
            if player_prediction:
                predictions['team1']['players'][player] = player_prediction
        
        # Predict for team2 players against team1
        for player in team2_players:
            player_match_details = {
                **match_details,
                'opposing_team': team1
            }
            player_prediction = self.predict_next_match_performance(player, player_match_details)
            if player_prediction:
                predictions['team2']['players'][player] = player_prediction
        
        return predictions
    
    def export_predictions(self, predictions, format='json'):
        """
        Export predictions to file.
        
        Args:
            predictions: Dictionary of predictions
            format: 'json' or 'csv'
            
        Returns:
            str: Path to the exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(self.models_dir, 'predictions')
        os.makedirs(output_dir, exist_ok=True)
        
        if format == 'json':
            output_path = os.path.join(output_dir, f'match_predictions_{timestamp}.json')
            import json
            with open(output_path, 'w') as f:
                json.dump(predictions, f, indent=4)
            return output_path
        
        elif format == 'csv':
            # Flatten the predictions dict for CSV
            rows = []
            
            for team_key, team_data in [('team1', predictions['team1']), ('team2', predictions['team2'])]:
                team_name = team_data['name']
                for player, prediction in team_data['players'].items():
                    player_row = {
                        'team': team_name,
                        'player': player,
                        'venue': predictions['match_details']['venue']
                    }
                    
                    # Add batting predictions if available
                    if 'batting' in prediction:
                        player_row['predicted_runs'] = prediction['batting'].get('predicted_runs')
                        player_row['batting_performance_class'] = prediction['batting'].get('performance_class')
                    
                    # Add bowling predictions if available
                    if 'bowling' in prediction:
                        player_row['predicted_wickets'] = prediction['bowling'].get('predicted_wickets')
                        player_row['bowling_performance_class'] = prediction['bowling'].get('performance_class')
                    
                    rows.append(player_row)
            
            # Convert to DataFrame and save
            output_path = os.path.join(output_dir, f'match_predictions_{timestamp}.csv')
            pd.DataFrame(rows).to_csv(output_path, index=False)
            return output_path
        
        else:
            logging.error(f"Invalid export format: {format}")
            return None
