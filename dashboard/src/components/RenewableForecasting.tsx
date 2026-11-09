import React from 'react';
import { RenewableForecast } from '../types/mlopsTypes';

interface RenewableForecastingProps {
  forecasts: RenewableForecast[];
}

const RenewableForecasting: React.FC<RenewableForecastingProps> = ({ forecasts }) => {
  return (
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

      {forecasts.length > 0 ? (
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
                <p><strong>Model:</strong> {forecasts[0].model_name}</p>
                <p><strong>Version:</strong> {forecasts[0].model_version}</p>
                <p><strong>Forecast Date:</strong> {new Date(forecasts[0].forecast_timestamp).toLocaleString()}</p>
              </div>
            </div>

            <div className="forecast-metrics">
              <h4>Evaluation Metrics</h4>
              <div className="metrics-grid">
                <div className="metric-card">
                  <span className="metric-label">MAE</span>
                  <span className="metric-value">{forecasts[0].evaluation_metrics.mae.toFixed(2)}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">RMSE</span>
                  <span className="metric-value">{forecasts[0].evaluation_metrics.rmse.toFixed(2)}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">MAPE</span>
                  <span className="metric-value">{forecasts[0].evaluation_metrics.mape.toFixed(2)}%</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">sMAPE</span>
                  <span className="metric-value">{forecasts[0].evaluation_metrics.smape.toFixed(2)}%</span>
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
};

export default RenewableForecasting;