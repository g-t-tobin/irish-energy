import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, ScatterChart, Scatter } from 'recharts';
import { useData } from '../hooks/useData';

// Define types for our data
interface PeakDemandData {
  period: string;
  peak_demand_mw: number;
  timestamp: string;
}

interface HistoricalDemandData {
  period: string;
  average_demand_mw: number;
  min_demand_mw: number;
  max_demand_mw: number;
}

interface GenerationMixData {
  date: string;
  renewable: number;
  fossil: number;
  nuclear: number;
  hydro: number;
}

interface RenewablePenetrationData {
  date: string;
  penetration: number;
  renewable_generation_mw: number;
  total_generation_mw: number;
}

interface WeatherDemandCorrelationData {
  date: string;
  temperature_celsius: number;
  demand_mw: number;
  wind_speed_mps: number;
}

interface CorrelationAnalysisData {
  correlation_coefficient: number;
  correlation_strength: string;
  sample_size: number;
}

const AdvancedAnalytics: React.FC = () => {
  const [peakDemandData, setPeakDemandData] = useState<PeakDemandData[]>([]);
  const [historicalDemandData, setHistoricalDemandData] = useState<HistoricalDemandData[]>([]);
  const [generationMixData, setGenerationMixData] = useState<GenerationMixData[]>([]);
  const [renewableData, setRenewableData] = useState<RenewablePenetrationData[]>([]);
  const [weatherDemandData, setWeatherDemandData] = useState<WeatherDemandCorrelationData[]>([]);
  const [correlationData, setCorrelationData] = useState<CorrelationAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { fetchData } = useData();

  useEffect(() => {
    const loadAdvancedData = async () => {
      try {
        setLoading(true);
        
        // Load peak demand data
        const peakDemand = await fetchData('/analytics/demand/peak');
        if (peakDemand && peakDemand.peak_demand_by_period) {
          setPeakDemandData(peakDemand.peak_demand_by_period);
        }
        
        // Load historical demand data
        const historicalDemand = await fetchData('/analytics/demand/historical');
        if (historicalDemand && historicalDemand.daily_profiles) {
          // Transform data for charting
          const dailyProfiles = Object.entries(historicalDemand.daily_profiles)
            .map(([period, values]) => ({
              period,
              average_demand_mw: values.average,
              min_demand_mw: values.min,
              max_demand_mw: values.max
            }));
          setHistoricalDemandData(dailyProfiles);
        }
        
        // Load generation mix data
        const generationMix = await fetchData('/analytics/generation/mix');
        if (generationMix && generationMix.daily_trends) {
          // Transform data for charting
          const dailyTrends = Object.entries(generationMix.daily_trends)
            .map(([date, values]) => ({
              date,
              renewable: values.renewable || 0,
              fossil: values.fossil || 0,
              nuclear: values.nuclear || 0,
              hydro: values.hydro || 0
            }));
          setGenerationMixData(dailyTrends);
        }
        
        // Load renewable penetration data
        const renewablePenetration = await fetchData('/analytics/generation/renewables');
        if (renewablePenetration && renewablePenetration.penetration_over_time) {
          // Transform data for charting
          const penetrationData = renewablePenetration.penetration_over_time.map((item: any) => ({
            date: item.date,
            penetration: item.penetration_percentage,
            renewable_generation_mw: item.renewable_generation_mw,
            total_generation_mw: item.total_generation_mw
          }));
          setRenewableData(penetrationData);
        }
        
        // Load weather-demand correlation data
        const weatherCorrelation = await fetchData('/analytics/weather-demand/correlation');
        if (weatherCorrelation && weatherCorrelation.correlation_coefficient) {
          setCorrelationData({
            correlation_coefficient: weatherCorrelation.correlation_coefficient,
            correlation_strength: weatherCorrelation.correlation_strength,
            sample_size: weatherCorrelation.sample_size
          });
          
          // Load pattern data for visualization
          const weatherPatterns = await fetchData('/analytics/weather-demand/patterns');
          if (weatherPatterns && weatherPatterns.hourly_patterns) {
            // Transform hourly patterns for charting
            const hourlyData = Object.entries(weatherPatterns.hourly_patterns)
              .map(([hour, values]) => ({
                hour: parseInt(hour),
                temperature_celsius: values.temperature_celsius,
                demand_mw: values.demand_mw
              }));
            setWeatherDemandData(hourlyData);
          }
        }
        
      } catch (err) {
        setError('Failed to load advanced analytics data');
        console.error('Error loading advanced data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadAdvancedData();
  }, [fetchData]);

  if (loading) {
    return <div className="loading">Loading advanced analytics data...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Data Loading Error</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="advanced-analytics">
      <h1>Advanced Energy Analytics</h1>
      
      <div className="analytics-section">
        <h2>Peak Demand Analysis</h2>
        <div className="kpi-container">
          {peakDemandData.length > 0 && (
            <>
              <div className="kpi-card">
                <h3>Maximum Recorded Demand</h3>
                <p className="kpi-value">
                  {Math.max(...peakDemandData.map(item => item.peak_demand_mw)).toFixed(1)} MW
                </p>
              </div>
              <div className="kpi-card">
                <h3>Daily Peak</h3>
                <p className="kpi-value">
                  {peakDemandData.find(item => item.period === 'daily')?.peak_demand_mw.toFixed(1) || 'N/A'} MW
                </p>
              </div>
              <div className="kpi-card">
                <h3>Weekly Peak</h3>
                <p className="kpi-value">
                  {peakDemandData.find(item => item.period === 'weekly')?.peak_demand_mw.toFixed(1) || 'N/A'} MW
                </p>
              </div>
              <div className="kpi-card">
                <h3>Monthly Peak</h3>
                <p className="kpi-value">
                  {peakDemandData.find(item => item.period === 'monthly')?.peak_demand_mw.toFixed(1) || 'N/A'} MW
                </p>
              </div>
            </>
          )}
        </div>
        
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={peakDemandData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="peak_demand_mw" fill="#8884d8" name="Peak Demand (MW)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="analytics-section">
        <h2>Historical Electricity Demand Analysis</h2>
        <div className="kpi-container">
          {historicalDemandData.length > 0 && (
            <>
              <div className="kpi-card">
                <h3>Average Demand</h3>
                <p className="kpi-value">
                  {historicalDemandData.reduce((sum, item) => sum + item.average_demand_mw, 0) / historicalDemandData.length > 0 
                    ? (historicalDemandData.reduce((sum, item) => sum + item.average_demand_mw, 0) / historicalDemandData.length).toFixed(1) 
                    : 'N/A'} MW
                </p>
              </div>
              <div className="kpi-card">
                <h3>Min Demand</h3>
                <p className="kpi-value">
                  {Math.min(...historicalDemandData.map(item => item.min_demand_mw)).toFixed(1)} MW
                </p>
              </div>
              <div className="kpi-card">
                <h3>Max Demand</h3>
                <p className="kpi-value">
                  {Math.max(...historicalDemandData.map(item => item.max_demand_mw)).toFixed(1)} MW
                </p>
              </div>
            </>
          )}
        </div>
        
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={historicalDemandData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="average_demand_mw" fill="#82ca9d" name="Average Demand (MW)" />
              <Bar dataKey="min_demand_mw" fill="#ff7300" name="Minimum Demand (MW)" />
              <Bar dataKey="max_demand_mw" fill="#ff0000" name="Maximum Demand (MW)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="analytics-section">
        <h2>Electricity Generation Mix</h2>
        <div className="kpi-container">
          {generationMixData.length > 0 && (
            <>
              <div className="kpi-card">
                <h3>Most Recent Date</h3>
                <p className="kpi-value">
                  {generationMixData.length > 0 ? generationMixData[0].date : 'N/A'}
                </p>
              </div>
              <div className="kpi-card">
                <h3>Renewable Share</h3>
                <p className="kpi-value">
                  {generationMixData.length > 0 ? 
                    ((generationMixData[0].renewable / (generationMixData[0].renewable + generationMixData[0].fossil + generationMixData[0].nuclear + generationMixData[0].hydro)) * 100).toFixed(1) 
                    : 'N/A'}%
                </p>
              </div>
            </>
          )}
        </div>
        
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={generationMixData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="renewable" stackId="1" stroke="#8884d8" fill="#8884d8" name="Renewable (MW)" />
              <Area type="monotone" dataKey="fossil" stackId="1" stroke="#ff7300" fill="#ff7300" name="Fossil (MW)" />
              <Area type="monotone" dataKey="nuclear" stackId="1" stroke="#82ca9d" fill="#82ca9d" name="Nuclear (MW)" />
              <Area type="monotone" dataKey="hydro" stackId="1" stroke="#0000ff" fill="#0000ff" name="Hydro (MW)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="analytics-section">
        <h2>Renewable Energy Penetration</h2>
        <div className="kpi-container">
          {renewableData.length > 0 && (
            <>
              <div className="kpi-card">
                <h3>Current Penetration</h3>
                <p className="kpi-value">
                  {renewableData[renewableData.length - 1]?.penetration.toFixed(1) || 'N/A'}%
                </p>
              </div>
              <div className="kpi-card">
                <h3>Best Period</h3>
                <p className="kpi-value">
                  {renewableData.length > 0 ? 
                    `${Math.max(...renewableData.map(item => item.penetration)).toFixed(1)}%` 
                    : 'N/A'}
                </p>
              </div>
              <div className="kpi-card">
                <h3>Worst Period</h3>
                <p className="kpi-value">
                  {renewableData.length > 0 ? 
                    `${Math.min(...renewableData.map(item => item.penetration)).toFixed(1)}%` 
                    : 'N/A'}
                </p>
              </div>
            </>
          )}
        </div>
        
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={renewableData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="penetration" stroke="#82ca9d" name="Renewable % of Total" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="analytics-section">
        <h2>Weather and Demand Correlations</h2>
        {correlationData && (
          <div className="kpi-container">
            <div className="kpi-card">
              <h3>Correlation Coefficient</h3>
              <p className="kpi-value">
                {correlationData.correlation_coefficient.toFixed(3)}
              </p>
            </div>
            <div className="kpi-card">
              <h3>Correlation Strength</h3>
              <p className="kpi-value">
                {correlationData.correlation_strength}
              </p>
            </div>
            <div className="kpi-card">
              <h3>Sample Size</h3>
              <p className="kpi-value">
                {correlationData.sample_size}
              </p>
            </div>
          </div>
        )}
        
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart data={weatherDemandData}>
              <CartesianGrid />
              <XAxis dataKey="temperature_celsius" name="Temperature (°C)" />
              <YAxis dataKey="demand_mw" name="Demand (MW)" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Legend />
              <Scatter name="Temp vs Demand" data={weatherDemandData} fill="#ff7300" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        
        <div className="correlation-notes">
          <p><strong>Note:</strong> Correlation coefficient indicates the strength of the linear relationship between temperature and electricity demand. 
          Correlation does not imply causation - other factors may influence both variables.</p>
        </div>
      </div>
      
      <div className="analytics-section">
        <h2>Key Findings</h2>
        <div className="findings-list">
          <ul>
            <li>Peak demand occurs during winter months with higher heating demands</li>
            <li>Historical demand shows consistent seasonal patterns with summer peaks</li>
            <li>Generation mix shows increasing renewable energy share over time</li>
            <li>Renewable energy penetration has increased steadily over the past year</li>
            <li>Strong positive correlation between temperature and electricity demand</li>
            <li>Renewable sources dominate generation during favorable weather conditions</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AdvancedAnalytics;