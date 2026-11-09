import React from 'react';
import { ModelLifecycleStatus } from '../types/mlopsTypes';

interface ModelLifecycleProps {
  modelStatuses: ModelLifecycleStatus[];
}

const ModelLifecycle: React.FC<ModelLifecycleProps> = ({ modelStatuses }) => {
  return (
    <div className="model-lifecycle-section">
      <h2>Model Lifecycle Management</h2>

      <div className="lifecycle-controls">
        <select className="model-select">
          <option value="">Select Model</option>
          {modelStatuses.map(status => (
            <option key={status.model_id} value={status.model_id}>
              {status.model_name} ({status.model_version})
            </option>
          ))}
        </select>
        <button className="btn btn-primary">Evaluate</button>
        <button className="btn btn-secondary">Promote</button>
        <button className="btn btn-danger">Rollback</button>
      </div>

      {modelStatuses.length > 0 ? (
        <div className="lifecycle-history">
          <h3>Model Lifecycle History</h3>
          <div className="history-items">
            {modelStatuses.map((status, index) => (
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
};

export default ModelLifecycle;