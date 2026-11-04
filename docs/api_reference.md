# Irish Energy Analytics Data Platform - API Reference

## Overview
This document provides reference information for the APIs and interfaces used in the Irish Energy Analytics Data Platform.

## Data Ingestion APIs

### EirGrid API Client
**Module**: `src/ingestion/eirgrid_client.py`

#### Methods
- `get_demand_data(date: str)` - Fetch electricity demand data for a specific date
- `get_generation_data(date: str)` - Fetch electricity generation data for a specific date
- `validate_data(data: dict)` - Validate data against expected schema

#### Response Format
```json
{
  "date": "2023-01-01",
  "demand_values": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "value": 1000
    }
  ]
}
```

### Open-Meteo API Client
**Module**: `src/ingestion/open_meteo_client.py`

#### Methods
- `get_weather_data(latitude: float, longitude: float, start_date: str, end_date: str)` - Fetch weather data
- `validate_data(data: dict)` - Validate weather data against expected schema

#### Response Format
```json
{
  "latitude": 53.3498,
  "longitude": -6.2603,
  "hourly": {
    "time": ["2023-01-01T00:00:00Z", ...],
    "temperature_2m": [5.2, ...]
  }
}
```

## Data Processing APIs

### Bronze Layer Processor
**Module**: `src/transformation/bronze_layer.py`

#### Methods
- `store_bronze_data(key: str, data: dict)` - Store raw data in Bronze layer
- `retrieve_bronze_data(key: str)` - Retrieve raw data from Bronze layer
- `list_bronze_files(prefix: str)` - List files in Bronze layer

### Silver Layer Processor
**Module**: `src/transformation/silver_layer.py`

#### Methods
- `transform_to_silver(data_type: str, raw_data: dict)` - Transform raw data to Silver format
- `store_silver_data(key: str, df: pandas.DataFrame)` - Store validated data in Silver layer
- `retrieve_silver_data(key: str)` - Retrieve validated data from Silver layer

### Gold Layer Processor
**Module**: `src/transformation/gold_layer.py`

#### Methods
- `transform_to_gold(data_type: str, silver_df: pandas.DataFrame)` - Transform Silver data to Gold format
- `store_gold_data(key: str, df: pandas.DataFrame)` - Store analytical data in Gold layer
- `retrieve_gold_data(key: str)` - Retrieve analytical data from Gold layer

## Data Transformation Pipeline
**Module**: `src/transformation/data_transformation.py`

#### Methods
- `process_data_pipeline(data_type: str, date: str, raw_data: dict)` - Execute complete data pipeline
- `process_incremental_data(data_type: str, date: str, raw_data: dict)` - Process data incrementally
- `get_data_quality_metrics(data_type: str, date: str)` - Generate quality metrics

## Data Quality Checks
**Module**: `src/transformation/quality_checks.py`

#### Methods
- `validate_completeness(data: dict)` - Check data completeness
- `validate_schema(data: dict, expected_schema: dict)` - Validate data schema
- `detect_anomalies(data: pandas.DataFrame)` - Detect data anomalies
- `generate_quality_report(data_type: str, date: str)` - Generate comprehensive quality report

## Configuration
**Module**: `src/common/config.py`

### Environment Variables
- `AWS_PROFILE`: AWS profile name (default: `irish-energy-data-platform-dev`)
- `AWS_REGION`: AWS region (default: `eu-west-1`)
- `BRONZE_BUCKET_NAME`: S3 bucket name for Bronze layer
- `SILVER_BUCKET_NAME`: S3 bucket name for Silver layer
- `GOLD_BUCKET_NAME`: S3 bucket name for Gold layer

### Constants
- `MAX_RETRIES`: Maximum number of retry attempts (default: 3)
- `BASE_DELAY`: Base delay for exponential backoff (default: 1 second)
- `RATE_LIMIT`: API rate limit in requests per minute (default: 20)
- `DATA_LAYERS`: List of data layers (['bronze', 'silver', 'gold'])

## Error Handling
All components implement proper error handling with:
- Exponential backoff retry mechanisms
- Structured logging for debugging
- Graceful failure modes
- Circuit breaker patterns for external API calls

## Rate Limiting
Both API clients implement rate limiting:
- EirGrid: Maximum 20 requests per minute
- Open-Meteo: Respects API rate limits
- Automatic retry with exponential backoff