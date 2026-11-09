export interface PipelineExecution {
  execution_id: string;
  pipeline_date: string;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  status: string;
  stage_results: {
    [stage: string]: {
      status: string;
      start_time: string;
      end_time: string;
      duration_seconds: number;
    };
  };
  failed_stages?: string[];
  retry_info?: {
    attempts: number;
    last_retry_time?: string;
  };
}

export interface QualityMetric {
  dataset_name: string;
  total_records: number;
  missing_values: number;
  data_quality_score: number;
  last_updated: string;
}

export interface Alert {
  alert_id: string;
  rule_id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  affected_dataset: string;
  execution_id: string;
  detection_timestamp: string;
  status: string;
  evidence?: any;
}

export interface Incident {
  incident_id: string;
  alert_ids: string[];
  title: string;
  description: string;
  severity: string;
  affected_datasets: string[];
  execution_id: string;
  creation_timestamp: string;
  last_updated_timestamp: string;
  resolution_timestamp?: string;
  status: string;
  resolution_notes?: string;
  history?: any[];
}

export interface ReconciliationReport {
  reconciliation_id: string;
  dataset_name: string;
  date_range: [string, string];
  overall_status: string;
  missing_dates: string[];
  incomplete_dates: string[];
  record_count_differences: {
    [date: string]: {
      bronze_count: number;
      silver_count: number;
      difference: number;
    };
  };
  quality_issues: string[];
  identified_discrepancies: string[];
  recommended_actions: string[];
}

export interface BackfillPlan {
  backfill_id: string;
  dataset_name: string;
  date_range: [string, string];
  missing_partitions: string[];
  required_stages: string[];
  dependencies: string[];
  expected_input_data: string[];
  expected_output_partitions: string[];
  estimated_workload: number;
  identified_risks: string[];
  execution_prerequisites: string[];
  dry_run: boolean;
}

export interface DatasetInventory {
  dataset_name: string;
  data_layer: string;
  earliest_available_date: string;
  latest_available_date: string;
  available_partitions: number;
  missing_partitions: number;
  total_file_sizes: number;
}

export interface DatasetDetails {
  dataset_name: string;
  data_layer: string;
  earliest_available_date: string;
  latest_available_date: string;
  available_partitions: string[];
  missing_partitions: string[];
  record_counts: { [date: string]: number };
  file_counts: { [date: string]: number };
  total_file_sizes: { [date: string]: number };
  schema_info: {
    fields: string[];
    types: string[];
  };
}

export interface AggregatedObservabilityMetrics {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  average_duration_seconds: number;
  execution_trends: {
    date: string;
    count: number;
    duration: number;
  }[];
  dataset_metrics: {
    dataset_name: string;
    record_count: number;
    last_updated: string;
  }[];
}