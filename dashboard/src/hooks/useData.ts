import { useEffect, useState } from 'react';
import { DemandData, WeatherData, GenerationData, DataQualityMetrics } from '../types';
import { DataService } from '../services/dataService';
import { mockDemandData, mockWeatherData, mockGenerationData, mockDataQualityMetrics } from '../mockData';

export const useDemandData = () => {
  const [data, setData] = useState<DemandData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Try to fetch from API first, fall back to mock data if it fails
        try {
          const result = await DataService.getDemandData();
          setData(result);
        } catch (err) {
          console.warn('Failed to fetch from API, using mock data for demand');
          setData(mockDemandData);
        }
      } catch (err) {
        setError('Failed to fetch demand data');
        console.error(err);
        // Fall back to mock data on error
        setData(mockDemandData);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};

export const useWeatherData = () => {
  const [data, setData] = useState<WeatherData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Try to fetch from API first, fall back to mock data if it fails
        try {
          const result = await DataService.getWeatherData();
          setData(result);
        } catch (err) {
          console.warn('Failed to fetch from API, using mock data for weather');
          setData(mockWeatherData);
        }
      } catch (err) {
        setError('Failed to fetch weather data');
        console.error(err);
        // Fall back to mock data on error
        setData(mockWeatherData);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};

export const useGenerationData = () => {
  const [data, setData] = useState<GenerationData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Try to fetch from API first, fall back to mock data if it fails
        try {
          const result = await DataService.getGenerationData();
          setData(result);
        } catch (err) {
          console.warn('Failed to fetch from API, using mock data for generation');
          setData(mockGenerationData);
        }
      } catch (err) {
        setError('Failed to fetch generation data');
        console.error(err);
        // Fall back to mock data on error
        setData(mockGenerationData);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};

export const useDataQualityMetrics = () => {
  const [data, setData] = useState<DataQualityMetrics[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Try to fetch from API first, fall back to mock data if it fails
        try {
          const result = await DataService.getDataQualityMetrics();
          setData(result);
        } catch (err) {
          console.warn('Failed to fetch from API, using mock data for metrics');
          setData(mockDataQualityMetrics);
        }
      } catch (err) {
        setError('Failed to fetch data quality metrics');
        console.error(err);
        // Fall back to mock data on error
        setData(mockDataQualityMetrics);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};