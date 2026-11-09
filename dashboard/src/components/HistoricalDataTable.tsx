import React from 'react';
import { HistoricalDemandData, HistoricalWeatherData, HistoricalGenerationData } from '../types';

interface HistoricalDataTableProps {
  demandData: HistoricalDemandData[];
  weatherData: HistoricalWeatherData[];
  generationData: HistoricalGenerationData[];
}

const HistoricalDataTable: React.FC<HistoricalDataTableProps> = ({
  demandData,
  weatherData,
  generationData
}) => {
  // Combine all data by date
  const combinedData: Record<string, any> = {};

  // Add demand data
  demandData.forEach(item => {
    if (!combinedData[item.date]) {
      combinedData[item.date] = { date: item.date };
    }
    combinedData[item.date].demand = item.total_demand;
    combinedData[item.date].avg_demand = item.avg_demand;
    combinedData[item.date].min_demand = item.min_demand;
    combinedData[item.date].max_demand = item.max_demand;
  });

  // Add weather data
  weatherData.forEach(item => {
    if (!combinedData[item.date]) {
      combinedData[item.date] = { date: item.date };
    }
    combinedData[item.date].avg_temperature = item.avg_temperature;
    combinedData[item.date].min_temperature = item.min_temperature;
    combinedData[item.date].max_temperature = item.max_temperature;
    combinedData[item.date].avg_humidity = item.avg_humidity;
  });

  // Add generation data by fuel type
  const fuelTypes = Array.from(new Set(generationData.map(item => item.fuel_type)));
  fuelTypes.forEach(fuelType => {
    const fuelData = generationData.filter(item => item.fuel_type === fuelType);
    fuelData.forEach(item => {
      if (combinedData[item.date]) {
        combinedData[item.date][`generation_${fuelType}`] = item.total_generation;
      }
    });
  });

  const sortedData = Object.values(combinedData).sort((a, b) =>
    new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  if (sortedData.length === 0) {
    return <div>No historical data available for the selected period.</div>;
  }

  return (
    <div className="historical-data-table">
      <h2>Historical Data Table</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Demand (MW)</th>
            <th>Avg Demand (MW)</th>
            <th>Min Demand (MW)</th>
            <th>Max Demand (MW)</th>
            <th>Avg Temp (°C)</th>
            <th>Min Temp (°C)</th>
            <th>Max Temp (°C)</th>
            <th>Avg Humidity (%)</th>
            {fuelTypes.map(type => (
              <th key={`gen-${type}`}>Generation {type.toUpperCase()} (MW)</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row: any, index: number) => (
            <tr key={index}>
              <td>{row.date}</td>
              <td>{row.demand?.toFixed(2) || '-'}</td>
              <td>{row.avg_demand?.toFixed(2) || '-'}</td>
              <td>{row.min_demand?.toFixed(2) || '-'}</td>
              <td>{row.max_demand?.toFixed(2) || '-'}</td>
              <td>{row.avg_temperature?.toFixed(2) || '-'}</td>
              <td>{row.min_temperature?.toFixed(2) || '-'}</td>
              <td>{row.max_temperature?.toFixed(2) || '-'}</td>
              <td>{row.avg_humidity?.toFixed(2) || '-'}</td>
              {fuelTypes.map(type => (
                <td key={`gen-${type}`}>{row[`generation_${type}`]?.toFixed(2) || '-'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default HistoricalDataTable;