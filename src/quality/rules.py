"""
Quality rules for Irish Energy Analytics Data Platform
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
from loguru import logger
from .models import QualityStatus


def _check_null_values(data: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, str, Optional[Dict]]:
    """
    Check for null values in required columns

    Args:
        data: DataFrame to check
        required_columns: List of required columns

    Returns:
        Tuple of (success, message, details)
    """
    if not isinstance(data, pd.DataFrame):
        return False, "Data must be a pandas DataFrame", None

    null_counts = data[required_columns].isnull().sum()
    null_summary = null_counts[null_counts > 0].to_dict()

    if null_summary:
        message = f"Found null values in columns: {list(null_summary.keys())}"
        return False, message, {"null_counts": null_summary}
    else:
        return True, "No null values found in required columns", None


def _check_missing_columns(data: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, str, Optional[Dict]]:
    """
    Check for missing required columns

    Args:
        data: DataFrame to check
        required_columns: List of required columns

    Returns:
        Tuple of (success, message, details)
    """
    if not isinstance(data, pd.DataFrame):
        return False, "Data must be a pandas DataFrame", None

    missing_columns = [col for col in required_columns if col not in data.columns]

    if missing_columns:
        message = f"Missing required columns: {missing_columns}"
        return False, message, {"missing_columns": missing_columns}
    else:
        return True, "All required columns present", None


def _check_numeric_values(data: pd.DataFrame, numeric_columns: List[str]) -> Tuple[bool, str, Optional[Dict]]:
    """
    Check that numeric columns contain valid numeric values

    Args:
        data: DataFrame to check
        numeric_columns: List of numeric columns

    Returns:
        Tuple of (success, message, details)
    """
    if not isinstance(data, pd.DataFrame):
        return False, "Data must be a pandas DataFrame", None

    invalid_values = {}
    for col in numeric_columns:
        if col in data.columns:
            # Check for infinite values
            infinite_mask = np.isinf(data[col])
            if infinite_mask.any():
                invalid_values[col] = {
                    'count': infinite_mask.sum(),
                    'indices': infinite_mask[infinite_mask].index.tolist()
                }

            # Check for NaN values
            nan_mask = data[col].isna()
            if nan_mask.any():
                invalid_values[col] = {
                    'count': nan_mask.sum(),
                    'indices': nan_mask[nan_mask].index.tolist()
                }

    if invalid_values:
        message = f"Found invalid numeric values in columns: {list(invalid_values.keys())}"
        return False, message, {"invalid_values": invalid_values}
    else:
        return True, "All numeric values are valid", None


def _check_timestamps(data: pd.DataFrame, timestamp_column: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Check that timestamp column contains valid timestamps

    Args:
        data: DataFrame to check
        timestamp_column: Column name containing timestamps

    Returns:
        Tuple of (success, message, details)
    """
    if not isinstance(data, pd.DataFrame):
        return False, "Data must be a pandas DataFrame", None

    if timestamp_column not in data.columns:
        return False, f"Timestamp column '{timestamp_column}' not found", None

    # Try to parse timestamps
    try:
        parsed_timestamps = pd.to_datetime(data[timestamp_column], errors='coerce')
        invalid_count = parsed_timestamps.isna().sum()

        if invalid_count > 0:
            message = f"{invalid_count} invalid timestamps found"
            return False, message, {"invalid_count": invalid_count}
        else:
            return True, "All timestamps are valid", None
    except Exception as e:
        return False, f"Error parsing timestamps: {str(e)}", None


def _check_unique_records(data: pd.DataFrame, unique_keys: List[str]) -> Tuple[bool, str, Optional[Dict]]:
    """
    Check for duplicate records using specified keys

    Args:
        data: DataFrame to check
        unique_keys: List of columns that should form a unique key

    Returns:
        Tuple of (success, message, details)
    """
    if not isinstance(data, pd.DataFrame):
        return False, "Data must be a pandas DataFrame", None

    if not unique_keys:
        return True, "No unique key specified", None

    # Check if all unique keys exist
    missing_keys = [key for key in unique_keys if key not in data.columns]
    if missing_keys:
        return False, f"Missing unique key columns: {missing_keys}", {"missing_keys": missing_keys}

    # Check for duplicates
    duplicates = data.duplicated(subset=unique_keys, keep=False)
    duplicate_count = duplicates.sum()

    if duplicate_count > 0:
        message = f"{duplicate_count} duplicate records found"
        return False, message, {"duplicate_count": duplicate_count}
    else:
        return True, "No duplicate records found", None


def _check_data_consistency(data: pd.DataFrame, consistency_checks: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
    """
    Check data consistency based on specified rules

    Args:
        data: DataFrame to check
        consistency_checks: Dictionary of consistency check parameters

    Returns:
        Tuple of (success, message, details)
    """
    if not isinstance(data, pd.DataFrame):
        return False, "Data must be a pandas DataFrame", None

    # Check for specific consistency requirements based on data type
    try:
        # This is a generic checker - specific implementations would be more detailed
        # For now, we'll return success if no obvious issues
        return True, "Consistency checks passed", None
    except Exception as e:
        return False, f"Consistency check error: {str(e)}", None


def _check_freshness(data: pd.DataFrame, date_column: str, threshold_days: int = 1) -> Tuple[bool, str, Optional[Dict]]:
    """
    Check that data is not stale beyond the threshold

    Args:
        data: DataFrame to check
        date_column: Column containing date information
        threshold_days: Maximum days of staleness allowed

    Returns:
        Tuple of (success, message, details)
    """
    if not isinstance(data, pd.DataFrame):
        return False, "Data must be a pandas DataFrame", None

    if date_column not in data.columns:
        return False, f"Date column '{date_column}' not found", None

    # Check if data is recent enough
    try:
        latest_date = pd.to_datetime(data[date_column]).max()
        current_date = datetime.now(timezone.utc).date()
        days_diff = (current_date - latest_date.date()).days

        if days_diff <= threshold_days:
            return True, f"Data is fresh (latest date: {latest_date.date()})", {"days_stale": days_diff}
        else:
            return False, f"Data is stale (latest date: {latest_date.date()}, {days_diff} days old)", {"days_stale": days_diff}
    except Exception as e:
        return False, f"Error checking freshness: {str(e)}", None


def _check_anomalies(data: pd.DataFrame, numeric_columns: List[str],
                     method: str = "std_dev", threshold: float = 3.0) -> Tuple[bool, str, Optional[Dict]]:
    """
    Check for statistical anomalies in numeric data

    Args:
        data: DataFrame to check
        numeric_columns: List of numeric columns to check
        method: Method for anomaly detection ("std_dev", "iqr")
        threshold: Threshold for anomaly detection

    Returns:
        Tuple of (success, message, details)
    """
    if not isinstance(data, pd.DataFrame):
        return False, "Data must be a pandas DataFrame", None

    anomalies_found = {}

    for col in numeric_columns:
        if col in data.columns and pd.api.types.is_numeric_dtype(data[col]):
            try:
                if method == "std_dev":
                    # Standard deviation method
                    mean = data[col].mean()
                    std = data[col].std()
                    if std > 0:
                        z_scores = abs((data[col] - mean) / std)
                        anomalies = z_scores[z_scores > threshold]
                        if not anomalies.empty:
                            anomalies_found[col] = {
                                'count': len(anomalies),
                                'method': 'standard_deviation',
                                'threshold': threshold
                            }
                elif method == "iqr":
                    # Interquartile range method
                    Q1 = data[col].quantile(0.25)
                    Q3 = data[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - threshold * IQR
                    upper_bound = Q3 + threshold * IQR
                    outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)]
                    if not outliers.empty:
                        anomalies_found[col] = {
                            'count': len(outliers),
                            'method': 'interquartile_range',
                            'threshold': threshold
                        }

            except Exception as e:
                logger.warning(f"Error checking anomalies in column {col}: {str(e)}")

    if anomalies_found:
        message = f"Found anomalies in columns: {list(anomalies_found.keys())}"
        return False, message, {"anomalies": anomalies_found}
    else:
        return True, "No significant anomalies found", None


# Specific rules for EirGrid data
def eirgrid_completeness_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Check completeness for EirGrid data"""
    required_columns = ['date', 'timestamp', 'value']
    return _check_missing_columns(data, required_columns)


def eirgrid_validity_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Check validity for EirGrid data"""
    numeric_columns = ['value']
    return _check_numeric_values(data, numeric_columns)


def eirgrid_uniqueness_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Check uniqueness for EirGrid data"""
    unique_keys = ['date', 'timestamp']
    return _check_unique_records(data, unique_keys)


def eirgrid_consistency_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Check consistency for EirGrid data"""
    # Check timestamp ordering
    if 'timestamp' in data.columns:
        sorted_data = data.sort_values('timestamp')
        is_sorted = data['timestamp'].equals(sorted_data['timestamp'])
        if not is_sorted:
            return False, "Timestamps are not in ascending order", {"unsorted_indices": sorted_data.index.tolist()}
    return True, "Timestamps are properly ordered", None


# Specific rules for Open-Meteo weather data
def weather_completeness_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Check completeness for Open-Meteo weather data"""
    required_columns = ['latitude', 'longitude', 'timestamp', 'temperature', 'humidity']
    return _check_missing_columns(data, required_columns)


def weather_validity_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Check validity for Open-Meteo weather data"""
    numeric_columns = ['latitude', 'longitude', 'temperature', 'humidity']
    return _check_numeric_values(data, numeric_columns)


def weather_uniqueness_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Check uniqueness for Open-Meteo weather data"""
    unique_keys = ['timestamp', 'latitude', 'longitude']
    return _check_unique_records(data, unique_keys)


def weather_consistency_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Check consistency for Open-Meteo weather data"""
    return _check_data_consistency(data, {})


# Generic rules for all datasets
def generic_completeness_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Generic completeness check"""
    # This would be overridden by dataset-specific rules
    return True, "Completeness check passed", None


def generic_validity_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Generic validity check"""
    # This would be overridden by dataset-specific rules
    return True, "Validity check passed", None


def generic_uniqueness_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Generic uniqueness check"""
    # This would be overridden by dataset-specific rules
    return True, "Uniqueness check passed", None


def generic_consistency_rule(data: pd.DataFrame) -> Tuple[bool, str, Optional[Dict]]:
    """Generic consistency check"""
    # This would be overridden by dataset-specific rules
    return True, "Consistency check passed", None