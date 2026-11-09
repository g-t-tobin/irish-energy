"""
Test file for the reconciliation framework
"""
import pytest
from datetime import datetime, date
from src.reconciliation.models import HistoricalDatasetInfo, DataLayer, ReconciliationReport, ReconciliationStatus
from src.reconciliation.inventory import HistoricalDataInventoryService
from src.reconciliation.engine import ReconciliationEngine
from src.reconciliation.backfill import BackfillPlanningEngine, BackfillPlan


def test_inventory_models():
    """Test that inventory models can be instantiated"""

    # Test HistoricalDatasetInfo model
    dataset_info = HistoricalDatasetInfo(
        dataset_name="test_dataset",
        data_layer=DataLayer.BRONZE,
        earliest_available_date=datetime.now(),
        latest_available_date=datetime.now(),
        available_partitions=["2023-01-01", "2023-01-02"],
        missing_partitions=["2023-01-03"],
        record_counts={"2023-01-01": 1000, "2023-01-02": 1200},
        file_counts={"2023-01-01": 2, "2023-01-02": 2},
        total_file_sizes={"2023-01-01": 1024000, "2023-01-02": 1228800},
        schema_info={
            'fields': ['date', 'value'],
            'types': ['date', 'float']
        }
    )

    assert dataset_info.dataset_name == "test_dataset"
    assert dataset_info.data_layer == DataLayer.BRONZE
    assert len(dataset_info.available_partitions) == 2
    assert len(dataset_info.missing_partitions) == 1


def test_reconciliation_models():
    """Test that reconciliation models can be instantiated"""

    # Test ReconciliationReport model
    report = ReconciliationReport(
        reconciliation_id="test_recon_123",
        dataset_name="test_dataset",
        date_range=("2023-01-01", "2023-01-05"),
        data_layer=DataLayer.BRONZE,
        assessment_timestamp=datetime.now(),
        overall_status=ReconciliationStatus.WARNING,
        missing_dates=["2023-01-03"],
        incomplete_dates=["2023-01-04"],
        record_count_differences={"2023-01-03": {"bronze_count": 1000, "silver_count": 950, "difference": 50}},
        quality_issues=["Missing field validation"],
        identified_discrepancies=["Record count mismatch"],
        recommended_actions=["Reprocess missing partition"]
    )

    assert report.reconciliation_id == "test_recon_123"
    assert report.dataset_name == "test_dataset"
    assert report.overall_status == ReconciliationStatus.WARNING
    assert len(report.missing_dates) == 1
    assert len(report.record_count_differences) == 1


def test_inventory_service():
    """Test inventory service functionality"""

    # Initialize inventory service
    inventory_service = HistoricalDataInventoryService()

    # Test getting dataset inventory
    dataset_info = inventory_service.get_dataset_inventory("eirgrid_demand", DataLayer.BRONZE)
    assert dataset_info is not None
    assert dataset_info.dataset_name == "eirgrid_demand"
    assert dataset_info.data_layer == DataLayer.BRONZE
    assert len(dataset_info.available_partitions) == 4
    assert len(dataset_info.missing_partitions) == 1

    # Test getting all datasets inventory
    datasets = inventory_service.get_all_datasets_inventory(DataLayer.BRONZE)
    assert len(datasets) == 3  # Should have 3 datasets (eirgrid_demand, eirgrid_generation, openmeteo_weather)

    # Test getting dataset summary
    summary = inventory_service.get_dataset_summary("eirgrid_demand", DataLayer.BRONZE)
    assert summary is not None
    assert summary['dataset_name'] == "eirgrid_demand"
    assert summary['data_layer'] == "bronze"
    assert len(summary['available_partitions']) == 4


def test_reconciliation_engine():
    """Test reconciliation engine functionality"""

    # Initialize reconciliation engine
    engine = ReconciliationEngine()

    # Test identifying missing dates
    missing_dates = engine.identify_missing_dates("eirgrid_demand", DataLayer.BRONZE, "2023-01-01", "2023-01-05")
    assert "2023-01-03" in missing_dates  # Should be missing
    assert "2023-01-01" not in missing_dates  # Should be present

    # Test identifying incomplete partitions
    incomplete_dates = engine.identify_incomplete_partitions("eirgrid_demand", DataLayer.BRONZE)
    # In our mock data, there are no incomplete partitions, so should be empty
    assert len(incomplete_dates) == 0

    # Test bronze to silver reconciliation
    recon_report = engine.reconcile_bronze_to_silver("eirgrid_demand", "2023-01-01", "2023-01-05")
    assert recon_report is not None
    assert recon_report.dataset_name == "eirgrid_demand"
    assert recon_report.data_layer == DataLayer.BRONZE

    # Test silver to gold reconciliation
    recon_report = engine.reconcile_silver_to_gold("eirgrid_demand", "2023-01-01", "2023-01-05")
    assert recon_report is not None
    assert recon_report.dataset_name == "eirgrid_demand"
    assert recon_report.data_layer == DataLayer.SILVER

    # Test running reconciliation
    recon_report = engine.run_reconciliation("eirgrid_demand", DataLayer.BRONZE, "2023-01-01", "2023-01-05")
    assert recon_report is not None
    assert recon_report.dataset_name == "eirgrid_demand"


def test_backfill_planning():
    """Test backfill planning functionality"""

    # Initialize backfill planning engine
    backfill_engine = BackfillPlanningEngine()

    # Test creating backfill plan
    backfill_plan = backfill_engine.create_backfill_plan("eirgrid_demand", "2023-01-01", "2023-01-05", dry_run=True)
    assert backfill_plan is not None
    assert backfill_plan.dataset_name == "eirgrid_demand"
    assert backfill_plan.dry_run is True
    assert len(backfill_plan.missing_partitions) == 1  # Should have one missing partition

    # Test validating backfill plan
    is_valid = backfill_engine.validate_backfill_plan(backfill_plan)
    assert is_valid is True  # Should be valid in dry-run mode

    # Test getting backfill summary
    summary = backfill_engine.get_backfill_summary(backfill_plan)
    assert summary is not None
    assert summary['dataset_name'] == "eirgrid_demand"
    assert summary['missing_partitions_count'] == 1

    # Test with no missing partitions
    backfill_plan_none = backfill_engine.create_backfill_plan("eirgrid_demand", "2023-01-01", "2023-01-02", dry_run=True)
    assert backfill_plan_none is None  # Should return None when no missing partitions


def test_backfill_plan_model():
    """Test backfill plan model"""

    # Create a backfill plan
    backfill_plan = BackfillPlan(
        backfill_id="test_bf_123",
        dataset_name="test_dataset",
        date_range=("2023-01-01", "2023-01-05"),
        missing_partitions=["2023-01-03"],
        required_stages=["bronze", "silver", "gold"],
        dependencies=["bronze_depends_on_silver"],
        expected_input_data=["test_dataset_2023-01-03"],
        expected_output_partitions=["2023-01-03"],
        estimated_workload=100,
        identified_risks=["Risk 1"],
        execution_prerequisites=["Prerequisite 1"],
        dry_run=True
    )

    assert backfill_plan.backfill_id == "test_bf_123"
    assert backfill_plan.dataset_name == "test_dataset"
    assert backfill_plan.dry_run is True

    # Test conversion to dict
    plan_dict = backfill_plan.to_dict()
    assert plan_dict['backfill_id'] == "test_bf_123"
    assert plan_dict['dataset_name'] == "test_dataset"
    assert plan_dict['dry_run'] is True


if __name__ == "__main__":
    test_inventory_models()
    test_reconciliation_models()
    test_inventory_service()
    test_reconciliation_engine()
    test_backfill_planning()
    test_backfill_plan_model()
    print("All tests passed!")