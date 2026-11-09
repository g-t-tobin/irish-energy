"""
Test suite for Phase 4.1 analytics implementation
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the modules we're testing
from src.analytics.models import (
    DemandAnalysisResult,
    GenerationAnalysisResult,
    RenewableAnalysisResult,
    WeatherAnalysisResult,
    CorrelationAnalysisResult,
    StatisticalAnalysisResult,
    AnalyticalReport
)
from src.analytics.data_access import GoldDataAccessor
from src.analytics.demand import DemandAnalyzer
from src.analytics.generation import GenerationAnalyzer
from src.analytics.renewables import RenewableAnalyzer
from src.analytics.weather import WeatherAnalyzer
from src.analytics.correlations import CorrelationAnalyzer
from src.analytics.statistics import StatisticalAnalyzer
from src.analytics.reporting import ReportingEngine

# Test data fixtures
DEMAND_TEST_DATA = [
    {
        'timestamp': '2023-01-01',
        'demand_mw': 2086.97,
        'demand_mwh': 1269.08,
        'forecast_mw': 4672.14,
        'forecast_mwh': 1030.42
    },
    {
        'timestamp': '2023-01-02',
        'demand_mw': 2502.79,
        'demand_mwh': 866.66,
        'forecast_mw': 4175.72,
        'forecast_mwh': 600.19
    },
    {
        'timestamp': '2023-01-03',
        'demand_mw': 2085.44,
        'demand_mwh': 532.25,
        'forecast_mw': 3469.54,
        'forecast_mwh': 2429.66
    }
]

GENERATION_TEST_DATA = [
    {
        'timestamp': '2023-01-01',
        'renewable_generation_mw': 1200.0,
        'fossil_generation_mw': 2000.0,
        'nuclear_generation_mw': 2163.58,
        'total_generation_mw': 5363.58
    },
    {
        'timestamp': '2023-01-02',
        'renewable_generation_mw': 1500.0,
        'fossil_generation_mw': 1200.0,
        'nuclear_generation_mw': 1888.25,
        'total_generation_mw': 3088.25
    },
    {
        'timestamp': '2023-01-03',
        'renewable_generation_mw': 1800.0,
        'fossil_generation_mw': 1793.0,
        'nuclear_generation_mw': 1893.00,
        'total_generation_mw': 3593.00
    }
]

WEATHER_TEST_DATA = [
    {
        'timestamp': '2023-01-01',
        'temperature_celsius': 3.42,
        'humidity_percent': 75.0,
        'wind_speed_mps': 3.5,
        'wind_direction_degrees': 180.0,
        'pressure_hpa': 1022.09,
        'precipitation_mm': 9.40
    },
    {
        'timestamp': '2023-01-02',
        'temperature_celsius': 25.84,
        'humidity_percent': 60.0,
        'wind_speed_mps': 4.2,
        'wind_direction_degrees': 90.0,
        'pressure_hpa': 1029.83,
        'precipitation_mm': 11.04
    },
    {
        'timestamp': '2023-01-03',
        'temperature_celsius': 22.55,
        'humidity_percent': 65.0,
        'wind_speed_mps': 3.8,
        'wind_direction_degrees': 270.0,
        'pressure_hpa': 1013.94,
        'precipitation_mm': 12.97
    }
]


def test_models_creation():
    """Test that all model classes can be instantiated"""
    # Test DemandAnalysisResult
    demand_result = DemandAnalysisResult(
        dataset_name='demand',
        date_range=('2023-01-01', '2023-12-31'),
        total_demand_mwh=100000.0,
        average_demand_mw=5000.0,
        min_demand_mw=1000.0,
        max_demand_mw=10000.0,
        median_demand_mw=5000.0,
        peak_demand_periods=[{'date': '2023-01-01', 'demand_mw': 10000.0}],
        daily_profiles={'Monday': 5000.0},
        weekly_patterns={'1': 5000.0},
        monthly_patterns={'January': 5000.0},
        seasonal_patterns={'Winter': 5000.0}
    )
    assert demand_result.dataset_name == 'demand'

    # Test GenerationAnalysisResult
    gen_result = GenerationAnalysisResult(
        dataset_name='generation',
        date_range=('2023-01-01', '2023-12-31'),
        total_generation_mw=100000.0,
        renewable_generation_mw=30000.0,
        fossil_generation_mw=50000.0,
        nuclear_generation_mw=20000.0,
        generation_mix={'renewable': 30.0, 'fossil': 50.0, 'nuclear': 20.0},
        daily_trends={'Monday': 5000.0},
        monthly_trends={'January': 5000.0},
        fuel_type_breakdown={'renewable': 30000.0, 'fossil': 50000.0, 'nuclear': 20000.0}
    )
    assert gen_result.dataset_name == 'generation'

    # Test RenewableAnalysisResult
    renewable_result = RenewableAnalysisResult(
        dataset_name='generation',
        date_range=('2023-01-01', '2023-12-31'),
        renewable_generation_mw=30000.0,
        total_generation_mw=100000.0,
        renewable_share_percentage=30.0,
        renewable_trends={'January': 3000.0},
        seasonal_contribution={'Winter': 3000.0},
        peak_renewable_periods=[{'date': '2023-01-01', 'renewable_generation_mw': 3000.0}]
    )
    assert renewable_result.dataset_name == 'generation'

    # Test WeatherAnalysisResult
    weather_result = WeatherAnalysisResult(
        dataset_name='weather',
        date_range=('2023-01-01', '2023-12-31'),
        avg_temperature_celsius=10.0,
        avg_humidity_percent=65.0,
        avg_wind_speed_mps=3.0,
        avg_precipitation_mm=10.0,
        temperature_trends={'January': 5.0},
        precipitation_trends={'January': 10.0},
        weather_patterns={'avg_temperature': 10.0},
        seasonal_weather={'Winter': 5.0}
    )
    assert weather_result.dataset_name == 'weather'

    # Test CorrelationAnalysisResult
    corr_result = CorrelationAnalysisResult(
        dataset_names=['demand', 'weather'],
        date_range=('2023-01-01', '2023-12-31'),
        pearson_correlation=0.5,
        spearman_correlation=0.4,
        sample_size=365,
        correlation_strength='moderate',
        key_findings=['Test finding 1', 'Test finding 2']
    )
    assert corr_result.dataset_names == ['demand', 'weather']

    # Test StatisticalAnalysisResult
    stat_result = StatisticalAnalysisResult(
        dataset_name='demand',
        date_range=('2023-01-01', '2023-12-31'),
        rolling_averages={'demand_mw': [5000.0]},
        percentage_changes={'demand_mw': [0.0]},
        standard_deviations={'demand_mw': 1000.0},
        interquartile_ranges={'demand_mw': 2000.0},
        trends={'demand_mw': 'stable'},
        outliers=[{'column': 'demand_mw', 'index': 0, 'value': 5000.0}],
        distribution_summary={'demand_mw': {'mean': 5000.0}}
    )
    assert stat_result.dataset_name == 'demand'

    # Test AnalyticalReport
    report = AnalyticalReport(
        report_name='Test Report',
        dataset_references=['demand'],
        date_range=('2023-01-01', '2023-12-31'),
        observation_count=365,
        metrics={'total_demand': 100000.0},
        key_findings=['Test finding'],
        statistical_results={},
        limitations=['Test limitation'],
        data_quality_considerations=['Test consideration'],
        calculation_parameters={}
    )
    assert report.report_name == 'Test Report'


def test_data_access():
    """Test data access utilities"""
    # Create a mock data accessor
    with patch('api.services.data_service.S3GoldDataRetriever') as mock_retriever:
        mock_instance = MagicMock()
        mock_retriever.return_value = mock_instance

        # Mock data responses
        mock_instance.get_demand_data.return_value = DEMAND_TEST_DATA
        mock_instance.get_generation_data.return_value = GENERATION_TEST_DATA
        mock_instance.get_weather_data.return_value = WEATHER_TEST_DATA

        accessor = GoldDataAccessor()

        # Test getting demand data
        demand_df = accessor.get_demand_data()
        assert not demand_df.empty
        assert 'timestamp' in demand_df.columns

        # Test getting generation data
        gen_df = accessor.get_generation_data()
        assert not gen_df.empty
        assert 'timestamp' in gen_df.columns

        # Test getting weather data
        weather_df = accessor.get_weather_data()
        assert not weather_df.empty
        assert 'timestamp' in weather_df.columns

        # Test getting all datasets
        all_datasets = accessor.get_all_datasets()
        assert 'demand' in all_datasets
        assert 'generation' in all_datasets
        assert 'weather' in all_datasets


def test_demand_analysis():
    """Test demand analysis functionality"""
    with patch('src.analytics.data_access.GoldDataAccessor') as mock_accessor:
        mock_instance = MagicMock()
        mock_accessor.return_value = mock_instance

        # Mock demand data
        mock_instance.get_demand_data.return_value = pd.DataFrame(DEMAND_TEST_DATA)

        analyzer = DemandAnalyzer(mock_instance)
        result = analyzer.analyze_demand()

        assert result.dataset_name == 'demand'
        assert result.total_demand_mwh > 0
        assert result.average_demand_mw > 0
        assert result.min_demand_mw >= 0
        assert result.max_demand_mw > 0
        assert result.median_demand_mw >= 0
        assert len(result.peak_demand_periods) > 0
        assert len(result.daily_profiles) > 0
        assert len(result.monthly_patterns) > 0


def test_generation_analysis():
    """Test generation analysis functionality"""
    with patch('src.analytics.data_access.GoldDataAccessor') as mock_accessor:
        mock_instance = MagicMock()
        mock_accessor.return_value = mock_instance

        # Mock generation data
        mock_instance.get_generation_data.return_value = pd.DataFrame(GENERATION_TEST_DATA)

        analyzer = GenerationAnalyzer(mock_instance)
        result = analyzer.analyze_generation()

        assert result.dataset_name == 'generation'
        assert result.total_generation_mw > 0
        assert result.renewable_generation_mw >= 0
        assert result.fossil_generation_mw >= 0
        assert result.nuclear_generation_mw >= 0
        assert len(result.generation_mix) > 0
        assert len(result.fuel_type_breakdown) > 0


def test_renewable_analysis():
    """Test renewable analysis functionality"""
    with patch('src.analytics.data_access.GoldDataAccessor') as mock_accessor:
        mock_instance = MagicMock()
        mock_accessor.return_value = mock_instance

        # Mock generation data
        mock_instance.get_generation_data.return_value = pd.DataFrame(GENERATION_TEST_DATA)

        analyzer = RenewableAnalyzer(mock_instance)
        result = analyzer.analyze_renewables()

        assert result.dataset_name == 'generation'
        assert result.renewable_generation_mw >= 0
        assert result.total_generation_mw > 0
        assert result.renewable_share_percentage >= 0
        assert len(result.renewable_trends) > 0
        assert len(result.seasonal_contribution) > 0
        assert len(result.peak_renewable_periods) > 0


def test_weather_analysis():
    """Test weather analysis functionality"""
    with patch('src.analytics.data_access.GoldDataAccessor') as mock_accessor:
        mock_instance = MagicMock()
        mock_accessor.return_value = mock_instance

        # Mock weather data
        mock_instance.get_weather_data.return_value = pd.DataFrame(WEATHER_TEST_DATA)

        analyzer = WeatherAnalyzer(mock_instance)
        result = analyzer.analyze_weather()

        assert result.dataset_name == 'weather'
        assert result.avg_temperature_celsius >= -50
        assert result.avg_humidity_percent >= 0
        assert result.avg_wind_speed_mps >= 0
        assert result.avg_precipitation_mm >= 0
        assert len(result.temperature_trends) > 0
        assert len(result.weather_patterns) > 0


def test_correlation_analysis():
    """Test correlation analysis functionality"""
    with patch('src.analytics.data_access.GoldDataAccessor') as mock_accessor:
        mock_instance = MagicMock()
        mock_accessor.return_value = mock_instance

        # Mock weather and demand data
        mock_instance.get_all_datasets.return_value = {
            'demand': pd.DataFrame(DEMAND_TEST_DATA),
            'weather': pd.DataFrame(WEATHER_TEST_DATA)
        }

        analyzer = CorrelationAnalyzer(mock_instance)
        result = analyzer.analyze_correlations()

        assert len(result.dataset_names) == 2
        assert result.sample_size > 0
        assert len(result.key_findings) >= 0


def test_statistical_analysis():
    """Test statistical analysis functionality"""
    with patch('src.analytics.data_access.GoldDataAccessor') as mock_accessor:
        mock_instance = MagicMock()
        mock_accessor.return_value = mock_instance

        # Mock demand data
        mock_instance.get_demand_data.return_value = pd.DataFrame(DEMAND_TEST_DATA)

        analyzer = StatisticalAnalyzer(mock_instance)
        result = analyzer.analyze_statistics('demand')

        assert result.dataset_name == 'demand'
        assert len(result.rolling_averages) > 0
        assert len(result.percentage_changes) > 0
        assert len(result.standard_deviations) > 0
        assert len(result.interquartile_ranges) > 0
        assert len(result.trends) > 0
        assert len(result.outliers) >= 0
        assert len(result.distribution_summary) > 0


def test_reporting_engine():
    """Test reporting engine functionality"""
    engine = ReportingEngine()

    # Test demand report generation
    demand_data = {
        'total_demand_mwh': 100000.0,
        'average_demand_mw': 5000.0,
        'min_demand_mw': 1000.0,
        'max_demand_mw': 10000.0,
        'median_demand_mw': 5000.0,
        'observation_count': 365
    }

    report = engine.generate_demand_report(demand_data, '2023-01-01', '2023-12-31')
    assert report.report_name == 'Electricity Demand Analysis Report'
    assert len(report.key_findings) > 0
    assert len(report.limitations) > 0
    assert len(report.data_quality_considerations) > 0


def test_error_handling():
    """Test error handling in analytics"""
    with patch('src.analytics.data_access.GoldDataAccessor') as mock_accessor:
        mock_instance = MagicMock()
        mock_accessor.return_value = mock_instance

        # Mock empty data
        mock_instance.get_demand_data.return_value = pd.DataFrame()

        analyzer = DemandAnalyzer(mock_instance)

        # Should raise ValueError when no data
        try:
            result = analyzer.analyze_demand()
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])