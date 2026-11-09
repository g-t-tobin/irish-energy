export interface EnergySummary {
  total_demand_mwh: number;
  total_generation_mw: number;
  total_renewable_generation_mw: number;
  renewable_percentage: number;
  last_updated: string;
}

export interface DemandForecast {
  timestamp: string;
  actual_demand_mw: number;
  forecast_demand_mw: number;
  forecast_horizon_days: number;
  model_name: string;
  model_version: string;
  forecast_timestamp: string;
  evaluation_metrics: {
    mae: number;
    rmse: number;
    mape: number;
    smape: number;
    mbe: number;
  };
}

export interface RenewableForecast {
  timestamp: string;
  actual_renewable_generation_mw: number;
  forecast_renewable_generation_mw: number;
  forecast_horizon_days: number;
  model_name: string;
  model_version: string;
  forecast_timestamp: string;
  evaluation_metrics: {
    mae: number;
    rmse: number;
    mape: number;
    smape: number;
    mbe: number;
  };
}

export interface ModelMetadata {
  model_id: string;
  model_name: string;
  model_type: string;
  model_version: string;
  forecasting_category: string;
  training_timestamp: string;
  training_dataset_range: [string, string];
  features_used: string[];
  parameters: { [key: string]: any };
  evaluation_metrics: { [key: string]: number };
  feature_importance: { [key: string]: number };
  model_artifact_path: string;
  registration_timestamp: string;
  model_status: string;
  model_description: string;
}

export interface ModelPerformance {
  model_id: string;
  model_version: string;
  evaluation_period: [string, string];
  forecast_horizon: number;
  observation_count: number;
  metrics: { [key: string]: number };
  evaluation_timestamp: string;
}

export interface DriftDetectionResult {
  feature_name: string;
  drift_detected: boolean;
  drift_score: number;
  drift_type: string;
  previous_distribution: { [key: string]: number };
  current_distribution: { [key: string]: number };
  timestamp: string;
}

export interface RetrainingRecommendation {
  model_id: string;
  model_version: string;
  recommendation_reason: string;
  recommendation_type: string;
  confidence_score: number;
  suggested_action: string;
  threshold_met: boolean;
  timestamp: string;
}

export interface PromotionDecision {
  model_id: string;
  model_version: string;
  previous_production_version: string;
  promotion_reason: string;
  evaluation_results: { [key: string]: any };
  decision_timestamp: string;
  approved: boolean;
}

export interface RollbackRecord {
  model_id: string;
  rolled_back_from_version: string;
  rolled_back_to_version: string;
  rollback_reason: string;
  rollback_timestamp: string;
  rollback_user?: string;
}

export interface ModelLifecycleStatus {
  model_id: string;
  model_name: string;
  model_version: string;
  model_status: string;
  forecasting_category: string;
  training_timestamp: string;
  promotion_history: PromotionDecision[];
  rollback_history: RollbackRecord[];
}

export interface ForecastComparison {
  timestamp: string;
  actual_demand_mw: number;
  forecast_demand_mw: number;
  renewable_generation_mw: number;
  forecast_renewable_mw: number;
}