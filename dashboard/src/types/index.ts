export interface DemandData {
  date: string;
  total_demand: number;
  avg_demand: number;
  min_demand: number;
  max_demand: number;
}

export interface WeatherData {
  date: string;
  avg_temperature: number;
  min_temperature: number;
  max_temperature: number;
  avg_humidity: number;
}

export interface GenerationData {
  date: string;
  fuel_type: string;
  total_generation: number;
  avg_generation: number;
}

export interface DataQualityMetrics {
  data_type: string;
  date: string;
  bronze_processed: boolean;
  silver_processed: boolean;
  gold_processed: boolean;
  processing_timestamp: string;
}