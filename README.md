# Irish Energy Analytics Data Platform

A cloud-native data platform for collecting, processing, and analyzing Irish energy consumption and weather data from EirGrid and Open-Meteo APIs.

## Overview

This platform provides a complete solution for:
- Ingesting electricity demand and generation data from EirGrid
- Collecting weather data from Open-Meteo
- Processing data through Bronze/Silver/Gold layers
- Enabling data analysis and visualization
- Supporting energy consumption forecasting and insights

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EirGrid API   │    │ Open-Meteo API  │    │   Streamlit     │
│   (External)    │    │   (External)    │    │   Dashboard     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Ingestion Layer                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │             Lambda Functions                            │   │
│  │  - EirGrid Client                                       │   │
│  │  - Open-Meteo Client                                    │   │
│  │  - Data Validation                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Lake                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ Bronze  │  │ Silver  │  │ Gold    │  │ Athena  │            │
│  │ Layer   │  │ Layer   │  │ Layer   │  │ Queries │            │
│  │ (Raw)   │  │ (Clean) │  │ (Analytical) │  │         │            │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Monitoring & Alerts                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  CloudWatch Metrics                                     │   │
│  │  - Data Ingestion Success Rates                         │   │
│  │  - Processing Latency                                   │   │
│  │  - Data Quality Scores                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### Data Ingestion
- Robust API clients for EirGrid and Open-Meteo
- Rate limiting and retry mechanisms
- Data validation and schema checking
- Structured logging and monitoring

### Data Processing
- Three-layer architecture (Bronze/Silver/Gold)
- Immutable storage design
- Idempotent processing
- Schema evolution support
- Data quality validation

### Analytics
- Athena-based querying
- Streamlit dashboard for visualization
- Aggregated analytical datasets
- Historical data analysis

### Infrastructure
- Cloud-native deployment with AWS CDK
- Scalable Lambda functions
- S3 data lake storage
- Event-driven scheduling
- Comprehensive monitoring

## Quick Start

### Prerequisites
- AWS account with `eu-west-1` region
- Python 3.8+
- AWS CLI configured
- CDK installed

### Installation
```bash
# Clone repository
git clone https://github.com/g-t-tobin/irish-energy.git
cd irish-energy

# Install dependencies
pip install -r requirements.txt
```

### Deployment
```bash
# Configure AWS profile
aws configure --profile irish-energy-data-platform-dev

# Deploy infrastructure
cdk deploy --all --profile irish-energy-data-platform-dev
```

## Components

### Ingestion Layer
- `src/ingestion/` - API clients for data sources
- `src/common/config.py` - Configuration management

### Transformation Layer
- `src/transformation/` - Data processing components
- `src/transformation/quality_checks.py` - Data quality validation

### Infrastructure
- `infrastructure/` - CDK stack definitions
- `infrastructure/app.py` - Main CDK application

### Dashboard
- `dashboard/` - Streamlit visualization dashboard

## Data Flow

1. **Ingestion**: Lambda functions fetch data from EirGrid and Open-Meteo APIs
2. **Bronze Layer**: Raw data stored in S3 as JSON
3. **Silver Layer**: Data validated and transformed to Parquet format
4. **Gold Layer**: Aggregated analytical datasets prepared for querying
5. **Analytics**: Athena queries or Streamlit dashboard for insights

## Testing

Run unit tests:
```bash
pytest tests/
```

Run integration tests:
```bash
pytest tests/test_integration.py
```

## Documentation

- `docs/technical_documentation.md` - Technical implementation details
- `docs/user_guide.md` - How to use the platform
- `docs/api_reference.md` - API and interface reference
- `docs/development_guide.md` - Developer guidelines

## Contributing

See `docs/development_guide.md` for contribution guidelines.

## License

MIT License - see LICENSE file for details.