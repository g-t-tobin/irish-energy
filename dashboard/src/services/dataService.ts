import axios from 'axios';
import { DemandData, WeatherData, GenerationData, DataQualityMetrics } from '../types';

// Base URL for API endpoints (will be configured via environment variables)
const API_BASE_URL = (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000';

export class DataService {
  // Fetch demand data
  static async getDemandData(): Promise<DemandData[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/demand`);
      return response.data;
    } catch (error) {
      console.error('Error fetching demand data:', error);
      throw error;
    }
  }

  // Fetch weather data
  static async getWeatherData(): Promise<WeatherData[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/weather`);
      return response.data;
    } catch (error) {
      console.error('Error fetching weather data:', error);
      throw error;
    }
  }

  // Fetch generation data
  static async getGenerationData(): Promise<GenerationData[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/generation`);
      return response.data;
    } catch (error) {
      console.error('Error fetching generation data:', error);
      throw error;
    }
  }

  // Fetch data quality metrics
  static async getDataQualityMetrics(): Promise<DataQualityMetrics[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/metrics`);
      return response.data;
    } catch (error) {
      console.error('Error fetching data quality metrics:', error);
      throw error;
    }
  }

  // Fetch data for a specific date range
  static async getHistoricalData(startDate: string, endDate: string): Promise<any> {
    try {
      const response = await axios.get(`${API_BASE_URL}/historical`, {
        params: { start_date: startDate, end_date: endDate }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching historical data:', error);
      throw error;
    }
  }
}