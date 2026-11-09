import React from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { HistoricalDemandData, HistoricalWeatherData, HistoricalGenerationData } from '../../types';

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

interface HistoricalChartsProps {
  demandData: HistoricalDemandData[];
  weatherData: HistoricalWeatherData[];
  generationData: HistoricalGenerationData[];
}

const HistoricalCharts: React.FC<HistoricalChartsProps> = ({
  demandData,
  weatherData,
  generationData
}) => {
  // Create renewable vs fossil generation data
  const renewableTypes = ['wind', 'solar'];
  const fossilTypes = ['gas', 'coal', 'oil'];

  const renewableData = generationData.filter(item => renewableTypes.includes(item.fuel_type));
  const fossilData = generationData.filter(item => fossilTypes.includes(item.fuel_type));

  // Group renewable data by fuel type
  const groupedRenewableData: Record<string, any[]> = {};
  renewableData.forEach((item: any) => {
    if (!groupedRenewableData[item.fuel_type]) {
      groupedRenewableData[item.fuel_type] = [];
    }
    groupedRenewableData[item.fuel_type].push({
      date: item.date,
      generation: item.total_generation
    });
  });

  // Group fossil data by fuel type
  const groupedFossilData: Record<string, any[]> = {};
  fossilData.forEach((item: any) => {
    if (!groupedFossilData[item.fuel_type]) {
      groupedFossilData[item.fuel_type] = [];
    }
    groupedFossilData[item.fuel_type].push({
      date: item.date,
      generation: item.total_generation
    });
  });

  return (
    <div className="historical-charts">
      <h2>Historical Charts</h2>

      {/* Demand Chart */}
      <SimpleLineChart
        title="Electricity Demand Over Time"
        data={demandData}
        dataKey="total_demand"
        name="Total Demand (MW)"
        color="#8884d8"
      />

      {/* Weather Chart */}
      {weatherData.length > 0 && (
        <SimpleLineChart
          title="Temperature Over Time"
          data={weatherData}
          dataKey="avg_temperature"
          name="Avg Temperature (°C)"
          color="#ff7300"
        />
      )}

      {/* Generation by Category */}
      {Object.entries(groupedRenewableData).length > 0 && (
        <div>
          {Object.entries(groupedRenewableData).map(([fuelType, fuelData]) => (
            <SimpleBarChart
              key={`renewable-${fuelType}`}
              title={`Renewable Generation by ${fuelType}`}
              data={fuelData}
              dataKey="generation"
              name="Generation (MW)"
              color="#00c49f"
            />
          ))}
        </div>
      )}

      {/* Fossil Generation */}
      {Object.entries(groupedFossilData).length > 0 && (
        <div>
          {Object.entries(groupedFossilData).map(([fuelType, fuelData]) => (
            <SimpleBarChart
              key={`fossil-${fuelType}`}
              title={`Fossil Generation by ${fuelType}`}
              data={fuelData}
              dataKey="generation"
              name="Generation (MW)"
              color="#ff4757"
            />
          ))}
        </div>
      )}

      {/* Renewable vs Fossil Comparison */}
      {renewableData.length > 0 && fossilData.length > 0 && (
        <SimpleBarChart
          title="Renewable vs Fossil Generation Comparison"
          data={renewableData.map(item => ({
            date: item.date,
            renewable: item.total_generation,
            fossil: fossilData.find(f => f.date === item.date)?.total_generation || 0
          }))}
          dataKey="renewable"
          name="Renewable (MW)"
          color="#00c49f"
        />
      )}
    </div>
  );
};

export default HistoricalCharts;