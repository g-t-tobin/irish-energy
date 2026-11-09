import { useEffect, useState } from 'react';
import { HistoricalDataResponse } from '../types';
import { DataService } from '../services/dataService';

export const useHistoricalData = (startDate: string, endDate: string) => {
  const [data, setData] = useState<HistoricalDataResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!startDate || !endDate) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const result = await DataService.getHistoricalData(startDate, endDate);
        setData(result);
      } catch (err) {
        setError('Failed to fetch historical data');
        console.error(err);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [startDate, endDate]);

  return { data, loading, error };
};