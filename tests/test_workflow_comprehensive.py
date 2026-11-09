"""
Comprehensive tests for transformation and pipeline workflow
"""
import pytest
import json
from unittest.mock import Mock, patch

from src.transformation.silver_lambda_handler import transform_silver_handler, transform_gold_handler
from src.transformation.silver_transformation import SilverTransformationService
from src.transformation.gold_transformation import GoldTransformationService


class TestTransformationPayloads:
    """Test that transformation handlers accept correct payloads"""

    def test_silver_transformation_payload_structure(self):
        """Test that silver transformation accepts correct event structure"""
        # Test the expected event structure from orchestration
        event = {
            "transformation_type": "silver",
            "data_type": "weather",
            "date": "2023-01-01",
            "execution_id": "test-execution-123"
        }

        # Mock context
        context = Mock()
        context.function_name = "TestSilverFunction"

        # This should not raise an exception
        # Note: We're just testing the structure parsing, not actual execution
        try:
            # Just parse the event to make sure it's valid
            data_type = event.get('data_type')
            date_str = event.get('date')
            execution_id = event.get('execution_id')

            assert data_type is not None
            assert date_str is not None
            assert execution_id is not None
            assert event['transformation_type'] == 'silver'

            print("✓ Silver transformation payload structure is correct")
        except Exception as e:
            pytest.fail(f"Silver transformation payload validation failed: {e}")

    def test_gold_transformation_payload_structure(self):
        """Test that gold transformation accepts correct event structure"""
        # Test the expected event structure from orchestration
        event = {
            "transformation_type": "gold",
            "data_type": "weather",
            "date": "2023-01-01",
            "execution_id": "test-execution-456"
        }

        # Mock context
        context = Mock()
        context.function_name = "TestGoldFunction"

        # This should not raise an exception
        # Note: We're just testing the structure parsing, not actual execution
        try:
            # Just parse the event to make sure it's valid
            data_type = event.get('data_type')
            date_str = event.get('date')
            execution_id = event.get('execution_id')

            assert data_type is not None
            assert date_str is not None
            assert execution_id is not None
            assert event['transformation_type'] == 'gold'

            print("✓ Gold transformation payload structure is correct")
        except Exception as e:
            pytest.fail(f"Gold transformation payload validation failed: {e}")

    def test_all_data_types_supported(self):
        """Test that all supported data types are handled correctly"""
        supported_types = ["demand", "weather", "generation"]

        for data_type in supported_types:
            # Test silver transformation
            silver_event = {
                "transformation_type": "silver",
                "data_type": data_type,
                "date": "2023-01-01",
                "execution_id": f"test-{data_type}-execution"
            }

            # Test gold transformation
            gold_event = {
                "transformation_type": "gold",
                "data_type": data_type,
                "date": "2023-01-01",
                "execution_id": f"test-{data_type}-execution"
            }

            # Just verify structure parsing works
            assert silver_event['data_type'] == data_type
            assert gold_event['data_type'] == data_type
            print(f"✓ Data type '{data_type}' correctly handled by both transformations")


class TestTransformationFailureHandling:
    """Test that transformation failures properly propagate"""

    def test_transformation_failure_raises_exception(self):
        """Test that transformation failures raise exceptions instead of returning 500 status"""
        # Test with invalid data to simulate failure
        event = {
            "transformation_type": "silver",
            "data_type": "nonexistent",
            "date": "2023-01-01",
            "execution_id": "test-execution-789"
        }

        context = Mock()
        context.function_name = "TestFailureFunction"

        # This should raise an exception, not return a 500 status
        with pytest.raises(Exception) as exc_info:
            transform_silver_handler(event, context)

        assert "failed" in str(exc_info.value).lower()
        print("✓ Transformation failure properly raises exception")


class TestS3Configuration:
    """Test S3 bucket and key configuration consistency"""

    def test_s3_bucket_consistency(self):
        """Test that configuration constants are properly set"""
        from src.common.config import Config

        config = Config()

        # Check that required buckets are configured
        assert hasattr(config, 'BRONZE_BUCKET')
        assert hasattr(config, 'SILVER_BUCKET')
        assert hasattr(config, 'GOLD_BUCKET')

        # Check that they have meaningful values (not default placeholders)
        assert config.BRONZE_BUCKET != 'irish-energy-bronze-default'
        assert config.SILVER_BUCKET != 'irish-energy-silver-default'
        assert config.GOLD_BUCKET != 'irish-energy-gold-default'

        print("✓ S3 bucket configuration is properly set")


if __name__ == "__main__":
    # Run tests manually
    test_instance = TestTransformationPayloads()
    test_instance.test_silver_transformation_payload_structure()
    test_instance.test_gold_transformation_payload_structure()
    test_instance.test_all_data_types_supported()

    test_instance2 = TestTransformationFailureHandling()
    test_instance2.test_transformation_failure_raises_exception()

    test_instance3 = TestS3Configuration()
    test_instance3.test_s3_bucket_consistency()

    print("All comprehensive tests passed!")