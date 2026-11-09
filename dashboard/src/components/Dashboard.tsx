import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PipelineExecution,
  QualityMetric,
  Alert,
  Incident,
  ReconciliationReport,
  BackfillPlan,
  DatasetInventory,
  AggregatedObservabilityMetrics,
  EnergySummary,
  DemandForecast,
  RenewableForecast,
  ModelMetadata,
  ModelPerformance,
  DriftDetectionResult,
  RetrainingRecommendation,
  ModelLifecycleStatus
} from '../types/dashboardTypes';
import {
  ModelMetadata as MLOpsModelMetadata,
  ModelPerformance as MLOpsModelPerformance,
  DriftDetectionResult as MLOpsDriftDetectionResult,
  RetrainingRecommendation as MLOpsRetrainingRecommendation,
  ModelLifecycleStatus as MLOpsModelLifecycleStatus
} from '../types/mlopsTypes';

// Mock data for initial implementation
const mockEnergySummary: EnergySummary = {
  total_demand_mwh: 150000,
  total_generation_mw: 180000,
  total_renewable_generation_mw: 90000,
  renewable_percentage: 50.0,
  last_updated: '2023-01-05T08:15:00Z'
};

const mockDemandForecasts: DemandForecast[] = [
  {
    timestamp: '2023-01-05T00:00:00Z',
    actual_demand_mw: 120000,
    forecast_demand_mw: 122000,
    forecast_horizon_days: 1,
    model_name: 'ARIMA Demand Model',
    model_version: '2.1.0',
    forecast_timestamp: '2023-01-05T08:00:00Z',
    evaluation_metrics: {
      mae: 1500,
      rmse: 2200,
      mape: 1.2,
      smape: 1.1,
      mbe: 50
    }
  },
  {
    timestamp: '2023-01-06T00:00:00Z',
    actual_demand_mw: 125000,
    forecast_demand_mw: 123000,
    forecast_horizon_days: 1,
    model_name: 'ARIMA Demand Model',
    model_version: '2.1.0',
    forecast_timestamp: '2023-01-05T08:00:00Z',
    evaluation_metrics: {
      mae: 1500,
      rmse: 2200,
      mape: 1.2,
      smape: 1.1,
      mbe: 50
    }
  }
];

const mockRenewableForecasts: RenewableForecast[] = [
  {
    timestamp: '2023-01-05T00:00:00Z',
    actual_renewable_generation_mw: 45000,
    forecast_renewable_generation_mw: 46000,
    forecast_horizon_days: 1,
    model_name: 'Renewable Forecast Model',
    model_version: '1.0.0',
    forecast_timestamp: '2023-01-05T08:00:00Z',
    evaluation_metrics: {
      mae: 800,
      rmse: 1200,
      mape: 1.8,
      smape: 1.7,
      mbe: -20
    }
  }
];

const mockModels: ModelMetadata[] = [
  {
    model_id: 'demand_forecast_v2',
    model_name: 'Electricity Demand Forecasting Model',
    model_type: 'ARIMA',
    model_version: '2.1.0',
    forecasting_category: 'demand',
    training_timestamp: '2023-01-01T00:00:00Z',
    training_dataset_range: ['2020-01-01', '2022-12-31'],
    features_used: ['temperature', 'humidity', 'day_of_week'],
    parameters: { order: [1,1,1], seasonal_order: [1,1,1,12] },
    evaluation_metrics: { mae: 1500, rmse: 2200, mape: 1.2 },
    feature_importance: { temperature: 0.45, humidity: 0.30, day_of_week: 0.25 },
    model_artifact_path: '/artifacts/demand_forecast_v2/v2.1.0',
    registration_timestamp: '2023-01-01T00:00:00Z',
    model_status: 'production',
    model_description: 'Primary demand forecasting model'
  },
  {
    model_id: 'renewable_forecast_v1',
    model_name: 'Renewable Generation Forecasting Model',
    model_type: 'Random Forest',
    model_version: '1.0.0',
    forecasting_category: 'renewable_total',
    training_timestamp: '2023-01-01T00:00:00Z',
    training_dataset_range: ['2020-01-01', '2022-12-31'],
    features_used: ['temperature', 'humidity', 'wind_speed', 'precipitation'],
    parameters: { n_estimators: 100, max_depth: 10 },
    evaluation_metrics: { mae: 800, rmse: 1200, mape: 1.8 },
    feature_importance: { temperature: 0.35, wind_speed: 0.40, humidity: 0.15, precipitation: 0.10 },
    model_artifact_path: '/artifacts/renewable_forecast_v1/v1.0.0',
    registration_timestamp: '2023-01-01T00:00:00Z',
    model_status: 'candidate',
    model_description: 'Aggregate renewable forecasting model'
  }
];

const mockModelPerformances: ModelPerformance[] = [
  {
    model_id: 'demand_forecast_v2',
    model_version: '2.1.0',
    evaluation_period: ['2023-01-01', '2023-01-05'],
    forecast_horizon: 1,
    observation_count: 100,
    metrics: { mae: 1500, rmse: 2200, mape: 1.2, smape: 1.1, mbe: 50 },
    evaluation_timestamp: '2023-01-05T08:00:00Z'
  }
];

const mockDriftResults: DriftDetectionResult[] = [
  {
    feature_name: 'temperature',
    drift_detected: true,
    drift_score: 0.15,
    drift_type: 'distribution_change',
    previous_distribution: { mean: 12.5, std: 3.2 },
    current_distribution: { mean: 14.2, std: 3.8 },
    timestamp: '2023-01-05T08:00:00Z'
  }
];

const mockRetrainingRecommendations: RetrainingRecommendation[] = [
  {
    model_id: 'demand_forecast_v2',
    model_version: '2.1.0',
    recommendation_reason: 'Performance degradation detected',
    recommendation_type: 'performance_degradation',
    confidence_score: 0.85,
    suggested_action: 'retrain',
    threshold_met: true,
    timestamp: '2023-01-05T08:00:00Z'
  }
];

const mockModelLifecycleStatuses: ModelLifecycleStatus[] = [
  {
    model_id: 'demand_forecast_v2',
    model_name: 'Electricity Demand Forecasting Model',
    model_version: '2.1.0',
    model_status: 'production',
    forecasting_category: 'demand',
    training_timestamp: '2023-01-01T00:00:00Z',
    promotion_history: [],
    rollback_history: []
  }
];

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [energySummary, setEnergySummary] = useState<EnergySummary | null>(null);
  const [demandForecasts, setDemandForecasts] = useState<DemandForecast[]>([]);
  const [renewableForecasts, setRenewableForecasts] = useState<RenewableForecast[]>([]);
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [modelPerformances, setModelPerformances] = useState<ModelPerformance[]>([]);
  const [driftResults, setDriftResults] = useState<DriftDetectionResult[]>([]);
  const [retrainingRecommendations, setRetrainingRecommendations] = useState<RetrainingRecommendation[]>([]);
  const [modelLifecycleStatuses, setModelLifecycleStatuses] = useState<ModelLifecycleStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API loading
    setTimeout(() => {
      setEnergySummary(mockEnergySummary);
      setDemandForecasts(mockDemandForecasts);
      setRenewableForecasts(mockRenewableForecasts);
      setModels(mockModels);
      setModelPerformances(mockModelPerformances);
      setDriftResults(mockDriftResults);
      setRetrainingRecommendations(mockRetrainingRecommendations);
      setModelLifecycleStatuses(mockModelLifecycleStatuses);
      setLoading(false);
    }, 500);
  }, []);

  // Render Energy Overview Section
  const renderEnergyOverview = () => (
    <div className="energy-overview-section">
      <h2>Energy Overview</h2>

      {energySummary ? (
        <div className="energy-summary-cards">
          <div className="energy-card">
            <h3>Total Demand</h3>
            <p className="energy-value">{(energySummary.total_demand_mwh / 1000).toFixed(1)} TWh</p>
            <p className="energy-meta">Last updated: {new Date(energySummary.last_updated).toLocaleDateString()}</p>
          </div>

          <div className="energy-card">
            <h3>Total Generation</h3>
            <p className="energy-value">{(energySummary.total_generation_mw / 1000).toFixed(1)} GW</p>
            <p className="energy-meta">Last updated: {new Date(energySummary.last_updated).toLocaleDateString()}</p>
          </div>

          <div className="energy-card">
            <h3>Renewable Generation</h3>
            <p className="energy-value">{(energySummary.total_renewable_generation_mw / 1000).toFixed(1)} GW</p>
            <p className="energy-meta">Percentage: {energySummary.renewable_percentage.toFixed(1)}%</p>
          </div>

          <div className="energy-card">
            <h3>Historical Trend</h3>
            <div className="trend-chart-placeholder">
              <p>Historical demand trend chart</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="loading-placeholder">
          <p>Loading energy summary...</p>
        </div>
      )}

      <div className="data-quality-section">
        <h3>Data Quality Status</h3>
        <div className="quality-status">
          <div className="quality-item">
            <span className="quality-label">Demand Data:</span>
            <span className="quality-value good">Good</span>
          </div>
          <div className="quality-item">
            <span className="quality-label">Generation Data:</span>
            <span className="quality-value good">Good</span>
          </div>
          <div className="quality-item">
            <span className="quality-label">Weather Data:</span>
            <span className="quality-value warning">Medium</span>
          </div>
        </div>
      </div>
    </div>
  );

  // Render Demand Forecasting Section
  const renderDemandForecasting = () => (
    <div className="demand-forecasting-section">
      <h2>Demand Forecasting</h2>

      {demandForecasts.length > 0 ? (
        <div className="forecast-container">
          <div className="forecast-header">
            <h3>Actual vs Forecast</h3>
            <div className="forecast-controls">
              <select className="forecast-horizon-select">
                <option value="1">1 Day Horizon</option>
                <option value="7">7 Day Horizon</option>
                <option value="30">30 Day Horizon</option>
              </select>
            </div>
          </div>

          <div className="forecast-chart-placeholder">
            <p>Demand forecasting chart showing actual vs forecast values</p>
          </div>

          <div className="forecast-details">
            <div className="forecast-info">
              <h4>Model Information</h4>
              <div className="model-details">
                <p><strong>Model:</strong> {demandForecasts[0].model_name}</p>
                <p><strong>Version:</strong> {demandForecasts[0].model_version}</p>
                <p><strong>Forecast Date:</strong> {new Date(demandForecasts[0].forecast_timestamp).toLocaleString()}</p>
              </div>
            </div>

            <div className="forecast-metrics">
              <h4>Evaluation Metrics</h4>
              <div className="metrics-grid">
                <div className="metric-card">
                  <span className="metric-label">MAE</span>
                  <span className="metric-value">{demandForecasts[0].evaluation_metrics.mae.toFixed(2)}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">RMSE</span>
                  <span className="metric-value">{demandForecasts[0].evaluation_metrics.rmse.toFixed(2)}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">MAPE</span>
                  <span className="metric-value">{demandForecasts[0].evaluation_metrics.mape.toFixed(2)}%</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">sMAPE</span>
                  <span className="metric-value">{demandForecasts[0].evaluation_metrics.smape.toFixed(2)}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <p>No demand forecast data available</p>
        </div>
      )}
    </div>
  );

  // Render Renewable Forecasting Section
  const renderRenewableForecasting = () => (
    <div className="renewable-forecasting-section">
      <h2>Renewable Generation Forecasting</h2>

      <div className="renewable-note">
        <p className="note">
          ⚠️ Wind and solar generation are not separately available in test data.
          The renewable forecasts shown here use aggregate renewable generation data.
          Wind and solar forecasting capabilities are implemented as frameworks
          pending separate source data.
        </p>
      </div>

      {renewableForecasts.length > 0 ? (
        <div className="forecast-container">
          <div className="forecast-header">
            <h3>Renewable Generation Forecast</h3>
            <div className="forecast-controls">
              <select className="forecast-horizon-select">
                <option value="1">1 Day Horizon</option>
                <option value="7">7 Day Horizon</option>
                <option value="30">30 Day Horizon</option>
              </select>
            </div>
          </div>

          <div className="forecast-chart-placeholder">
            <p>Renewable generation forecasting chart</p>
          </div>

          <div className="forecast-details">
            <div className="forecast-info">
              <h4>Model Information</h4>
              <div className="model-details">
                <p><strong>Model:</strong> {renewableForecasts[0].model_name}</p>
                <p><strong>Version:</strong> {renewableForecasts[0].model_version}</p>
                <p><strong>Forecast Date:</strong> {new Date(renewableForecasts[0].forecast_timestamp).toLocaleString()}</p>
              </div>
            </div>

            <div className="forecast-metrics">
              <h4>Evaluation Metrics</h4>
              <div className="metrics-grid">
                <div className="metric-card">
                  <span className="metric-label">MAE</span>
                  <span className="metric-value">{renewableForecasts[0].evaluation_metrics.mae.toFixed(2)}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">RMSE</span>
                  <span className="metric-value">{renewableForecasts[0].evaluation_metrics.rmse.toFixed(2)}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">MAPE</span>
                  <span className="metric-value">{renewableForecasts[0].evaluation_metrics.mape.toFixed(2)}%</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">sMAPE</span>
                  <span className="metric-value">{renewableForecasts[0].evaluation_metrics.smape.toFixed(2)}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <p>No renewable forecast data available</p>
        </div>
      )}
    </div>
  );

  // Render Model Registry Section
  const renderModelRegistry = () => (
    <div className="model-registry-section">
      <h2>Model Registry</h2>

      <div className="registry-controls">
        <input type="text" placeholder="Search models..." className="search-input" />
        <select className="status-filter">
          <option value="">All Statuses</option>
          <option value="production">Production</option>
          <option value="candidate">Candidate</option>
          <option value="registered">Registered</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {models.length > 0 ? (
        <div className="models-table">
          <table>
            <thead>
              <tr>
                <th>Model ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Category</th>
                <th>Version</th>
                <th>Status</th>
                <th>Training Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map(model => (
                <tr key={model.model_id}>
                  <td>{model.model_id}</td>
                  <td>{model.model_name}</td>
                  <td>{model.model_type}</td>
                  <td>{model.forecasting_category}</td>
                  <td>{model.model_version}</td>
                  <td><span className={`status-badge ${model.model_status}`}>
                    {model.model_status}
                  </span></td>
                  <td>{new Date(model.training_timestamp).toLocaleDateString()}</td>
                  <td>
                    <button className="btn btn-small" onClick={() => navigate(`/models/${model.model_id}`)}>
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <p>No models registered</p>
        </div>
      )}
    </div>
  );

  // Render Model Performance Section
  const renderModelPerformance = () => (
    <div className="model-performance-section">
      <h2>Model Performance</h2>

      {modelPerformances.length > 0 ? (
        <div className="performance-container">
          <div className="performance-controls">
            <select className="model-select">
              <option value="">Select Model</option>
              {models.map(model => (
                <option key={model.model_id} value={model.model_id}>
                  {model.model_name} ({model.model_version})
                </option>
              ))}
            </select>
            <select className="horizon-select">
              <option value="">All Horizons</option>
              <option value="1">1 Day</option>
              <option value="7">7 Days</option>
              <option value="30">30 Days</option>
            </select>
          </div>

          <div className="performance-charts">
            <div className="chart-placeholder">
              <p>Performance metrics chart</p>
            </div>
            <div className="chart-placeholder">
              <p>Performance trend chart</p>
            </div>
          </div>

          <div className="performance-metrics">
            <h3>Latest Evaluation Results</h3>
            <div className="metrics-grid">
              {modelPerformances.map(performance => (
                <div key={`${performance.model_id}-${performance.model_version}`} className="metrics-card">
                  <h4>{performance.model_id} v{performance.model_version}</h4>
                  <div className="metric-item">
                    <span className="metric-label">MAE:</span>
                    <span className="metric-value">{performance.metrics.mae.toFixed(2)}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">RMSE:</span>
                    <span className="metric-value">{performance.metrics.rmse.toFixed(2)}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">MAPE:</span>
                    <span className="metric-value">{performance.metrics.mape.toFixed(2)}%</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">sMAPE:</span>
                    <span className="metric-value">{performance.metrics.smape.toFixed(2)}%</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">MBE:</span>
                    <span className="metric-value">{performance.metrics.mbe.toFixed(2)}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Period:</span>
                    <span className="metric-value">{performance.evaluation_period[0]} to {performance.evaluation_period[1]}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <p>No performance data available</p>
        </div>
      )}
    </div>
  );

  // Render Drift Monitoring Section
  const renderDriftMonitoring = () => (
    <div className="drift-monitoring-section">
      <h2>Drift Monitoring</h2>

      {driftResults.length > 0 ? (
        <div className="drift-container">
          <div className="drift-controls">
            <input type="text" placeholder="Filter features..." className="filter-input" />
          </div>

          <div className="drift-results">
            {driftResults.map((drift, index) => (
              <div key={index} className="drift-result-card">
                <div className="drift-header">
                  <h4>{drift.feature_name}</h4>
                  <span className={`drift-status ${drift.drift_detected ? 'detected' : 'stable'}`}>
                    {drift.drift_detected ? 'Drift Detected' : 'Stable'}
                  </span>
                </div>

                <div className="drift-details">
                  <div className="drift-metric">
                    <span className="metric-label">Drift Score:</span>
                    <span className="metric-value">{drift.drift_score.toFixed(3)}</span>
                  </div>
                  <div className="drift-metric">
                    <span className="metric-label">Type:</span>
                    <span className="metric-value">{drift.drift_type}</span>
                  </div>
                  <div className="drift-metric">
                    <span className="metric-label">Timestamp:</span>
                    <span className="metric-value">{new Date(drift.timestamp).toLocaleString()}</span>
                  </div>
                </div>

                <div className="drift-distribution">
                  <h5>Previous Distribution</h5>
                  <div className="distribution-values">
                    {Object.entries(drift.previous_distribution).map(([key, value]) => (
                      <div key={key} className="distribution-item">
                        <span className="dist-label">{key}:</span>
                        <span className="dist-value">{value.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>

                  <h5>Current Distribution</h5>
                  <div className="distribution-values">
                    {Object.entries(drift.current_distribution).map(([key, value]) => (
                      <div key={key} className="distribution-item">
                        <span className="dist-label">{key}:</span>
                        <span className="dist-value">{value.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <p>No drift detection results available</p>
        </div>
      )}
    </div>
  );

  // Render Retraining Management Section
  const renderRetrainingManagement = () => (
    <div className="retraining-management-section">
      <h2>Retraining Management</h2>

      {retrainingRecommendations.length > 0 ? (
        <div className="retraining-container">
          <div className="recommendations-list">
            {retrainingRecommendations.map((recommendation, index) => (
              <div key={index} className="recommendation-card">
                <div className="recommendation-header">
                  <h4>Model {recommendation.model_id}</h4>
                  <span className="recommendation-severity">
                    {recommendation.confidence_score > 0.8 ? 'High' : recommendation.confidence_score > 0.6 ? 'Medium' : 'Low'} Priority
                  </span>
                </div>

                <div className="recommendation-details">
                  <div className="recommendation-item">
                    <span className="item-label">Reason:</span>
                    <span className="item-value">{recommendation.recommendation_reason}</span>
                  </div>
                  <div className="recommendation-item">
                    <span className="item-label">Type:</span>
                    <span className="item-value">{recommendation.recommendation_type}</span>
                  </div>
                  <div className="recommendation-item">
                    <span className="item-label">Action:</span>
                    <span className="item-value">{recommendation.suggested_action}</span>
                  </div>
                  <div className="recommendation-item">
                    <span className="item-label">Confidence:</span>
                    <span className="item-value">{(recommendation.confidence_score * 100).toFixed(1)}%</span>
                  </div>
                  <div className="recommendation-item">
                    <span className="item-label">Timestamp:</span>
                    <span className="item-value">{new Date(recommendation.timestamp).toLocaleString()}</span>
                  </div>
                </div>

                <div className="recommendation-actions">
                  <button className="btn btn-primary">View Model</button>
                  <button className="btn btn-secondary">Schedule Retraining</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <p>No retraining recommendations available</p>
        </div>
      )}
    </div>
  );

  // Render Model Lifecycle Management Section
  const renderModelLifecycle = () => (
    <div className="model-lifecycle-section">
      <h2>Model Lifecycle Management</h2>

      <div className="lifecycle-controls">
        <select className="model-select">
          <option value="">Select Model</option>
          {models.map(model => (
            <option key={model.model_id} value={model.model_id}>
              {model.model_name} ({model.model_version})
            </option>
          ))}
        </select>
        <button className="btn btn-primary">Evaluate</button>
        <button className="btn btn-secondary">Promote</button>
        <button className="btn btn-danger">Rollback</button>
      </div>

      {modelLifecycleStatuses.length > 0 ? (
        <div className="lifecycle-history">
          <h3>Model Lifecycle History</h3>
          <div className="history-items">
            {modelLifecycleStatuses.map((status, index) => (
              <div key={index} className="history-item">
                <div className="history-header">
                  <h4>{status.model_name}</h4>
                  <span className={`status-badge ${status.model_status}`}>
                    {status.model_status}
                  </span>
                </div>

                <div className="history-details">
                  <div className="history-item">
                    <span className="history-label">Version:</span>
                    <span className="history-value">{status.model_version}</span>
                  </div>
                  <div className="history-item">
                    <span className="history-label">Category:</span>
                    <span className="history-value">{status.forecasting_category}</span>
                  </div>
                  <div className="history-item">
                    <span className="history-label">Training Date:</span>
                    <span className="history-value">{new Date(status.training_timestamp).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="history-actions">
                  <button className="btn btn-small">View Details</button>
                  <button className="btn btn-small">Promote</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <p>No lifecycle history available</p>
        </div>
      )}
    </div>
  );

  const renderContent = () => {
    switch(activeTab) {
      case 'overview': return renderEnergyOverview();
      case 'demand': return renderDemandForecasting();
      case 'renewable': return renderRenewableForecasting();
      case 'models': return renderModelRegistry();
      case 'performance': return renderModelPerformance();
      case 'drift': return renderDriftMonitoring();
      case 'retraining': return renderRetrainingManagement();
      case 'lifecycle': return renderModelLifecycle();
      default: return renderEnergyOverview();
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Irish Energy Analytics Dashboard</h1>
        <div className="dashboard-navigation">
          <button
            className={activeTab === 'overview' ? 'nav-active' : ''}
            onClick={() => setActiveTab('overview')}
          >
            Energy Overview
          </button>
          <button
            className={activeTab === 'demand' ? 'nav-active' : ''}
            onClick={() => setActiveTab('demand')}
          >
            Demand Forecasting
          </button>
          <button
            className={activeTab === 'renewable' ? 'nav-active' : ''}
            onClick={() => setActiveTab('renewable')}
          >
            Renewable Forecasting
          </button>
          <button
            className={activeTab === 'models' ? 'nav-active' : ''}
            onClick={() => setActiveTab('models')}
          >
            Model Registry
          </button>
          <button
            className={activeTab === 'performance' ? 'nav-active' : ''}
            onClick={() => setActiveTab('performance')}
          >
            Model Performance
          </button>
          <button
            className={activeTab === 'drift' ? 'nav-active' : ''}
            onClick={() => setActiveTab('drift')}
          >
            Drift Monitoring
          </button>
          <button
            className={activeTab === 'retraining' ? 'nav-active' : ''}
            onClick={() => setActiveTab('retraining')}
          >
            Retraining
          </button>
          <button
            className={activeTab === 'lifecycle' ? 'nav-active' : ''}
            onClick={() => setActiveTab('lifecycle')}
          >
            Model Lifecycle
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {renderContent()}
      </div>
    </div>
  );
};

export default Dashboard;