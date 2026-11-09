"""
API endpoints for MLOps functionality
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from src.mlops.models import ModelMetadata, ModelLifecycleState, ModelPerformance, \
    DriftDetectionResult, RetrainingRecommendation, PromotionDecision, RollbackRecord
from src.mlops.registry import ModelRegistry
from src.mlops.performance import ModelPerformanceTracker
from src.mlops.drift import DriftDetector
from src.mlops.retraining import RetrainingEngine
from src.mlops.promotion import ModelPromotionEngine
from src.mlops.rollback import ModelRollbackEngine
from src.mlops.integration import MLOpsIntegration

# Initialize routers
router = APIRouter(prefix="/mlops", tags=["MLOps"])

# Pydantic models for API responses
class ModelListResponse(BaseModel):
    models: List[ModelMetadata]

class ModelDetailResponse(BaseModel):
    model: ModelMetadata

class ModelVersionsResponse(BaseModel):
    versions: List[str]

class ModelPerformanceResponse(BaseModel):
    performance: List[ModelPerformance]

class DriftResultsResponse(BaseModel):
    drift_results: List[DriftDetectionResult]

class RetrainingRecommendationsResponse(BaseModel):
    recommendations: List[RetrainingRecommendation]

class PromotionHistoryResponse(BaseModel):
    history: List[PromotionDecision]

class RollbackHistoryResponse(BaseModel):
    history: List[RollbackRecord]

class HealthResponse(BaseModel):
    status: str
    timestamp: str

class ModelPromotionRequest(BaseModel):
    model_id: str
    model_version: Optional[str] = None

class ModelRollbackRequest(BaseModel):
    model_id: str
    target_version: str
    rollback_reason: str
    rollback_user: Optional[str] = None

class ModelEvaluationRequest(BaseModel):
    model_id: str
    model_version: Optional[str] = None

# Initialize MLOps components
# Note: In a real implementation, these would be injected via dependency injection
registry = ModelRegistry()
performance_tracker = ModelPerformanceTracker()
drift_detector = DriftDetector()
retraining_engine = RetrainingEngine(registry, performance_tracker)
promotion_engine = ModelPromotionEngine(registry, performance_tracker, drift_detector)
rollback_engine = ModelRollbackEngine(registry)
integration = MLOpsIntegration(registry, performance_tracker, drift_detector,
                              retraining_engine, promotion_engine, rollback_engine)

@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """Get list of all registered models"""
    models = registry.list_models()
    return ModelListResponse(models=models)

@router.get("/models/{model_id}", response_model=ModelDetailResponse)
async def get_model(model_id: str):
    """Get detailed information about a specific model"""
    model = registry.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID {model_id} not found"
        )
    return ModelDetailResponse(model=model)

@router.get("/models/{model_id}/versions", response_model=ModelVersionsResponse)
async def get_model_versions(model_id: str):
    """Get all versions of a specific model"""
    versions = registry.get_model_versions(model_id)
    return ModelVersionsResponse(versions=versions)

@router.get("/models/{model_id}/performance", response_model=ModelPerformanceResponse)
async def get_model_performance(model_id: str, model_version: Optional[str] = None):
    """Get performance history for a model"""
    # If no version specified, use the latest version
    if model_version is None:
        model = registry.get_model(model_id)
        if model:
            model_version = model.model_version

    if model_version is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model version required"
        )

    performances = performance_tracker.get_performance_history(model_id, model_version)
    return ModelPerformanceResponse(performance=performances)

@router.get("/drift", response_model=DriftResultsResponse)
async def get_drift_results(feature_name: Optional[str] = None, limit: int = 10):
    """Get recent drift detection results"""
    results = drift_detector.get_recent_drift_results(feature_name, limit)
    return DriftResultsResponse(drift_results=results)

@router.get("/retraining/recommendations", response_model=RetrainingRecommendationsResponse)
async def get_retraining_recommendations(model_id: str, model_version: Optional[str] = None):
    """Get retraining recommendations for a model"""
    recommendations = retraining_engine.get_recommendations_history(model_id, 10)
    return RetrainingRecommendationsResponse(recommendations=recommendations)

@router.get("/registry/health", response_model=HealthResponse)
async def registry_health():
    """Check health of the model registry"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

@router.post("/models/{model_id}/evaluate", response_model=Dict[str, Any])
async def evaluate_model(request: ModelEvaluationRequest):
    """Evaluate a candidate model for promotion"""
    evaluation = promotion_engine.evaluate_candidate_model(
        request.model_id,
        request.model_version
    )
    return evaluation

@router.post("/models/{model_id}/promote", response_model=Dict[str, Any])
async def promote_model(request: ModelPromotionRequest):
    """Promote a candidate model to production"""
    result = promotion_engine.promote_model(
        request.model_id,
        request.model_version
    )
    return result

@router.post("/models/{model_id}/rollback", response_model=Dict[str, Any])
async def rollback_model(request: ModelRollbackRequest):
    """Rollback a model to a previous version"""
    result = rollback_engine.rollback_model(
        request.model_id,
        request.target_version,
        request.rollback_reason,
        request.rollback_user
    )
    return result

@router.get("/models/{model_id}/lifecycle", response_model=Dict[str, Any])
async def get_model_lifecycle(model_id: str):
    """Get complete lifecycle status of a model"""
    status_info = promotion_engine.get_model_lifecycle_status(model_id)
    return status_info

@router.get("/reports/comprehensive", response_model=Dict[str, Any])
async def get_comprehensive_report():
    """Generate comprehensive MLOps report"""
    report = integration.generate_comprehensive_report()
    return report