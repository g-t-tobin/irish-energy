"""
Reconciliation API endpoints for Irish Energy Analytics Data Platform
"""
from fastapi import FastAPI, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger
from src.reconciliation.inventory import HistoricalDataInventoryService
from src.reconciliation.engine import ReconciliationEngine
from src.reconciliation.backfill import BackfillPlanningEngine
from src.reconciliation.models import DataLayer


# Initialize services
inventory_service = HistoricalDataInventoryService()
reconciliation_engine = ReconciliationEngine(inventory_service)
backfill_engine = BackfillPlanningEngine(reconciliation_engine, inventory_service)


def get_inventory_service() -> HistoricalDataInventoryService:
    """Dependency injection for inventory service"""
    return inventory_service


def get_reconciliation_engine() -> ReconciliationEngine:
    """Dependency injection for reconciliation engine"""
    return reconciliation_engine


def get_backfill_engine() -> BackfillPlanningEngine:
    """Dependency injection for backfill engine"""
    return backfill_engine


# Define the API routes for reconciliation functionality
# Note: This will be mounted under /reconciliation in main.py
app = FastAPI(title="Reconciliation API", version="1.0.0")


@app.get("/health", response_model=dict)
async def reconciliation_health_check():
    """Health check endpoint for reconciliation service"""
    return {"status": "healthy", "service": "reconciliation"}


@app.get("/summary", response_model=List[Dict[str, Any]])
async def get_reconciliation_summary():
    """
    Get a summary of all datasets and their reconciliation status
    """
    try:
        # Get all datasets at bronze layer
        datasets = inventory_service.get_all_datasets_inventory(DataLayer.BRONZE)

        # Convert to summary format
        summaries = []
        for dataset in datasets:
            if dataset:
                summaries.append({
                    'dataset_name': dataset.dataset_name,
                    'data_layer': dataset.data_layer.value,
                    'earliest_available_date': dataset.earliest_available_date.isoformat() if dataset.earliest_available_date else None,
                    'latest_available_date': dataset.latest_available_date.isoformat() if dataset.latest_available_date else None,
                    'available_partitions': len(dataset.available_partitions),
                    'missing_partitions': len(dataset.missing_partitions),
                    'total_file_sizes': sum(dataset.total_file_sizes.values())
                })

        return summaries
    except Exception as e:
        logger.error(f"Error retrieving reconciliation summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving summary: {str(e)}")


@app.get("/datasets", response_model=List[str])
async def get_all_datasets():
    """
    Get list of all available datasets
    """
    try:
        # For now, we'll return the mock datasets
        return ["eirgrid_demand", "eirgrid_generation", "openmeteo_weather"]
    except Exception as e:
        logger.error(f"Error retrieving datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving datasets: {str(e)}")


@app.get("/datasets/{dataset_name}", response_model=Dict[str, Any])
async def get_dataset_info(dataset_name: str, data_layer: str = "bronze"):
    """
    Get detailed information for a specific dataset

    Args:
        dataset_name: Name of the dataset
        data_layer: Data layer (bronze, silver, gold)
    """
    try:
        layer_enum = DataLayer(data_layer)
        dataset_info = inventory_service.get_dataset_inventory(dataset_name, layer_enum)
        if not dataset_info:
            raise HTTPException(status_code=404, detail="Dataset not found")

        return {
            'dataset_name': dataset_info.dataset_name,
            'data_layer': dataset_info.data_layer.value,
            'earliest_available_date': dataset_info.earliest_available_date.isoformat() if dataset_info.earliest_available_date else None,
            'latest_available_date': dataset_info.latest_available_date.isoformat() if dataset_info.latest_available_date else None,
            'available_partitions': dataset_info.available_partitions,
            'missing_partitions': dataset_info.missing_partitions,
            'record_counts': dataset_info.record_counts,
            'file_counts': dataset_info.file_counts,
            'total_file_sizes': dataset_info.total_file_sizes
        }
    except Exception as e:
        logger.error(f"Error retrieving dataset info for {dataset_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving dataset info: {str(e)}")


@app.post("/reconciliation/run")
async def run_reconciliation(dataset_name: str, start_date: str, end_date: str,
                           data_layer: str = "bronze"):
    """
    Run a reconciliation for a specific dataset and date range

    Args:
        dataset_name: Name of the dataset
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        data_layer: Data layer (bronze, silver, gold)
    """
    try:
        layer_enum = DataLayer(data_layer)
        report = reconciliation_engine.run_reconciliation(dataset_name, layer_enum, start_date, end_date)

        return {
            'reconciliation_id': report.reconciliation_id,
            'dataset_name': report.dataset_name,
            'date_range': report.date_range,
            'overall_status': report.overall_status.value,
            'missing_dates': report.missing_dates,
            'incomplete_dates': report.incomplete_dates,
            'record_count_differences': report.record_count_differences
        }
    except Exception as e:
        logger.error(f"Error running reconciliation for {dataset_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running reconciliation: {str(e)}")


@app.post("/backfills/plan")
async def create_backfill_plan(dataset_name: str, start_date: str, end_date: str,
                             dry_run: bool = True):
    """
    Create a backfill plan for missing data

    Args:
        dataset_name: Name of the dataset
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        dry_run: Whether to create plan in dry-run mode (default True)
    """
    try:
        backfill_plan = backfill_engine.create_backfill_plan(dataset_name, start_date, end_date, dry_run)
        if not backfill_plan:
            raise HTTPException(status_code=404, detail="No backfill plan needed (no missing partitions)")

        return backfill_plan.to_dict()
    except Exception as e:
        logger.error(f"Error creating backfill plan for {dataset_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating backfill plan: {str(e)}")


@app.get("/backfills", response_model=List[Dict[str, Any]])
async def get_backfill_plans():
    """
    Get list of all backfill plans (in a real implementation, this would come from storage)
    """
    try:
        # For simulation purposes, return empty list
        return []
    except Exception as e:
        logger.error(f"Error retrieving backfill plans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving backfill plans: {str(e)}")


@app.get("/backfills/{backfill_id}", response_model=Dict[str, Any])
async def get_backfill_plan(backfill_id: str):
    """
    Get a specific backfill plan (in a real implementation, this would come from storage)

    Args:
        backfill_id: Backfill plan identifier
    """
    try:
        # For simulation purposes, return empty dict
        return {"message": "Backfill plan not found in simulation mode"}
    except Exception as e:
        logger.error(f"Error retrieving backfill plan {backfill_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving backfill plan: {str(e)}")


# Mount this app under /reconciliation in the main API