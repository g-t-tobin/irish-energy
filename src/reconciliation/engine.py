"""
Reconciliation engine for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, timedelta
from dateutil.parser import parse
from loguru import logger
from src.reconciliation.models import HistoricalDatasetInfo, DataLayer, ReconciliationReport, ReconciliationStatus
from src.quality.models import QualityReport
from src.reconciliation.inventory import HistoricalDataInventoryService


class ReconciliationEngine:
    """
    Engine for performing data reconciliation operations
    """

    def __init__(self, inventory_service: HistoricalDataInventoryService = None):
        self.inventory_service = inventory_service or HistoricalDataInventoryService()

    def identify_missing_dates(self, dataset_name: str, data_layer: DataLayer,
                             start_date: str, end_date: str) -> List[str]:
        """
        Identify missing dates in a date range for a dataset

        Args:
            dataset_name: Name of the dataset
            data_layer: Data layer (bronze, silver, gold)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of missing date strings in YYYY-MM-DD format
        """
        try:
            # Get dataset inventory
            dataset_info = self.inventory_service.get_dataset_inventory(dataset_name, data_layer)
            if not dataset_info:
                return []

            # Generate expected date range
            start = parse(start_date)
            end = parse(end_date)
            expected_dates = []
            current = start
            while current <= end:
                expected_dates.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)

            # Find missing dates
            available_dates = set(dataset_info.available_partitions)
            missing_dates = [d for d in expected_dates if d not in available_dates]

            return missing_dates
        except Exception as e:
            logger.error(f"Error identifying missing dates for {dataset_name}: {str(e)}")
            return []

    def identify_incomplete_partitions(self, dataset_name: str, data_layer: DataLayer) -> List[str]:
        """
        Identify partitions with potential issues (missing fields, low records, etc.)

        Args:
            dataset_name: Name of the dataset
            data_layer: Data layer (bronze, silver, gold)

        Returns:
            List of partition dates with issues
        """
        try:
            # Get dataset inventory
            dataset_info = self.inventory_service.get_dataset_inventory(dataset_name, data_layer)
            if not dataset_info:
                return []

            incomplete_partitions = []

            # Check for partitions with unusually low record counts
            # (This would be more sophisticated in a real implementation)
            for partition_date, record_count in dataset_info.record_counts.items():
                # Example rule: if record count is less than 10% of typical count
                if record_count < 100:  # Arbitrary threshold for demo
                    incomplete_partitions.append(partition_date)

            # Check for missing schema information
            if not dataset_info.schema_info:
                incomplete_partitions.extend(dataset_info.available_partitions)

            return list(set(incomplete_partitions))  # Remove duplicates
        except Exception as e:
            logger.error(f"Error identifying incomplete partitions for {dataset_name}: {str(e)}")
            return []

    def reconcile_bronze_to_silver(self, dataset_name: str,
                                start_date: str, end_date: str) -> ReconciliationReport:
        """
        Compare bronze and silver datasets for consistency

        Args:
            dataset_name: Name of the dataset
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            ReconciliationReport with comparison results
        """
        try:
            # Get inventory for both layers
            bronze_info = self.inventory_service.get_dataset_inventory(dataset_name, DataLayer.BRONZE)
            silver_info = self.inventory_service.get_dataset_inventory(dataset_name, DataLayer.SILVER)

            if not bronze_info or not silver_info:
                return self._create_empty_report(dataset_name, DataLayer.BRONZE, start_date, end_date)

            # Generate expected date range
            start = parse(start_date)
            end = parse(end_date)
            expected_dates = []
            current = start
            while current <= end:
                expected_dates.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)

            # Find missing processing dates
            bronze_dates = set(bronze_info.available_partitions)
            silver_dates = set(silver_info.available_partitions)

            missing_processing_dates = []
            for expected_date in expected_dates:
                if expected_date not in bronze_dates and expected_date in silver_dates:
                    missing_processing_dates.append(expected_date)

            # Find record count differences
            record_count_differences = {}
            for expected_date in expected_dates:
                bronze_count = bronze_info.record_counts.get(expected_date, 0)
                silver_count = silver_info.record_counts.get(expected_date, 0)

                if bronze_count != silver_count:
                    record_count_differences[expected_date] = {
                        'bronze_count': bronze_count,
                        'silver_count': silver_count,
                        'difference': abs(bronze_count - silver_count)
                    }

            # Determine overall status
            overall_status = ReconciliationStatus.PASS
            if missing_processing_dates or record_count_differences:
                overall_status = ReconciliationStatus.WARNING

            # Create report
            return ReconciliationReport(
                reconciliation_id=f"recon_{dataset_name}_bronze_silver_{start_date}_{end_date}",
                dataset_name=dataset_name,
                date_range=(start_date, end_date),
                data_layer=DataLayer.BRONZE,
                assessment_timestamp=datetime.now(),
                overall_status=overall_status,
                missing_dates=missing_processing_dates,
                incomplete_dates=[],
                record_count_differences=record_count_differences,
                quality_issues=[],
                identified_discrepancies=[],
                recommended_actions=[]
            )
        except Exception as e:
            logger.error(f"Error reconciling bronze to silver for {dataset_name}: {str(e)}")
            return self._create_empty_report(dataset_name, DataLayer.BRONZE, start_date, end_date)

    def reconcile_silver_to_gold(self, dataset_name: str,
                              start_date: str, end_date: str) -> ReconciliationReport:
        """
        Compare silver and gold datasets for consistency

        Args:
            dataset_name: Name of the dataset
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            ReconciliationReport with comparison results
        """
        try:
            # Get inventory for both layers
            silver_info = self.inventory_service.get_dataset_inventory(dataset_name, DataLayer.SILVER)
            gold_info = self.inventory_service.get_dataset_inventory(dataset_name, DataLayer.GOLD)

            if not silver_info or not gold_info:
                return self._create_empty_report(dataset_name, DataLayer.SILVER, start_date, end_date)

            # Generate expected date range
            start = parse(start_date)
            end = parse(end_date)
            expected_dates = []
            current = start
            while current <= end:
                expected_dates.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)

            # Find missing gold partitions
            silver_dates = set(silver_info.available_partitions)
            gold_dates = set(gold_info.available_partitions)

            missing_gold_partitions = []
            for expected_date in expected_dates:
                if expected_date in silver_dates and expected_date not in gold_dates:
                    missing_gold_partitions.append(expected_date)

            # Find record count differences
            record_count_differences = {}
            for expected_date in expected_dates:
                silver_count = silver_info.record_counts.get(expected_date, 0)
                gold_count = gold_info.record_counts.get(expected_date, 0)

                if silver_count != gold_count:
                    record_count_differences[expected_date] = {
                        'silver_count': silver_count,
                        'gold_count': gold_count,
                        'difference': abs(silver_count - gold_count)
                    }

            # Determine overall status
            overall_status = ReconciliationStatus.PASS
            if missing_gold_partitions or record_count_differences:
                overall_status = ReconciliationStatus.WARNING

            # Create report
            return ReconciliationReport(
                reconciliation_id=f"recon_{dataset_name}_silver_gold_{start_date}_{end_date}",
                dataset_name=dataset_name,
                date_range=(start_date, end_date),
                data_layer=DataLayer.SILVER,
                assessment_timestamp=datetime.now(),
                overall_status=overall_status,
                missing_dates=missing_gold_partitions,
                incomplete_dates=[],
                record_count_differences=record_count_differences,
                quality_issues=[],
                identified_discrepancies=[],
                recommended_actions=[]
            )
        except Exception as e:
            logger.error(f"Error reconciling silver to gold for {dataset_name}: {str(e)}")
            return self._create_empty_report(dataset_name, DataLayer.SILVER, start_date, end_date)

    def _create_empty_report(self, dataset_name: str, data_layer: DataLayer,
                           start_date: str, end_date: str) -> ReconciliationReport:
        """Helper method to create an empty reconciliation report"""
        return ReconciliationReport(
            reconciliation_id=f"recon_{dataset_name}_{data_layer.value}_empty",
            dataset_name=dataset_name,
            date_range=(start_date, end_date),
            data_layer=data_layer,
            assessment_timestamp=datetime.now(),
            overall_status=ReconciliationStatus.UNKNOWN,
            missing_dates=[],
            incomplete_dates=[],
            record_count_differences={},
            quality_issues=[],
            identified_discrepancies=[],
            recommended_actions=[]
        )

    def run_reconciliation(self, dataset_name: str, data_layer: DataLayer,
                          start_date: str, end_date: str) -> ReconciliationReport:
        """
        Run a full reconciliation for a dataset

        Args:
            dataset_name: Name of the dataset
            data_layer: Data layer (bronze, silver, gold)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            ReconciliationReport with results
        """
        try:
            # Identify missing dates
            missing_dates = self.identify_missing_dates(dataset_name, data_layer, start_date, end_date)

            # Identify incomplete partitions
            incomplete_dates = self.identify_incomplete_partitions(dataset_name, data_layer)

            # Create a basic report
            return ReconciliationReport(
                reconciliation_id=f"recon_{dataset_name}_{data_layer.value}_{start_date}_{end_date}",
                dataset_name=dataset_name,
                date_range=(start_date, end_date),
                data_layer=data_layer,
                assessment_timestamp=datetime.now(),
                overall_status=ReconciliationStatus.PASS,
                missing_dates=missing_dates,
                incomplete_dates=incomplete_dates,
                record_count_differences={},
                quality_issues=[],
                identified_discrepancies=[],
                recommended_actions=[]
            )
        except Exception as e:
            logger.error(f"Error running reconciliation for {dataset_name}: {str(e)}")
            return self._create_empty_report(dataset_name, data_layer, start_date, end_date)