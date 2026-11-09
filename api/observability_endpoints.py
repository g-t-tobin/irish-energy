"""
Observability API endpoints for Irish Energy Analytics Data Platform
"""
from fastapi import FastAPI, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger
from src.observability.service import ObservabilityService
from src.monitoring.service import MonitoringService


app = FastAPI(title="Observability API", version="1.0.0")


# Initialize the observability service
observability_service = ObservabilityService()


def get_observability_service() -> ObservabilityService:
    """Dependency injection for observability service"""
    return observability_service


def get_monitoring_service() -> MonitoringService:
    """Dependency injection for monitoring service"""
    return MonitoringService()


@app.get("/observability/health", response_model=dict)
async def observability_health_check():
    """Health check endpoint for observability service"""
    return {"status": "healthy", "service": "observability"}


@app.get("/observability/executions", response_model=List[Dict[str, Any]])
async def get_recent_executions(limit: int = 20,
                               source_filter: str = None,
                               status_filter: str = None):
    """
    Retrieve recent pipeline executions

    Args:
        limit: Maximum number of executions to return
        source_filter: Filter by source (pipeline, manual, etc.)
        status_filter: Filter by status (started, completed, failed)
    """
    try:
        # Use the monitoring service to get execution summaries
        monitoring_service = get_monitoring_service()
        executions = monitoring_service.storage.list_execution_summaries(
            limit=limit,
            source_filter=source_filter,
            status_filter=status_filter
        )
        return executions
    except Exception as e:
        logger.error(f"Error retrieving recent executions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving executions: {str(e)}")


@app.get("/observability/metrics/aggregated", response_model=Dict[str, Any])
async def get_aggregated_metrics(time_window_hours: int = 24):
    """
    Retrieve aggregated observability metrics

    Args:
        time_window_hours: Time window in hours to filter metrics
    """
    try:
        # Generate aggregated metrics report
        report = observability_service.generate_aggregated_metrics_report(time_window_hours)
        return report
    except Exception as e:
        logger.error(f"Error generating aggregated metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating metrics: {str(e)}")


@app.get("/observability/recent", response_model=List[Dict[str, Any]])
async def get_recent_observability_data(limit: int = 20):
    """
    Retrieve recent observability data

    Args:
        limit: Maximum number of records to return
    """
    try:
        # Get recent observability data
        data = observability_service.get_recent_observability_data(limit)
        return data
    except Exception as e:
        logger.error(f"Error retrieving recent observability data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving observability data: {str(e)}")