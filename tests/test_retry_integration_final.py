"""
Test the retry logic integration in transformation pipeline
"""

import pytest
from unittest.mock import Mock, patch
from src.transformation.data_transformation import DataTransformer
from src.transformation.retry_logic import RetryConfig, CircuitBreaker


class TestRetryLogicIntegration:
    """Test that retry logic is properly integrated into transformation pipeline"""
    
    def test_retry_manager_creation(self):
        """Test that DataTransformer creates retry manager correctly"""
        transformer = DataTransformer()
        
        assert transformer.retry_config is not None
        assert isinstance(transformer.retry_config, RetryConfig)
        assert transformer.circuit_breaker is not None
        assert isinstance(transformer.circuit_breaker, CircuitBreaker)
        assert transformer.retry_manager is not None
        
    def test_retry_config_values(self):
        """Test that retry config has correct default values"""
        transformer = DataTransformer()
        
        assert transformer.retry_config.max_attempts == 3
        assert transformer.retry_config.base_delay == 1.0
        assert transformer.retry_config.max_delay == 60.0
        assert transformer.retry_config.backoff_factor == 2.0
        
    def test_circuit_breaker_values(self):
        """Test that circuit breaker has correct default values"""
        transformer = DataTransformer()
        
        assert transformer.circuit_breaker.failure_threshold == 5
        assert transformer.circuit_breaker.timeout == 60.0
        
    def test_retry_integration_methods_exist(self):
        """Test that retry integration methods exist"""
        transformer = DataTransformer()
        
        # These methods should exist and be callable
        assert hasattr(transformer, '_execute_with_retry')
        assert hasattr(transformer, 'process_bronze_layer')
        assert hasattr(transformer, 'process_silver_layer')
        assert hasattr(transformer, 'process_gold_layer')
        assert hasattr(transformer, 'process_data_pipeline')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])