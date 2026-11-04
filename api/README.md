# Irish Energy Analytics API

This is a FastAPI backend service that connects to the Irish Energy Analytics Gold layer in S3, providing REST endpoints for energy data.

## Features

- Retrieve demand, weather, generation, quality and summary data
- Date-range filtering support
- Proper data schema alignment with frontend TypeScript interfaces
- Robust error handling
- Unit and integration tests

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Frontend      │    │  FastAPI Backend │    │    S3 Gold Layer    │
│  (React/TS)     │────│  (Python/Pydantic)│────│  (Parquet files)    │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

## Local Setup

1. Install dependencies:
```bash
pip install fastapi uvicorn boto3 pandas pyarrow loguru pytest pytest-mock
```

2. Set environment variables:
```bash
export AWS_REGION=eu-west-1
export S3_BUCKET_NAME=irish-energy-gold-layer
```

3. Run the server:
```bash
uvicorn api.main:app --reload
```

## API Endpoints

- `GET /health` - Health check
- `GET /demand` - Demand data
- `GET /weather` - Weather data
- `GET /generation` - Generation data
- `GET /quality` - Quality metrics
- `GET /summary` - Summary data

## Testing

Run unit tests:
```bash
pytest api/tests/test_data_service.py
```

Run integration tests:
```bash
pytest api/tests/test_data_service_integration.py
```

## Development Notes

- This implementation assumes the S3 structure matches the Gold layer schema
- The API returns JSON that aligns with the frontend TypeScript interfaces
- Error handling is implemented for missing datasets, malformed Parquet files, and AWS errors
- All data access is through S3, no data is exposed publicly or deployed to AWS
- Mock data is available for local frontend development