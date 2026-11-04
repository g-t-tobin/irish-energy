# Irish Energy Analytics Data Platform - Development Guide

## Overview
This guide provides instructions for developers working on the Irish Energy Analytics Data Platform, covering development setup, coding standards, and contribution guidelines.

## Development Environment Setup

### Prerequisites
- Python 3.8+
- pip package manager
- AWS CLI configured
- Docker (for containerization)
- Git version control

### Installation
```bash
# Clone the repository
git clone https://github.com/g-t-tobin/irish-energy.git
cd irish-energy

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

## Project Structure
```
irish-energy/
├── infrastructure/          # CDK infrastructure code
│   ├── app.py               # Main CDK application
│   └── stacks/              # Individual CDK stacks
├── src/                     # Source code
│   ├── ingestion/           # Data ingestion components
│   ├── transformation/      # Data processing components
│   ├── common/              # Shared utilities
│   └── dashboard/           # Streamlit dashboard
├── tests/                   # Test suite
├── docs/                    # Documentation
├── sql/                     # SQL queries
├── scripts/                 # Utility scripts
├── workflows/               # GitHub Actions workflows
├── Dockerfile               # Container definition
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
└── pyproject.toml           # Project configuration
```

## Coding Standards

### Python Style Guide
- Follow PEP 8 style guide
- Use type hints for all function signatures
- Write docstrings for all public functions
- Use descriptive variable and function names

### Logging
- Use loguru for structured logging
- Include relevant context in log messages
- Log at appropriate levels (debug, info, warning, error)
- Include timestamps and correlation IDs where applicable

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Implement retry logic for transient failures
- Gracefully handle missing or malformed data

## Testing Strategy

### Unit Tests
Located in `tests/` directory. Test individual components:
- `test_ingestion.py` - API client tests
- `test_transformation.py` - Data processing tests
- `test_quality_checks.py` - Data quality validation tests
- `test_structure.py` - Repository structure tests

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_ingestion.py

# Run with coverage
pytest --cov=src tests/
```

### Test Coverage Requirements
- Minimum 80% code coverage
- All public methods tested
- Edge cases covered
- Error conditions tested

## Data Processing Workflow

### Bronze Layer
1. Raw data ingestion from APIs
2. Data stored in JSON format
3. Timestamp-based keys for immutability
4. No transformation applied

### Silver Layer
1. Data validation and cleaning
2. Schema enforcement
3. Type conversion and normalization
4. Parquet format storage for efficiency

### Gold Layer
1. Aggregation and summarization
2. Statistical calculations
3. Business intelligence preparation
4. Optimized for analytical queries

## Contribution Guidelines

### Branching Strategy
- `main` - Production stable code
- `develop` - Development branch
- Feature branches - For new features

### Pull Request Process
1. Create feature branch from `develop`
2. Implement changes with tests
3. Run all tests locally
4. Submit pull request to `develop`
5. Address review comments
6. Merge after approval

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(ingestion): add Open-Meteo API client

Added robust client for Open-Meteo API with rate limiting and retry logic.

Fixes #123
```

## Continuous Integration

### GitHub Actions Workflows
Located in `.github/workflows/`:
- `ci.yml` - Continuous integration pipeline
- `cdk-deploy.yml` - CDK deployment pipeline

### CI Pipeline Steps
1. Code linting with flake8 and black
2. Type checking with mypy
3. Unit tests execution
4. Security scanning
5. Dependency vulnerability checks

## Deployment Process

### Local Development
```bash
# Deploy CDK stack
cdk deploy --profile irish-energy-data-platform-dev

# Deploy specific stack
cdk deploy IngestionStack --profile irish-energy-data-platform-dev
```

### Production Deployment
1. Merge `develop` to `main`
2. Tag release with semantic versioning
3. Trigger production deployment workflow
4. Monitor deployment in AWS console

## Performance Considerations

### Data Processing
- Use efficient pandas operations
- Leverage PyArrow for Parquet I/O
- Implement incremental processing
- Optimize memory usage for large datasets

### API Calls
- Implement rate limiting
- Use connection pooling
- Add retry logic with exponential backoff
- Cache responses where appropriate

## Security Best Practices

### Credential Management
- Never hardcode AWS credentials
- Use IAM roles for EC2 instances
- Rotate credentials regularly
- Use AWS Secrets Manager for sensitive data

### Data Security
- Encrypt data at rest in S3
- Use secure S3 bucket policies
- Implement proper access controls
- Regular security audits

## Monitoring and Observability

### Logging
- Structured logging with loguru
- Centralized log aggregation
- Log retention policies
- Alerting on error conditions

### Metrics
- CloudWatch metrics for system health
- Custom metrics for business KPIs
- Dashboard creation for monitoring
- Automated alerting setup