"""
Backfill planning engine for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from dateutil.parser import parse
from loguru import logger
from src.reconciliation.models import DataLayer, ReconciliationReport, ReconciliationStatus
from src.reconciliation.engine import ReconciliationEngine
from src.reconciliation.inventory import HistoricalDataInventoryService


class BackfillPlan:
    """Represents a backfill plan"""
    def __init__(self, backfill_id: str, dataset_name: str, date_range: tuple,
                 missing_partitions: List[str], required_stages: List[str],
                 dependencies: List[str], expected_input_data: List[str],
                 expected_output_partitions: List[str], estimated_workload: int = 0,
                 identified_risks: List[str] = None, execution_prerequisites: List[str] = None,
                 dry_run: bool = True):
        self.backfill_id = backfill_id
        self.dataset_name = dataset_name
        self.date_range = date_range
        self.missing_partitions = missing_partitions
        self.required_stages = required_stages
        self.dependencies = dependencies
        self.expected_input_data = expected_input_data
        self.expected_output_partitions = expected_output_partitions
        self.estimated_workload = estimated_workload
        self.identified_risks = identified_risks or []
        self.execution_prerequisites = execution_prerequisites or []
        self.dry_run = dry_run

    def to_dict(self) -> Dict[str, Any]:
        """Convert backfill plan to dictionary format"""
        return {
            'backfill_id': self.backfill_id,
            'dataset_name': self.dataset_name,
            'date_range': self.date_range,
            'missing_partitions': self.missing_partitions,
            'required_stages': self.required_stages,
            'dependencies': self.dependencies,
            'expected_input_data': self.expected_input_data,
            'expected_output_partitions': self.expected_output_partitions,
            'estimated_workload': self.estimated_workload,
            'identified_risks': self.identified_risks,
            'execution_prerequisites': self.execution_prerequisites,
            'dry_run': self.dry_run
        }


class BackfillPlanningEngine:
    """
    Engine for creating safe backfill plans
    """

    def __init__(self, reconciliation_engine: ReconciliationEngine = None,
                 inventory_service: HistoricalDataInventoryService = None):
        self.reconciliation_engine = reconciliation_engine or ReconciliationEngine()
        self.inventory_service = inventory_service or HistoricalDataInventoryService()

    def create_backfill_plan(self, dataset_name: str, start_date: str, end_date: str,
                           dry_run: bool = True) -> Optional[BackfillPlan]:
        """
        Create a backfill plan for missing data

        Args:
            dataset_name: Name of the dataset
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            dry_run: Whether to create plan in dry-run mode (default True)

        Returns:
            BackfillPlan or None if no plan can be created
        """
        try:
            # Run reconciliation to identify missing data
            recon_report = self.reconciliation_engine.run_reconciliation(dataset_name, DataLayer.BRONZE, start_date, end_date)

            # Identify missing partitions
            missing_partitions = recon_report.missing_dates

            if not missing_partitions:
                logger.info(f"No missing partitions found for {dataset_name} in date range {start_date} to {end_date}")
                return None

            # Determine required processing stages
            required_stages = self._determine_required_stages(dataset_name, missing_partitions)

            # Determine dependencies
            dependencies = self._determine_dependencies(dataset_name, required_stages)

            # Determine expected input/output data
            expected_input_data = self._determine_expected_input_data(dataset_name, missing_partitions)
            expected_output_partitions = missing_partitions

            # Estimate workload (simple estimation)
            estimated_workload = len(missing_partitions) * 10  # 10 units per partition

            # Identify risks
            identified_risks = self._identify_risks(dataset_name, missing_partitions)

            # Set execution prerequisites
            execution_prerequisites = self._set_execution_prerequisites(dataset_name, missing_partitions)

            # Create backfill plan
            backfill_id = f"bf_{dataset_name}_{start_date}_{end_date}_{int(datetime.now().timestamp())}"

            return BackfillPlan(
                backfill_id=backfill_id,
                dataset_name=dataset_name,
                date_range=(start_date, end_date),
                missing_partitions=missing_partitions,
                required_stages=required_stages,
                dependencies=dependencies,
                expected_input_data=expected_input_data,
                expected_output_partitions=expected_output_partitions,
                estimated_workload=estimated_workload,
                identified_risks=identified_risks,
                execution_prerequisites=execution_prerequisites,
                dry_run=dry_run
            )

        except Exception as e:
            logger.error(f"Error creating backfill plan for {dataset_name}: {str(e)}")
            return None

    def _determine_required_stages(self, dataset_name: str, missing_partitions: List[str]) -> List[str]:
        """Determine required processing stages based on dataset and partitions"""
        # For simplicity, we'll assume all datasets need bronze->silver->gold processing
        # In a real implementation, this would be more sophisticated
        return ['bronze', 'silver', 'gold']

    def _determine_dependencies(self, dataset_name: str, required_stages: List[str]) -> List[str]:
        """Determine dependencies for processing stages"""
        # For EirGrid datasets, dependencies are:
        # bronze -> silver -> gold
        # For Open-Meteo datasets, dependencies are:
        # bronze -> silver -> gold

        # Simple dependency tree - each stage depends on the previous one
        dependencies = []
        for i, stage in enumerate(required_stages):
            if i > 0:
                dependencies.append(f"{stage}_depends_on_{required_stages[i-1]}")

        return dependencies

    def _determine_expected_input_data(self, dataset_name: str, missing_partitions: List[str]) -> List[str]:
        """Determine expected input data for the backfill"""
        # For this demo, we'll assume input data is based on the missing partitions
        return [f"{dataset_name}_{partition}" for partition in missing_partitions]

    def _identify_risks(self, dataset_name: str, missing_partitions: List[str]) -> List[str]:
        """Identify potential risks for the backfill"""
        risks = []

        # Risk: Overwriting existing partitions
        # (In a real implementation, this would check if partitions already exist)

        # Risk: Large backfill volume
        if len(missing_partitions) > 100:
            risks.append(f"Large backfill volume ({len(missing_partitions)} partitions)")

        # Risk: Missing source data
        if dataset_name in ['eirgrid_demand', 'eirgrid_generation']:
            risks.append("EirGrid source data may have gaps")
        elif dataset_name == 'openmeteo_weather':
            risks.append("Open-Meteo source data may have gaps")

        return risks

    def _set_execution_prerequisites(self, dataset_name: str, missing_partitions: List[str]) -> List[str]:
        """Set execution prerequisites for the backfill"""
        prerequisites = [
            "Source data availability check",
            "Target data lake access",
            "Required processing resources available",
            "Dry-run mode enabled (default)"
        ]

        # Add dataset-specific prerequisites
        if dataset_name in ['eirgrid_demand', 'eirgrid_generation']:
            prerequisites.append("EirGrid API access verified")
        elif dataset_name == 'openmeteo_weather':
            prerequisites.append("Open-Meteo API access verified")

        return prerequisites

    def validate_backfill_plan(self, backfill_plan: BackfillPlan) -> bool:
        """
        Validate a backfill plan for safety

        Args:
            backfill_plan: Backfill plan to validate

        Returns:
            True if valid, False otherwise
        """
        # Check that backfill is in dry-run mode by default
        if not backfill_plan.dry_run:
            logger.warning("Backfill plan is not in dry-run mode - this may cause data overwrite")
            return False

        # Check for overwriting existing partitions
        # (In a real implementation, this would check if partitions already exist)

        # Check for dependencies
        if not backfill_plan.dependencies:
            logger.info("No dependencies detected for backfill plan")

        # Check for required prerequisites
        if not backfill_plan.execution_prerequisites:
            logger.warning("No execution prerequisites defined")

        # If we got here, the plan is valid (in this simplified version)
        return True

    def get_backfill_summary(self, backfill_plan: BackfillPlan) -> Dict[str, Any]:
        """
        Get a summary of a backfill plan

        Args:
            backfill_plan: Backfill plan to summarize

        Returns:
            Dictionary with backfill summary
        """
        return {
            'backfill_id': backfill_plan.backfill_id,
            'dataset_name': backfill_plan.dataset_name,
            'date_range': backfill_plan.date_range,
            'missing_partitions_count': len(backfill_plan.missing_partitions),
            'required_stages': backfill_plan.required_stages,
            'estimated_workload': backfill_plan.estimated_workload,
            'risks': backfill_plan.identified_risks,
            'dry_run': backfill_plan.dry_run
        }