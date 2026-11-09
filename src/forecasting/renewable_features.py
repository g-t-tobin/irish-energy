"""
Renewable energy feature engineering for forecasting
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from src.forecasting.features import FeatureEngineer

class RenewableFeatureEngineer:
    """Engineer features for renewable energy forecasting models"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = []

    def engineer_features(self, data: pd.DataFrame,
                         include_weather: bool = True,
                         include_lagged: bool = True,
                         include_rolling: bool = True,
                         generation_category: str = "renewable") -> pd.DataFrame:
        """
        Engineer features from raw data for renewable forecasting

        Args:
            data: DataFrame with timestamp and target variables
            include_weather: Whether to include weather features
            include_lagged: Whether to include lagged features
            include_rolling: Whether to include rolling window features
            generation_category: Type of generation ('wind', 'solar', 'renewable_total')

        Returns:
            DataFrame with engineered features
        """
        df = data.copy()

        # Basic calendar features
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        df['quarter'] = df['timestamp'].dt.quarter
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

        # Seasonal indicators
        df['season'] = df['month'].apply(lambda x: 'Winter' if x in [12,1,2] else
                                        'Spring' if x in [3,4,5] else
                                        'Summer' if x in [6,7,8] else 'Fall')

        # Encode season as numeric
        season_mapping = {'Winter': 0, 'Spring': 1, 'Summer': 2, 'Fall': 3}
        df['season_encoded'] = df['season'].map(season_mapping)

        # Lagged features (if available)
        if include_lagged:
            # Use appropriate generation column based on category
            gen_column = self._get_generation_column(generation_category)
            if gen_column in df.columns:
                # Previous day generation
                df[f'{gen_column}_lag_1'] = df[gen_column].shift(1)
                # Previous week generation
                df[f'{gen_column}_lag_7'] = df[gen_column].shift(7)
                # Two weeks ago
                df[f'{gen_column}_lag_14'] = df[gen_column].shift(14)

        # Rolling window features (if available)
        if include_rolling:
            gen_column = self._get_generation_column(generation_category)
            if gen_column in df.columns:
                # 7-day rolling mean
                df[f'{gen_column}_rolling_mean_7'] = df[gen_column].rolling(window=7, min_periods=1).mean()
                # 7-day rolling std
                df[f'{gen_column}_rolling_std_7'] = df[gen_column].rolling(window=7, min_periods=1).std()
                # 30-day rolling mean
                df[f'{gen_column}_rolling_mean_30'] = df[gen_column].rolling(window=30, min_periods=1).mean()
                # 30-day rolling std
                df[f'{gen_column}_rolling_std_30'] = df[gen_column].rolling(window=30, min_periods=1).std()

        # Weather features (if available)
        if include_weather:
            if 'wind_speed_mps' in df.columns:
                df['wind_speed_lag_1'] = df['wind_speed_mps'].shift(1)
                df['wind_speed_rolling_mean_7'] = df['wind_speed_mps'].rolling(window=7, min_periods=1).mean()
                df['wind_speed_rolling_std_7'] = df['wind_speed_mps'].rolling(window=7, min_periods=1).std()

            if 'temperature_celsius' in df.columns:
                df['temperature_lag_1'] = df['temperature_celsius'].shift(1)
                df['temperature_rolling_mean_7'] = df['temperature_celsius'].rolling(window=7, min_periods=1).mean()
                df['temperature_rolling_std_7'] = df['temperature_celsius'].rolling(window=7, min_periods=1).std()

            if 'humidity_percent' in df.columns:
                df['humidity_lag_1'] = df['humidity_percent'].shift(1)
                df['humidity_rolling_mean_7'] = df['humidity_percent'].rolling(window=7, min_periods=1).mean()
                df['humidity_rolling_std_7'] = df['humidity_percent'].rolling(window=7, min_periods=1).std()

            if 'precipitation_mm' in df.columns:
                df['precipitation_lag_1'] = df['precipitation_mm'].shift(1)
                df['precipitation_rolling_mean_7'] = df['precipitation_mm'].rolling(window=7, min_periods=1).mean()
                df['precipitation_rolling_std_7'] = df['precipitation_mm'].rolling(window=7, min_periods=1).std()

        # Drop rows with NaN values from lagging/rolling operations
        df = df.dropna()

        # Store feature columns for later use
        self.feature_columns = [col for col in df.columns if col not in ['timestamp', 'renewable_generation_mw', 'fossil_generation_mw', 'nuclear_generation_mw', 'total_generation_mw']]

        return df

    def prepare_features_for_prediction(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for prediction (remove target variable)
        """
        # Remove target variables if present
        target_columns = ['renewable_generation_mw', 'fossil_generation_mw', 'nuclear_generation_mw', 'total_generation_mw']
        for col in target_columns:
            if col in data.columns:
                data = data.drop(col, axis=1)

        # Remove timestamp if present
        if 'timestamp' in data.columns:
            data = data.drop('timestamp', axis=1)

        return data

    def get_feature_columns(self) -> List[str]:
        """Return the list of engineered feature columns"""
        return self.feature_columns.copy()

    def scale_features(self, X: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Scale features using StandardScaler

        Args:
            X: DataFrame of features
            fit: Whether to fit the scaler or just transform

        Returns:
            Scaled DataFrame
        """
        if fit:
            X_scaled = pd.DataFrame(
                self.scaler.fit_transform(X),
                columns=X.columns,
                index=X.index
            )
        else:
            X_scaled = pd.DataFrame(
                self.scaler.transform(X),
                columns=X.columns,
                index=X.index
            )
        return X_scaled

    def _get_generation_column(self, generation_category: str) -> str:
        """Get the appropriate generation column name based on category"""
        category_mapping = {
            'wind': 'renewable_generation_mw',  # Assume renewable includes wind
            'solar': 'renewable_generation_mw',  # Assume renewable includes solar
            'renewable_total': 'renewable_generation_mw'
        }
        return category_mapping.get(generation_category, 'renewable_generation_mw')