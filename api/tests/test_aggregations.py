#!/usr/bin/env python3
"""
Tests for daily aggregation functions in Irish Energy Analytics API.
"""

import pytest
from datetime import datetime
from api.models import (
    DemandData, WeatherData, GenerationData,
    FrontendDemandData, FrontendWeatherData, FrontendGenerationData
)
from api.aggregations import (
    aggregate_demand_by_day,
    aggregate_weather_by_day,
    aggregate_generation_by_day
)


def test_aggregate_demand_by_day_single_observation():
    """Test demand aggregation with single observation per day"""
    # Create sample data with one observation per day
    api_data = [
        DemandData(
            timestamp=datetime(2023, 1, 1),
            demand_mw=1000.0,
            demand_mwh=500.0,
            forecast_mw=1100.0,
            forecast_mwh=550.0
        ),
        DemandData(
            timestamp=datetime(2023, 1, 2),
            demand_mw=1200.0,
            demand_mwh=600.0,
            forecast_mw=1300.0,
            forecast_mwh=650.0
        )
    ]

    result = aggregate_demand_by_day(api_data)

    # Should have 2 records
    assert len(result) == 2

    # Check first record
    record1 = next(r for r in result if r.date == "2023-01-01")
    assert record1.total_demand == 1000.0
    assert record1.avg_demand == 500.0
    assert record1.min_demand == 1100.0
    assert record1.max_demand == 550.0

    # Check second record
    record2 = next(r for r in result if r.date == "2023-01-02")
    assert record2.total_demand == 1200.0
    assert record2.avg_demand == 600.0
    assert record2.min_demand == 1300.0
    assert record2.max_demand == 650.0


def test_aggregate_demand_by_day_multiple_observations():
    """Test demand aggregation with multiple observations per day"""
    # Create sample data with multiple observations on same day
    api_data = [
        DemandData(
            timestamp=datetime(2023, 1, 1, 10, 0),
            demand_mw=1000.0,
            demand_mwh=500.0,
            forecast_mw=1100.0,
            forecast_mwh=550.0
        ),
        DemandData(
            timestamp=datetime(2023, 1, 1, 14, 0),
            demand_mw=1200.0,
            demand_mwh=600.0,
            forecast_mw=1300.0,
            forecast_mwh=650.0
        ),
        DemandData(
            timestamp=datetime(2023, 1, 2, 10, 0),
            demand_mw=1500.0,
            demand_mwh=700.0,
            forecast_mw=1600.0,
            forecast_mwh=750.0
        )
    ]

    result = aggregate_demand_by_day(api_data)

    # Should have 2 records (one per day)
    assert len(result) == 2

    # Check first day (should aggregate values)
    record1 = next(r for r in result if r.date == "2023-01-01")
    assert record1.total_demand == 1200.0  # Max of 1000 and 1200
    assert record1.avg_demand == 550.0  # Average of 500 and 600
    assert record1.min_demand == 1100.0  # Min of 1100 and 1300
    assert record1.max_demand == 650.0  # Max of 550 and 650

    # Check second day
    record2 = next(r for r in result if r.date == "2023-01-02")
    assert record2.total_demand == 1500.0
    assert record2.avg_demand == 700.0
    assert record2.min_demand == 1600.0
    assert record2.max_demand == 750.0


def test_aggregate_weather_by_day():
    """Test weather aggregation with multiple observations per day"""
    # Create sample data with multiple observations on same day
    api_data = [
        WeatherData(
            timestamp=datetime(2023, 1, 1, 10, 0),
            temperature_celsius=15.0,
            humidity_percent=70.0,
            wind_speed_mps=5.0,
            wind_direction_degrees=180.0,
            pressure_hpa=1013.0,
            precipitation_mm=0.0
        ),
        WeatherData(
            timestamp=datetime(2023, 1, 1, 14, 0),
            temperature_celsius=18.0,
            humidity_percent=75.0,
            wind_speed_mps=6.0,
            wind_direction_degrees=190.0,
            pressure_hpa=1012.0,
            precipitation_mm=0.5
        ),
        WeatherData(
            timestamp=datetime(2023, 1, 1, 18, 0),
            temperature_celsius=16.0,
            humidity_percent=72.0,
            wind_speed_mps=4.0,
            wind_direction_degrees=170.0,
            pressure_hpa=1014.0,
            precipitation_mm=0.2
        ),
        WeatherData(
            timestamp=datetime(2023, 1, 2, 10, 0),
            temperature_celsius=20.0,
            humidity_percent=65.0,
            wind_speed_mps=3.0,
            wind_direction_degrees=200.0,
            pressure_hpa=1015.0,
            precipitation_mm=0.1
        )
    ]

    result = aggregate_weather_by_day(api_data)

    # Should have 2 records (one per day)
    assert len(result) == 2

    # Check first day (should aggregate values)
    record1 = next(r for r in result if r.date == "2023-01-01")
    assert record1.avg_temperature == pytest.approx(16.33, rel=0.01)  # (15+18+16)/3
    assert record1.min_temperature == 15.0
    assert record1.max_temperature == 18.0
    assert record1.avg_humidity == pytest.approx(72.33, rel=0.01)  # (70+75+72)/3

    # Check second day
    record2 = next(r for r in result if r.date == "2023-01-02")
    assert record2.avg_temperature == 20.0
    assert record2.min_temperature == 20.0
    assert record2.max_temperature == 20.0
    assert record2.avg_humidity == 65.0


def test_aggregate_generation_by_day():
    """Test generation aggregation with multiple observations per day"""
    # Create sample data with multiple observations on same day
    api_data = [
        GenerationData(
            timestamp=datetime(2023, 1, 1, 10, 0),
            renewable_generation_mw=1000.0,
            fossil_generation_mw=2000.0,
            nuclear_generation_mw=500.0,
            total_generation_mw=3500.0
        ),
        GenerationData(
            timestamp=datetime(2023, 1, 1, 14, 0),
            renewable_generation_mw=1200.0,
            fossil_generation_mw=2200.0,
            nuclear_generation_mw=600.0,
            total_generation_mw=3800.0
        ),
        GenerationData(
            timestamp=datetime(2023, 1, 2, 10, 0),
            renewable_generation_mw=1100.0,
            fossil_generation_mw=2100.0,
            nuclear_generation_mw=550.0,
            total_generation_mw=3750.0
        )
    ]

    result = aggregate_generation_by_day(api_data)

    # Should have 6 records (2 days × 3 fuel types)
    assert len(result) == 6

    # Check first day renewable
    renewable_record = next(r for r in result if r.date == "2023-01-01" and r.fuel_type == "renewable")
    assert renewable_record.total_generation == 1200.0  # Peak
    assert renewable_record.avg_generation == 1100.0  # Average

    # Check first day fossil
    fossil_record = next(r for r in result if r.date == "2023-01-01" and r.fuel_type == "fossil")
    assert fossil_record.total_generation == 2200.0  # Peak
    assert fossil_record.avg_generation == 2100.0  # Average

    # Check first day nuclear
    nuclear_record = next(r for r in result if r.date == "2023-01-01" and r.fuel_type == "nuclear")
    assert nuclear_record.total_generation == 600.0  # Peak
    assert nuclear_record.avg_generation == 550.0  # Average





def test_aggregate_empty_dataset():
    """Test aggregation with empty dataset"""
    result = aggregate_demand_by_day([])
    assert len(result) == 0

    result = aggregate_weather_by_day([])
    assert len(result) == 0

    result = aggregate_generation_by_day([])
    assert len(result) == 0


def test_aggregate_with_zero_values():
    """Test aggregation with zero values (should be treated as valid)"""
    api_data = [
        GenerationData(
            timestamp=datetime(2023, 1, 1, 10, 0),
            renewable_generation_mw=0.0,
            fossil_generation_mw=2000.0,
            nuclear_generation_mw=500.0,
            total_generation_mw=2500.0
        )
    ]

    result = aggregate_generation_by_day(api_data)

    # Should include zero values
    assert len(result) == 3
    zero_record = next(r for r in result if r.fuel_type == "renewable")
    assert zero_record.total_generation == 0.0
    assert zero_record.avg_generation == 0.0


def test_aggregate_different_timezones():
    """Test aggregation handles different timestamps correctly"""
    # Test with various times on the same day
    api_data = [
        WeatherData(
            timestamp=datetime(2023, 1, 1, 0, 0),  # Midnight
            temperature_celsius=10.0,
            humidity_percent=60.0,
            wind_speed_mps=3.0,
            wind_direction_degrees=0.0,
            pressure_hpa=1013.0,
            precipitation_mm=0.0
        ),
        WeatherData(
            timestamp=datetime(2023, 1, 1, 23, 59),  # Just before midnight
            temperature_celsius=12.0,
            humidity_percent=65.0,
            wind_speed_mps=4.0,
            wind_direction_degrees=180.0,
            pressure_hpa=1012.0,
            precipitation_mm=0.1
        )
    ]

    result = aggregate_weather_by_day(api_data)

    # Should group into same day
    assert len(result) == 1
    record = result[0]
    assert record.date == "2023-01-01"
    assert record.avg_temperature == pytest.approx(11.0, rel=0.01)  # (10+12)/2