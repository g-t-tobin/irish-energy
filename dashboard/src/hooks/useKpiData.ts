import { useEffect, useState } from 'react';
import { DataService } from '../services/dataService';

export interface KpiData {
  avg_electricity_demand: number | null;
  peak_electricity_demand: number | null;
  avg_total_generation: number | null;
  avg_renewable_generation: number | null;
  avg_temperature: number | null;
  renewable_share_percentage: number | null;
}

export const useKpiData = () => {
  const [data, setData] = useState<KpiData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await DataService.getKpiData();
        setData(result);
      } catch (err) {
        setError('Failed to fetch KPI data');
        console.error(err);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};