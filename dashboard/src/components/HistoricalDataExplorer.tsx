import React, { useState, useEffect } from 'react';
import DateRangeSelector from './DateRangeSelector';
import HistoricalCharts from './charts/HistoricalCharts';
import HistoricalDataTable from './HistoricalDataTable';
import { useHistoricalData } from '../hooks/useHistoricalData';
import { exportToCSV } from '../utils/csvExporter';

const HistoricalDataExplorer: React.FC = () => {
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [csvFilename, setCsvFilename] = useState<string>('');

  const { data, loading, error } = useHistoricalData(startDate, endDate);

  // Set initial dates to last 7 days if not already set
  useEffect(() => {
    if (!startDate && !endDate) {
      const today = new Date();
      const endDateObj = new Date(today);
      const startDateObj = new Date(today);
      startDateObj.setDate(startDateObj.getDate() - 7);

      setStartDate(startDateObj.toISOString().split('T')[0]);
      setEndDate(endDateObj.toISOString().split('T')[0]);
    }
  }, [startDate, endDate]);

  // Update CSV filename when dates change
  useEffect(() => {
    if (startDate && endDate) {
      setCsvFilename(`historical-data-${startDate}-to-${endDate}.csv`);
    }
  }, [startDate, endDate]);

  const handleDatesChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
  };

  const handleExportCSV = () => {
    if (!data || !csvFilename) return;

    // Combine all data by date
    const combinedData: Record<string, any> = {};

    // Add demand data
    data.demand.forEach(item => {
      if (!combinedData[item.date]) {
        combinedData[item.date] = { date: item.date };
      }
      combinedData[item.date].demand = item.total_demand;
      combinedData[item.date].avg_demand = item.avg_demand;
      combinedData[item.date].min_demand = item.min_demand;
      combinedData[item.date].max_demand = item.max_demand;
    });

    // Add weather data
    data.weather.forEach(item => {
      if (!combinedData[item.date]) {
        combinedData[item.date] = { date: item.date };
      }
      combinedData[item.date].avg_temperature = item.avg_temperature;
      combinedData[item.date].min_temperature = item.min_temperature;
      combinedData[item.date].max_temperature = item.max_temperature;
      combinedData[item.date].avg_humidity = item.avg_humidity;
    });

    // Add generation data by fuel type
    const fuelTypes = Array.from(new Set(data.generation.map(item => item.fuel_type)));
    fuelTypes.forEach(fuelType => {
      const fuelData = data.generation.filter(item => item.fuel_type === fuelType);
      fuelData.forEach(item => {
        if (combinedData[item.date]) {
          combinedData[item.date][`generation_${fuelType}`] = item.total_generation;
        }
      });
    });

    const sortedData = Object.values(combinedData).sort((a, b) =>
      new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    exportToCSV(sortedData, csvFilename);
  };

  if (loading) {
    return <div className="loading">Loading historical data...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="historical-data-explorer">
      <h1>Historical Energy Data Explorer</h1>

      <DateRangeSelector
        onDatesChange={handleDatesChange}
        initialStartDate={startDate}
        initialEndDate={endDate}
      />

      <div className="actions">
        <button onClick={handleExportCSV} disabled={!data || data.demand.length === 0}>
          Export to CSV
        </button>
      </div>

      {data && data.demand.length > 0 && (
        <>
          <HistoricalCharts
            demandData={data.demand}
            weatherData={data.weather}
            generationData={data.generation}
          />
          <HistoricalDataTable
            demandData={data.demand}
            weatherData={data.weather}
            generationData={data.generation}
          />
        </>
      )}

      {data && data.demand.length === 0 && (
        <div className="empty-state">
          No historical data available for the selected period.
        </div>
      )}
    </div>
  );
};

export default HistoricalDataExplorer;