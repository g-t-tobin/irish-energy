import { DemandChart, WeatherChart, GenerationChart } from './charts/energyCharts';
import { useDataQualityMetrics } from '../hooks/useData';

const Dashboard: React.FC = () => {
  const { data: metrics, loading, error } = useDataQualityMetrics();

  if (loading) return <div>Loading dashboard...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="dashboard">
      <h2>Irish Energy Analytics Dashboard</h2>
      
      <div className="charts-section">
        <DemandChart />
        <WeatherChart />
        <GenerationChart />
      </div>
      
      <div className="metrics-section">
        <h3>Data Quality Metrics</h3>
        <table>
          <thead>
            <tr>
              <th>Data Type</th>
              <th>Date</th>
              <th>Bronze Processed</th>
              <th>Silver Processed</th>
              <th>Gold Processed</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((metric, index) => (
              <tr key={index}>
                <td>{metric.data_type}</td>
                <td>{metric.date}</td>
                <td>{metric.bronze_processed ? 'Yes' : 'No'}</td>
                <td>{metric.silver_processed ? 'Yes' : 'No'}</td>
                <td>{metric.gold_processed ? 'Yes' : 'No'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;