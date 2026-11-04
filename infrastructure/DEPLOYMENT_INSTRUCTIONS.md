# AWS Deployment Instructions

## Prerequisites

1. AWS CLI configured with profile `irish-energy-data-platform-dev`
2. Python 3.8+ with dependencies installed
3. AWS CDK installed (`npm install -g aws-cdk`)
4. Proper AWS permissions for:
   - S3 bucket creation and management
   - Lambda function deployment
   - EventBridge rule creation
   - IAM role creation
   - CloudWatch monitoring setup

## Deployment Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Bootstrap CDK (One-time setup)
```bash
cdk bootstrap aws://$(aws sts get-caller-identity --query 'Account' --output text)/eu-west-1 --profile irish-energy-data-platform-dev
```

### 3. Deploy All Stacks
```bash
cdk deploy --all --profile irish-energy-data-platform-dev
```

### 4. Deploy Specific Stacks
```bash
# Deploy Data Lake Stack
cdk deploy DataLakeStack --profile irish-energy-data-platform-dev

# Deploy Ingestion Stack  
cdk deploy IngestionStack --profile irish-energy-data-platform-dev

# Deploy Analytics Stack
cdk deploy AnalyticsStack --profile irish-energy-data-platform-dev

# Deploy Monitoring Stack
cdk deploy MonitoringStack --profile irish-energy-data-platform-dev
```

## Cleanup Commands

### Destroy All Resources
```bash
cdk destroy --all --profile irish-energy-data-platform-dev
```

### Destroy Specific Stacks
```bash
cdk destroy DataLakeStack --profile irish-energy-data-platform-dev
cdk destroy IngestionStack --profile irish-energy-data-platform-dev
cdk destroy AnalyticsStack --profile irish-energy-data-platform-dev
cdk destroy MonitoringStack --profile irish-energy-data-platform-dev
```

## AWS Region and Profile

- **Region**: eu-west-1
- **Profile**: irish-energy-data-platform-dev

## Post-Deployment

After successful deployment, you can:
1. Monitor CloudWatch logs for ingestion activities
2. Check S3 buckets for processed data in Bronze/Silver/Gold layers
3. Query Athena for analytical datasets
4. Access the Streamlit dashboard through the deployed UI