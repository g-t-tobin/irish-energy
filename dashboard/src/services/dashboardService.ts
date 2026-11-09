import axios from 'axios';
import {
  PipelineExecution,
  QualityMetric,
  Alert,
  Incident,
  ReconciliationReport,
  BackfillPlan,
  DatasetInventory,
  DatasetDetails,
  AggregatedObservabilityMetrics
} from '../types/dashboardTypes';

// Base URL for API endpoints (will be configured via environment variables)
const API_BASE_URL = (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000';

export class DashboardService {
  // Pipeline Execution APIs
  static async getPipelineExecutions(limit: number = 20, statusFilter?: string): Promise<PipelineExecution[]> {
    try {
      const url = `${API_BASE_URL}/observability/executions`;
      const params: any = { limit };
      if (statusFilter) params.status_filter = statusFilter;

      const response = await axios.get(url, { params });
      // Convert response to our internal format
      return response.data.map((item: any) => ({
        execution_id: item.execution_id,
        pipeline_date: item.pipeline_date,
        start_time: item.start_timestamp,
        end_time: item.end_timestamp,
        duration_seconds: item.duration_seconds,
        status: item.execution_status,
        stage_results: {} // Will be populated by detailed view if needed
      }));
    } catch (error) {
      console.error('Error fetching pipeline executions:', error);
      throw error;
    }
  }

  static async getPipelineExecution(executionId: string): Promise<PipelineExecution> {
    try {
      // For now, we'll use the same endpoint as getPipelineExecutions to simulate
      // In a real implementation, this would be a specific endpoint like:
      // const url = `${API_BASE_URL}/observability/executions/${executionId}`;
      const executions = await this.getPipelineExecutions(100); // Get all to find the specific one
      const execution = executions.find(e => e.execution_id === executionId);
      if (!execution) {
        throw new Error(`Pipeline execution ${executionId} not found`);
      }
      return execution;
    } catch (error) {
      console.error(`Error fetching pipeline execution ${executionId}:`, error);
      throw error;
    }
  }

  // Quality APIs
  static async getQualityMetrics(): Promise<QualityMetric[]> {
    try {
      const url = `${API_BASE_URL}/quality`;
      const response = await axios.get(url);
      // Convert response to our internal format
      return response.data.map((item: any) => ({
        dataset_name: item.dataset_name,
        total_records: item.total_records,
        missing_values: item.missing_values,
        data_quality_score: item.data_quality_score,
        last_updated: item.last_updated
      }));
    } catch (error) {
      console.error('Error fetching quality metrics:', error);
      throw error;
    }
  }

  // Alerting APIs
  static async getAlerts(limit: number = 100, severity?: string): Promise<Alert[]> {
    try {
      const url = `${API_BASE_URL}/alerts/alerts`;
      const params: any = { limit };
      if (severity) params.severity = severity;

      const response = await axios.get(url, { params });
      // Convert response to our internal format
      return response.data.map((item: any) => ({
        alert_id: item.alert_id,
        rule_id: item.rule_id,
        category: item.category,
        severity: item.severity,
        title: item.title,
        description: item.description,
        affected_dataset: item.affected_dataset,
        execution_id: item.execution_id,
        detection_timestamp: item.detection_timestamp,
        status: item.status,
        evidence: item.evidence
      }));
    } catch (error) {
      console.error('Error fetching alerts:', error);
      throw error;
    }
  }

  static async getIncidents(limit: number = 100, status?: string): Promise<Incident[]> {
    try {
      const url = `${API_BASE_URL}/alerts/incidents`;
      const params: any = { limit };
      if (status) params.status = status;

      const response = await axios.get(url, { params });
      // Convert response to our internal format
      return response.data.map((item: any) => ({
        incident_id: item.incident_id,
        alert_ids: item.alert_ids,
        title: item.title,
        description: item.description,
        severity: item.severity,
        affected_datasets: item.affected_datasets,
        execution_id: item.execution_id,
        creation_timestamp: item.creation_timestamp,
        last_updated_timestamp: item.last_updated_timestamp,
        resolution_timestamp: item.resolution_timestamp,
        status: item.status,
        resolution_notes: item.resolution_notes,
        history: item.history
      }));
    } catch (error) {
      console.error('Error fetching incidents:', error);
      throw error;
    }
  }

  static async acknowledgeIncident(incidentId: string, notes?: string): Promise<void> {
    try {
      const url = `${API_BASE_URL}/alerts/incidents/${incidentId}/acknowledge`;
      await axios.post(url, { notes });
    } catch (error) {
      console.error(`Error acknowledging incident ${incidentId}:`, error);
      throw error;
    }
  }

  static async resolveIncident(incidentId: string, resolutionNotes?: string): Promise<void> {
    try {
      const url = `${API_BASE_URL}/alerts/incidents/${incidentId}/resolve`;
      await axios.post(url, { resolution_notes: resolutionNotes });
    } catch (error) {
      console.error(`Error resolving incident ${incidentId}:`, error);
      throw error;
    }
  }

  // Reconciliation APIs
  static async getReconciliationSummary(): Promise<ReconciliationReport[]> {
    try {
      const url = `${API_BASE_URL}/reconciliation/summary`;
      const response = await axios.get(url);
      // Convert response to our internal format
      return response.data.map((item: any) => ({
        reconciliation_id: `${item.dataset_name}_recon`,
        dataset_name: item.dataset_name,
        date_range: [item.earliest_available_date, item.latest_available_date],
        overall_status: 'UNKNOWN', // Not in response, need to determine
        missing_dates: [],
        incomplete_dates: [],
        record_count_differences: {},
        quality_issues: [],
        identified_discrepancies: [],
        recommended_actions: []
      }));
    } catch (error) {
      console.error('Error fetching reconciliation summary:', error);
      throw error;
    }
  }

  static async getDatasetInfo(datasetName: string, dataLayer: string = 'bronze'): Promise<DatasetDetails> {
    try {
      const url = `${API_BASE_URL}/reconciliation/datasets/${datasetName}`;
      const params = { data_layer: dataLayer };

      const response = await axios.get(url, { params });
      // Convert response to our internal format
      return {
        dataset_name: response.data.dataset_name,
        data_layer: response.data.data_layer,
        earliest_available_date: response.data.earliest_available_date,
        latest_available_date: response.data.latest_available_date,
        available_partitions: response.data.available_partitions,
        missing_partitions: response.data.missing_partitions,
        record_counts: response.data.record_counts,
        file_counts: response.data.file_counts,
        total_file_sizes: response.data.total_file_sizes,
        schema_info: {
          fields: [],
          types: []
        }
      };
    } catch (error) {
      console.error(`Error fetching dataset info for ${datasetName}:`, error);
      throw error;
    }
  }

  static async runReconciliation(datasetName: string, startDate: string, endDate: string, dataLayer: string = 'bronze'): Promise<ReconciliationReport> {
    try {
      const url = `${API_BASE_URL}/reconciliation/reconciliation/run`;
      const response = await axios.post(url, {
        dataset_name: datasetName,
        start_date: startDate,
        end_date: endDate,
        data_layer: dataLayer
      });
      // Convert response to our internal format
      return {
        reconciliation_id: response.data.reconciliation_id,
        dataset_name: response.data.dataset_name,
        date_range: response.data.date_range,
        overall_status: response.data.overall_status,
        missing_dates: response.data.missing_dates,
        incomplete_dates: response.data.incomplete_dates,
        record_count_differences: response.data.record_count_differences,
        quality_issues: [],
        identified_discrepancies: [],
        recommended_actions: []
      };
    } catch (error) {
      console.error(`Error running reconciliation for ${datasetName}:`, error);
      throw error;
    }
  }

  // Backfill APIs
  static async createBackfillPlan(datasetName: string, startDate: string, endDate: string, dryRun: boolean = true): Promise<BackfillPlan> {
    try {
      const url = `${API_BASE_URL}/reconciliation/backfills/plan`;
      const response = await axios.post(url, {
        dataset_name: datasetName,
        start_date: startDate,
        end_date: endDate,
        dry_run: dryRun
      });
      // Convert response to our internal format
      return {
        backfill_id: response.data.backfill_id,
        dataset_name: response.data.dataset_name,
        date_range: response.data.date_range,
        missing_partitions: response.data.missing_partitions,
        required_stages: response.data.required_stages,
        dependencies: response.data.dependencies,
        expected_input_data: response.data.expected_input_data,
        expected_output_partitions: response.data.expected_output_partitions,
        estimated_workload: response.data.estimated_workload,
        identified_risks: response.data.identified_risks,
        execution_prerequisites: response.data.execution_prerequisites,
        dry_run: response.data.dry_run
      };
    } catch (error) {
      console.error(`Error creating backfill plan for ${datasetName}:`, error);
      throw error;
    }
  }

  static async getBackfillPlans(): Promise<BackfillPlan[]> {
    try {
      const url = `${API_BASE_URL}/reconciliation/backfills`;
      const response = await axios.get(url);
      // Convert response to our internal format
      return response.data.map((item: any) => ({
        backfill_id: item.backfill_id,
        dataset_name: item.dataset_name,
        date_range: item.date_range,
        missing_partitions: item.missing_partitions,
        required_stages: item.required_stages,
        dependencies: item.dependencies,
        expected_input_data: item.expected_input_data,
        expected_output_partitions: item.expected_output_partitions,
        estimated_workload: item.estimated_workload,
        identified_risks: item.identified_risks,
        execution_prerequisites: item.execution_prerequisites,
        dry_run: item.dry_run
      }));
    } catch (error) {
      console.error('Error fetching backfill plans:', error);
      throw error;
    }
  }

  // Dataset APIs
  static async getAllDatasets(): Promise<string[]> {
    try {
      const url = `${API_BASE_URL}/reconciliation/datasets`;
      const response = await axios.get(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching datasets:', error);
      throw error;
    }
  }

  static async getDatasetInventory(datasetName: string, dataLayer: string = 'bronze'): Promise<DatasetInventory> {
    try {
      const url = `${API_BASE_URL}/reconciliation/datasets/${datasetName}`;
      const params = { data_layer: dataLayer };

      const response = await axios.get(url, { params });
      // Convert response to our internal format
      return {
        dataset_name: response.data.dataset_name,
        data_layer: response.data.data_layer,
        earliest_available_date: response.data.earliest_available_date,
        latest_available_date: response.data.latest_available_date,
        available_partitions: response.data.available_partitions.length,
        missing_partitions: response.data.missing_partitions.length,
        total_file_sizes: Object.values(response.data.total_file_sizes).reduce((a: any, b: any) => a + b, 0)
      };
    } catch (error) {
      console.error(`Error fetching dataset inventory for ${datasetName}:`, error);
      throw error;
    }
  }

  // Observability APIs
  static async getAggregatedMetrics(timeWindowHours: number = 24): Promise<AggregatedObservabilityMetrics> {
    try {
      const url = `${API_BASE_URL}/observability/metrics/aggregated`;
      const params = { time_window_hours: timeWindowHours };

      const response = await axios.get(url, { params });
      // Convert response to our internal format
      return {
        total_executions: response.data.total_executions,
        successful_executions: response.data.successful_executions,
        failed_executions: response.data.failed_executions,
        average_duration_seconds: response.data.average_duration_seconds,
        execution_trends: response.data.execution_trends,
        dataset_metrics: response.data.dataset_metrics.map((item: any) => ({
          dataset_name: item.dataset_name,
          record_count: item.record_count,
          last_updated: item.last_updated
        }))
      };
    } catch (error) {
      console.error('Error fetching aggregated metrics:', error);
      throw error;
    }
  }

  static async getRecentObservabilityData(limit: number = 20): Promise<any[]> {
    try {
      const url = `${API_BASE_URL}/observability/recent`;
      const params = { limit };

      const response = await axios.get(url, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching recent observability data:', error);
      throw error;
    }
  }
}