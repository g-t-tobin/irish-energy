"""
Tests for Bronze Storage Implementation
"""

import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from src.storage.bronze_storage import (
    LocalBronzeStorage,
    S3BronzeStorage,
    BronzeStorageFactory,
    BronzeStorageError
)
from src.common.config import Config


class TestLocalBronzeStorage:

    def test_init(self):
        """Test local storage initialization"""
        storage = LocalBronzeStorage("./test_storage")
        assert isinstance(storage, LocalBronzeStorage)
        assert storage.base_path.exists()

    def test_build_key(self):
        """Test key generation"""
        storage = LocalBronzeStorage("./test_storage")

        # Test demand data key
        key = storage._build_key("demand", "2023-01-01")
        assert "bronze/demand/2023-01-01/" in key

        # Test weather data key with location
        key = storage._build_key("weather", "2023-01-01", "dublin")
        assert "bronze/weather/dublin/2023-01-01/" in key

        # Test with ingestion ID
        key = storage._build_key("demand", "2023-01-01", ingestion_id="test123")
        assert "test123_raw.json" in key

    def test_store_and_retrieve_raw_data(self):
        """Test storing and retrieving raw data"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = LocalBronzeStorage(tmp_dir)

            test_data = {"test": "data", "timestamp": "2023-01-01T00:00:00Z"}

            # Store data
            success = storage.store_raw_data(test_data, "demand", "2023-01-01")
            assert success is True

            # Retrieve data
            retrieved_data = storage.get_raw_data("demand", "2023-01-01")
            assert retrieved_data is not None
            assert retrieved_data["test"] == "data"


class TestS3BronzeStorage:

    def test_init(self):
        """Test S3 storage initialization"""
        config = Config()
        # Mock boto3 client
        with patch('boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_boto3.return_value = mock_client

            storage = S3BronzeStorage(config)
            assert isinstance(storage, S3BronzeStorage)
            mock_boto3.assert_called_once_with('s3', region_name=config.AWS_REGION)


class TestBronzeStorageFactory:

    def test_create_local_storage(self):
        """Test creating local storage"""
        storage = BronzeStorageFactory.create_storage('local')
        assert isinstance(storage, LocalBronzeStorage)

    def test_create_s3_storage(self):
        """Test creating S3 storage"""
        config = Config()
        with patch('boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_boto3.return_value = mock_client

            storage = BronzeStorageFactory.create_storage('s3', config)
            assert isinstance(storage, S3BronzeStorage)

    def test_create_auto_storage(self):
        """Test creating auto storage (should default to local)"""
        storage = BronzeStorageFactory.create_storage('auto')
        assert isinstance(storage, LocalBronzeStorage)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])