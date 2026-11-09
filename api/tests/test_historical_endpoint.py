import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pandas as pd
from io import BytesIO
from fastapi.testclient import TestClient
from api.main import app
from api.services.data_service import S3GoldDataRetriever

# Create TestClient correctly
client = TestClient(app)

def test_historical_endpoint_valid_dates():
    """Test that /historical endpoint works with valid date range"""
    response = client.get("/historical?start_date=2023-01-01&end_date=2023-01-02")
    assert response.status_code == 200
    data = response.json()
    assert "demand" in data
    assert "weather" in data
    assert "generation" in data
    assert "date_range" in data
    assert data["date_range"]["start"] == "2023-01-01"
    assert data["date_range"]["end"] == "2023-01-02"

def test_historical_endpoint_invalid_date_format():
    """Test that /historical endpoint rejects invalid date formats"""
    response = client.get("/historical?start_date=invalid&end_date=2023-01-02")
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]

def test_historical_endpoint_start_after_end():
    """Test that /historical endpoint rejects start date after end date"""
    response = client.get("/historical?start_date=2023-01-02&end_date=2023-01-01")
    assert response.status_code == 400
    assert "Start date must be before or equal to end date" in response.json()["detail"]

def test_historical_endpoint_missing_parameters():
    """Test that /historical endpoint requires both date parameters"""
    response = client.get("/historical?start_date=2023-01-01")
    assert response.status_code == 422  # Validation error

@patch('api.services.data_service.S3GoldDataRetriever._read_parquet_from_s3')
def test_data_service_get_demand_data_with_dates(mock_read_parquet):
    """Test data service demand data retrieval with date range"""
    # Setup mock to return sample data
    mock_df = pd.DataFrame({
        'timestamp': ['2023-01-01T00:00:00'],
        'demand_mw': [100.0],
        'demand_mwh': [2400.0],
        'forecast_mw': [110.0],
        'forecast_mwh': [2640.0]
    })
    mock_read_parquet.return_value = mock_df

    retriever = S3GoldDataRetriever()
    result = retriever.get_demand_data("2023-01-01", "2023-01-02")

    assert isinstance(result, list)
    assert len(result) == 1

@patch('api.services.data_service.S3GoldDataRetriever._read_parquet_from_s3')
def test_data_service_get_weather_data_with_dates(mock_read_parquet):
    """Test data service weather data retrieval with date range"""
    # Setup mock to return sample data
    mock_df = pd.DataFrame({
        'timestamp': ['2023-01-01T00:00:00'],
        'temperature_celsius': [15.0],
        'humidity_percent': [60.0],
        'wind_speed_mps': [3.0],
        'wind_direction_degrees': [180.0],
        'pressure_hpa': [1013.0],
        'precipitation_mm': [0.0]
    })
    mock_read_parquet.return_value = mock_df

    retriever = S3GoldDataRetriever()
    result = retriever.get_weather_data("2023-01-01", "2023-01-02")

    assert isinstance(result, list)
    assert len(result) == 1

@patch('api.services.data_service.S3GoldDataRetriever._read_parquet_from_s3')
def test_data_service_get_generation_data_with_dates(mock_read_parquet):
    """Test data service generation data retrieval with date range"""
    # Setup mock to return sample data
    mock_df = pd.DataFrame({
        'timestamp': ['2023-01-01T00:00:00'],
        'renewable_generation_mw': [50.0],
        'fossil_generation_mw': [30.0],
        'nuclear_generation_mw': [20.0],
        'total_generation_mw': [100.0]
    })
    mock_read_parquet.return_value = mock_df

    retriever = S3GoldDataRetriever()
    result = retriever.get_generation_data("2023-01-01", "2023-01-02")

    assert isinstance(result, list)
    assert len(result) == 1

@patch('api.services.data_service.S3GoldDataRetriever._get_s3_keys_for_date_range')
@patch('api.services.data_service.S3GoldDataRetriever._read_parquet_from_s3')
def test_data_service_get_demand_data_multiple_partitions(mock_read_parquet, mock_get_keys):
    """Test data service demand data retrieval with multiple partitions"""
    # Setup mocks
    mock_get_keys.return_value = [
        "demand/2023-01-01.parquet",
        "demand/2023-01-02.parquet"
    ]

    mock_df1 = pd.DataFrame({'timestamp': ['2023-01-01T00:00:00'], 'demand_mw': [100.0]})
    mock_df2 = pd.DataFrame({'timestamp': ['2023-01-02T00:00:00'], 'demand_mw': [110.0]})

    def side_effect(key):
        if key == "demand/2023-01-01.parquet":
            return mock_df1
        elif key == "demand/2023-01-02.parquet":
            return mock_df2
        else:
            raise Exception("Unexpected key")

    mock_read_parquet.side_effect = side_effect

    retriever = S3GoldDataRetriever()
    result = retriever.get_demand_data("2023-01-01", "2023-01-02")

    assert isinstance(result, list)
    assert len(result) == 2