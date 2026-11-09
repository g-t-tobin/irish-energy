"""
Tests for Ingestion Orchestration
"""

import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.ingestion.orchestration import IngestionOrchestrator, IngestionResult
from src.storage.bronze_storage import LocalBronzeStorage
from src.common.config import Config


class TestIngestionResult:

    def test_result_creation(self):
        """Test IngestionResult creation"""
        result = IngestionResult(True, "demand", "2023-01-01")
        assert result.success is True
        assert result.data_type == "demand"
        assert result.date == "2023-01-01"
        assert result.timestamp is not None

        # Test to_dict method
        result_dict = result.to_dict()
        assert "success" in result_dict
        assert "data_type" in result_dict
        assert "date" in result_dict


class TestIngestionOrchestrator:

    def test_init(self):
        """Test orchestrator initialization"""
        config = Config()
        storage = LocalBronzeStorage("./test_storage")

        orchestrator = IngestionOrchestrator(config, storage)
        assert orchestrator is not None
        assert orchestrator.config == config
        assert orchestrator.storage == storage

    def test_generate_ingestion_id(self):
        """Test ingestion ID generation"""
        config = Config()
        storage = LocalBronzeStorage("./test_storage")
        orchestrator = IngestionOrchestrator(config, storage)

        # Generate multiple IDs to ensure uniqueness
        ids = set()
        for _ in range(5):
            ingestion_id = orchestrator._generate_ingestion_id()
            ids.add(ingestion_id)
            assert len(ingestion_id) > 10  # Should be reasonably long
            assert "_" in ingestion_id  # Should contain separator

        # All IDs should be unique
        assert len(ids) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])