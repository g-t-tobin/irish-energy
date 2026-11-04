# Irish Energy Analytics Data Platform - User Guide

## Overview
This guide explains how to use and operate the Irish Energy Analytics Data Platform for analyzing Irish energy consumption and weather data.

## System Components

### Data Sources
1. **EirGrid API** - Provides electricity demand data for Ireland
2. **Open-Meteo API** - Provides weather data for Ireland

### Data Layers
1. **Bronze Layer** - Raw, unprocessed data from APIs
2. **Silver Layer** - Cleaned and validated data
3. **Gold Layer** - Aggregated analytical datasets

## Getting Started

### Prerequisites
- AWS account with `eu-west-1` region
- Python 3.8+ environment
- AWS CLI configured with appropriate credentials
- Required dependencies installed via `requirements.txt`

### Installation
```bash
# Clone the repository
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

## Using the Platform

### Data Ingestion
The platform automatically ingests data from EirGrid and Open-Meteo APIs on a scheduled basis using EventBridge.

### Data Access
Access processed data through:
- **S3 Buckets**: Direct access to Bronze, Silver, and Gold layer data
- **Athena Queries**: Analyze data using SQL queries
- **Streamlit Dashboard**: Interactive visualization

### Querying Data

#### Using Athena
```sql
-- Example query for Gold layer demand data
SELECT date, total_demand, avg_demand 
FROM gold_demand_summary 
WHERE date >= '2023-01-01'
ORDER BY date;
```

#### Using Python
```python
import boto3
import pandas as pd

# Connect to S3
s3 = boto3.client('s3')
bucket_name = 'your-bronze-bucket-name'

# Read data
response = s3.get_object(Bucket=bucket_name, Key='demand/2023-01-01.json')
data = json.loads(response['Body'].read())
```

## Monitoring and Maintenance

### CloudWatch Metrics
Monitor system health through:
- Ingestion success rates
- Processing latency
- Data quality scores
- Error rates

### Alerts
Configure alerts for:
- Failed data ingestion
- Data quality issues
- System performance degradation

## Troubleshooting

### Common Issues
1. **Authentication Errors**: Ensure AWS credentials are properly configured
2. **Rate Limiting**: API clients handle rate limiting automatically
3. **Data Quality Issues**: Check quality metrics in CloudWatch
4. **Storage Issues**: Monitor S3 bucket usage

### Debugging
1. Check CloudWatch logs for error details
2. Review data quality metrics
3. Inspect raw data in Bronze layer
4. Validate Silver layer transformations

## Best Practices

### Data Management
- All data is immutable - no modifications to existing records
- Process data incrementally to reduce computational overhead
- Maintain data lineage for audit purposes

### Performance Optimization
- Use Gold layer datasets for analytical queries
- Leverage Athena's partitioning for faster queries
- Schedule ingestions during off-peak hours when possible

### Security
- Regularly review IAM permissions
- Monitor access logs
- Keep dependencies updated