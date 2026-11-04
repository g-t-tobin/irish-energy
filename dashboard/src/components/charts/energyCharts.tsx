import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useDemandData, useWeatherData, useGenerationData } from '../../hooks/useData';

interface ChartProps {
  title: string;
  data: any[];
  dataKey: string;
  name: string;
  color: string;
}

const SimpleLineChart: React.FC<ChartProps> = ({ title, data, dataKey, name, color }) => {
  return (
    <div className="chart-container">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey={dataKey} name={name} stroke={color} activeDot={{ r: 8 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

const SimpleBarChart: React.FC<ChartProps> = ({ title, data, dataKey, name, color }) => {
  return (
    <div className="chart-container">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey={dataKey} name={name} fill={color} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

const DemandChart: React.FC = () => {
  const { data, loading, error } = useDemandData();

  if (loading) return <div>Loading demand chart...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <SimpleLineChart 
      title="Energy Demand Over Time" 
      data={data} 
      dataKey="total_demand" 
      name="Total Demand (MW)" 
      color="#8884d8" 
    />
  );
};

const WeatherChart: React.FC = () => {
  const { data, loading, error } = useWeatherData();

  if (loading) return <div>Loading weather chart...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <SimpleLineChart 
      title="Temperature Over Time" 
      data={data} 
      dataKey="avg_temperature" 
      name="Avg Temperature (°C)" 
      color="#ff7300" 
    />
  );
};

const GenerationChart: React.FC = () => {
  const { data, loading, error } = useGenerationData();

  if (loading) return <div>Loading generation chart...</div>;
  if (error) return <div>Error: {error}</div>;

  // Group data by fuel type for bar chart
  const groupedData: Record<string, any[]> = {};
  
  data.forEach((item: any) => {
    if (!groupedData[item.fuel_type]) {
      groupedData[item.fuel_type] = [];
    }
    groupedData[item.fuel_type].push({
      date: item.date,
      generation: item.total_generation
    });
  });

  return (
    <div>
      {Object.entries(groupedData).map(([fuelType, fuelData]) => (
        <SimpleBarChart 
          key={fuelType}
          title={`Generation by ${fuelType}`} 
          data={fuelData} 
          dataKey="generation" 
          name="Generation (MW)" 
          color="#0088fe" 
        />
      ))}
    </div>
  );
};

export { DemandChart, WeatherChart, GenerationChart };