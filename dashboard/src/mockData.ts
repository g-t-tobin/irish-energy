// Mock data for demonstration purposes
export const mockDemandData = [
  { date: '2023-01-01', total_demand: 3500, avg_demand: 3200, min_demand: 2800, max_demand: 3800 },
  { date: '2023-01-02', total_demand: 3700, avg_demand: 3400, min_demand: 3000, max_demand: 4000 },
  { date: '2023-01-03', total_demand: 3600, avg_demand: 3300, min_demand: 2900, max_demand: 3900 },
  { date: '2023-01-04', total_demand: 3800, avg_demand: 3500, min_demand: 3100, max_demand: 4100 },
  { date: '2023-01-05', total_demand: 3900, avg_demand: 3600, min_demand: 3200, max_demand: 4200 },
];

export const mockWeatherData = [
  { date: '2023-01-01', avg_temperature: 8.5, min_temperature: 4.2, max_temperature: 12.8, avg_humidity: 75 },
  { date: '2023-01-02', avg_temperature: 9.2, min_temperature: 5.1, max_temperature: 13.5, avg_humidity: 72 },
  { date: '2023-01-03', avg_temperature: 7.8, min_temperature: 3.5, max_temperature: 11.9, avg_humidity: 78 },
  { date: '2023-01-04', avg_temperature: 10.1, min_temperature: 6.3, max_temperature: 14.2, avg_humidity: 70 },
  { date: '2023-01-05', avg_temperature: 11.3, min_temperature: 7.2, max_temperature: 15.6, avg_humidity: 68 },
];

export const mockGenerationData = [
  { date: '2023-01-01', fuel_type: 'wind', total_generation: 1200, avg_generation: 1100 },
  { date: '2023-01-01', fuel_type: 'solar', total_generation: 800, avg_generation: 750 },
  { date: '2023-01-01', fuel_type: 'gas', total_generation: 1500, avg_generation: 1400 },
  { date: '2023-01-02', fuel_type: 'wind', total_generation: 1300, avg_generation: 1200 },
  { date: '2023-01-02', fuel_type: 'solar', total_generation: 900, avg_generation: 850 },
  { date: '2023-01-02', fuel_type: 'gas', total_generation: 1600, avg_generation: 1500 },
  { date: '2023-01-03', fuel_type: 'wind', total_generation: 1100, avg_generation: 1000 },
  { date: '2023-01-03', fuel_type: 'solar', total_generation: 700, avg_generation: 650 },
  { date: '2023-01-03', fuel_type: 'gas', total_generation: 1400, avg_generation: 1300 },
];

export const mockDataQualityMetrics = [
  { data_type: 'demand', date: '2023-01-01', bronze_processed: true, silver_processed: true, gold_processed: true, processing_timestamp: '2023-01-01T10:00:00Z' },
  { data_type: 'weather', date: '2023-01-01', bronze_processed: true, silver_processed: true, gold_processed: true, processing_timestamp: '2023-01-01T11:00:00Z' },
  { data_type: 'generation', date: '2023-01-01', bronze_processed: true, silver_processed: true, gold_processed: true, processing_timestamp: '2023-01-01T12:00:00Z' },
];