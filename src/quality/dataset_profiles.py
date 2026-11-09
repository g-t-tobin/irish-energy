"""
Dataset-specific quality profiles for Irish Energy Analytics Data Platform
"""
from typing import Dict, List, Any
from .models import QualityRule
from .rules import (
    eirgrid_completeness_rule, eirgrid_validity_rule, eirgrid_uniqueness_rule, eirgrid_consistency_rule,
    weather_completeness_rule, weather_validity_rule, weather_uniqueness_rule, weather_consistency_rule,
    generic_completeness_rule, generic_validity_rule, generic_uniqueness_rule, generic_consistency_rule
)


class DatasetProfile:
    """
    Defines quality rules and characteristics for specific datasets
    """

    def __init__(self, name: str, data_type: str, required_columns: List[str],
                 unique_keys: List[str], freshness_threshold: int = 1):
        self.name = name
        self.data_type = data_type
        self.required_columns = required_columns
        self.unique_keys = unique_keys
        self.freshness_threshold = freshness_threshold
        self.rules: List[QualityRule] = []

    def add_rule(self, rule: QualityRule) -> None:
        """Add a quality rule to this dataset profile"""
        self.rules.append(rule)

    def get_rules(self) -> List[QualityRule]:
        """Get all rules for this dataset profile"""
        return self.rules


# Predefined dataset profiles
EIRGRID_DEMAND_PROFILE = DatasetProfile(
    name="EirGrid Demand",
    data_type="demand",
    required_columns=['date', 'timestamp', 'value'],
    unique_keys=['date', 'timestamp'],
    freshness_threshold=1
)

EIRGRID_GENERATION_PROFILE = DatasetProfile(
    name="EirGrid Generation",
    data_type="generation",
    required_columns=['date', 'timestamp', 'value', 'fuel_type'],
    unique_keys=['date', 'timestamp', 'fuel_type'],
    freshness_threshold=1
)

OPENMETEO_WEATHER_PROFILE = DatasetProfile(
    name="Open-Meteo Weather",
    data_type="weather",
    required_columns=['latitude', 'longitude', 'timestamp', 'temperature', 'humidity'],
    unique_keys=['timestamp', 'latitude', 'longitude'],
    freshness_threshold=1
)

# Add rules to profiles
# EirGrid Demand rules
EIRGRID_DEMAND_PROFILE.add_rule({
    'name': 'demand_completeness',
    'severity': 'critical',
    'description': 'Check for required demand data fields',
    'check_function': eirgrid_completeness_rule,
    'weight': 1.0
})

EIRGRID_DEMAND_PROFILE.add_rule({
    'name': 'demand_validity',
    'severity': 'critical',
    'description': 'Check for valid numeric demand values',
    'check_function': eirgrid_validity_rule,
    'weight': 1.0
})

EIRGRID_DEMAND_PROFILE.add_rule({
    'name': 'demand_uniqueness',
    'severity': 'critical',
    'description': 'Check for unique timestamp entries',
    'check_function': eirgrid_uniqueness_rule,
    'weight': 1.0
})

EIRGRID_DEMAND_PROFILE.add_rule({
    'name': 'demand_consistency',
    'severity': 'warning',
    'description': 'Check timestamp ordering consistency',
    'check_function': eirgrid_consistency_rule,
    'weight': 0.8
})

# EirGrid Generation rules
EIRGRID_GENERATION_PROFILE.add_rule({
    'name': 'generation_completeness',
    'severity': 'critical',
    'description': 'Check for required generation data fields',
    'check_function': eirgrid_completeness_rule,
    'weight': 1.0
})

EIRGRID_GENERATION_PROFILE.add_rule({
    'name': 'generation_validity',
    'severity': 'critical',
    'description': 'Check for valid numeric generation values',
    'check_function': eirgrid_validity_rule,
    'weight': 1.0
})

EIRGRID_GENERATION_PROFILE.add_rule({
    'name': 'generation_uniqueness',
    'severity': 'critical',
    'description': 'Check for unique timestamp and fuel type combinations',
    'check_function': eirgrid_uniqueness_rule,
    'weight': 1.0
})

EIRGRID_GENERATION_PROFILE.add_rule({
    'name': 'generation_consistency',
    'severity': 'warning',
    'description': 'Check timestamp ordering consistency',
    'check_function': eirgrid_consistency_rule,
    'weight': 0.8
})

# Open-Meteo Weather rules
OPENMETEO_WEATHER_PROFILE.add_rule({
    'name': 'weather_completeness',
    'severity': 'critical',
    'description': 'Check for required weather data fields',
    'check_function': weather_completeness_rule,
    'weight': 1.0
})

OPENMETEO_WEATHER_PROFILE.add_rule({
    'name': 'weather_validity',
    'severity': 'critical',
    'description': 'Check for valid numeric weather values',
    'check_function': weather_validity_rule,
    'weight': 1.0
})

OPENMETEO_WEATHER_PROFILE.add_rule({
    'name': 'weather_uniqueness',
    'severity': 'critical',
    'description': 'Check for unique timestamp and location combinations',
    'check_function': weather_uniqueness_rule,
    'weight': 1.0
})

OPENMETEO_WEATHER_PROFILE.add_rule({
    'name': 'weather_consistency',
    'severity': 'warning',
    'description': 'Check data consistency',
    'check_function': weather_consistency_rule,
    'weight': 0.8
})

# Generic rules for all datasets
GENERIC_PROFILE = DatasetProfile(
    name="Generic Dataset",
    data_type="generic",
    required_columns=[],
    unique_keys=[],
    freshness_threshold=1
)

GENERIC_PROFILE.add_rule({
    'name': 'generic_completeness',
    'severity': 'critical',
    'description': 'Check for required dataset fields',
    'check_function': generic_completeness_rule,
    'weight': 1.0
})

GENERIC_PROFILE.add_rule({
    'name': 'generic_validity',
    'severity': 'critical',
    'description': 'Check for valid data types',
    'check_function': generic_validity_rule,
    'weight': 1.0
})

GENERIC_PROFILE.add_rule({
    'name': 'generic_uniqueness',
    'severity': 'warning',
    'description': 'Check for unique records',
    'check_function': generic_uniqueness_rule,
    'weight': 0.8
})

GENERIC_PROFILE.add_rule({
    'name': 'generic_consistency',
    'severity': 'warning',
    'description': 'Check data consistency',
    'check_function': generic_consistency_rule,
    'weight': 0.8
})

# Profile registry
DATASET_PROFILES = {
    'eirgrid_demand': EIRGRID_DEMAND_PROFILE,
    'eirgrid_generation': EIRGRID_GENERATION_PROFILE,
    'openmeteo_weather': OPENMETEO_WEATHER_PROFILE,
    'generic': GENERIC_PROFILE
}


def get_dataset_profile(dataset_name: str) -> DatasetProfile:
    """
    Get dataset profile by name

    Args:
        dataset_name: Name of the dataset

    Returns:
        DatasetProfile: Matching dataset profile
    """
    # Map common dataset names to profiles
    profile_map = {
        'demand': 'eirgrid_demand',
        'generation': 'eirgrid_generation',
        'weather': 'openmeteo_weather'
    }

    # Get profile name
    profile_name = profile_map.get(dataset_name, dataset_name)

    # Return profile or generic if not found
    return DATASET_PROFILES.get(profile_name, DATASET_PROFILES['generic'])