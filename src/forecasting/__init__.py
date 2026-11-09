"""
Forecasting package for Irish Energy Analytics Data Platform
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

# Import data access utilities
from src.forecasting.data_access import ForecastingDataAccessor

# Import models and services
from src.forecasting.models import (
    ForecastResult,
    ModelEvaluationResult,
    ModelMetadata,
    ForecastModel
)

# Import feature engineering
from src.forecasting.features import FeatureEngineer

# Import baselines and ML models
from src.forecasting.baselines import BaselineForecaster
from src.forecasting.training import MLForecastModel
from src.forecasting.evaluation import ModelEvaluator, Backtester
from src.forecasting.forecasting_service import ForecastingService

__version__ = "1.0.0"