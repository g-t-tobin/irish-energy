"""
Analytics package for Irish Energy Analytics Data Platform
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

# Import models for type safety
from src.analytics.models import (
    DemandAnalysisResult,
    GenerationAnalysisResult,
    RenewableAnalysisResult,
    WeatherAnalysisResult,
    CorrelationAnalysisResult,
    StatisticalAnalysisResult,
    AnalyticalReport,
    PeakDemandAnalysisResult
)

# Import data access utilities
from src.analytics.data_access import GoldDataAccessor

__version__ = "1.0.0"