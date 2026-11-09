import React from 'react';
import { useKpiData } from '../hooks/useKpiData';

interface KpiCardProps {
  title: string;
  value: number | null;
  unit: string;
  description?: string;
}

const KpiCard: React.FC<KpiCardProps> = ({ title, value, unit, description }) => {
  return (
    <div className="kpi-card">
      <h3>{title}</h3>
      <div className="kpi-value">
        {value !== null ? (
          <>
            <span className="value">{value.toLocaleString()}</span>
            <span className="unit">{unit}</span>
          </>
        ) : (
          <span className="no-data">No data available</span>
        )}
      </div>
      {description && <p className="kpi-description">{description}</p>}
    </div>
  );
};

const KpiOverview: React.FC = () => {
  const { data, loading, error } = useKpiData();

  if (loading) {
    return (
      <div className="kpi-overview">
        <h2>Dashboard Overview</h2>
        <div className="kpi-grid">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="kpi-card-placeholder">
              <div className="placeholder-skeleton"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="kpi-overview">
        <h2>Dashboard Overview</h2>
        <div className="kpi-grid">
          <div className="kpi-card-error">
            <p>Error loading KPI data: {error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="kpi-overview">
        <h2>Dashboard Overview</h2>
        <div className="kpi-grid">
          <div className="kpi-card-empty">
            <p>No KPI data available</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="kpi-overview">
      <h2>Dashboard Overview</h2>
      <div className="kpi-grid">
        <KpiCard
          title="Avg Electricity Demand"
          value={data.avg_electricity_demand}
          unit="MW"
          description="Average electricity demand across selected period"
        />
        <KpiCard
          title="Peak Electricity Demand"
          value={data.peak_electricity_demand}
          unit="MW"
          description="Highest electricity demand recorded"
        />
        <KpiCard
          title="Avg Total Generation"
          value={data.avg_total_generation}
          unit="MW"
          description="Average total electricity generation"
        />
        <KpiCard
          title="Avg Renewable Generation"
          value={data.avg_renewable_generation}
          unit="MW"
          description="Average renewable energy generation"
        />
        <KpiCard
          title="Avg Temperature"
          value={data.avg_temperature}
          unit="°C"
          description="Average temperature during selected period"
        />
        <KpiCard
          title="Renewable Share"
          value={data.renewable_share_percentage}
          unit="%"
          description="Percentage of renewable energy in total generation"
        />
      </div>
    </div>
  );
};

export default KpiOverview;