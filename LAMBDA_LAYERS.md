# AWS Lambda Layer Implementation Guide

This document outlines how to implement Lambda Layers for pandas and pyarrow dependencies.

## Layer Creation Process

1. Create a directory structure for the layer:
```bash
mkdir -p layers/pandas_pyarrow_layer/python
```

2. Install dependencies to the layer directory:
```bash
pip install --no-cache-dir -t layers/pandas_pyarrow_layer/python pandas==2.1.3 pyarrow==15.0.0
```

3. Create the zip file:
```bash
cd layers/pandas_pyarrow_layer
zip -r ../pandas_pyarrow_layer.zip .
```

## Alternative: Using AWS SAM or CDK

For production deployments, consider using AWS SAM or CDK's PythonLayerVersion construct to automate layer creation.

## CDK Integration

The CDK stack should reference the layer like this:
```python
pandas_pyarrow_layer = _lambda_python.PythonLayerVersion(
    self,
    "PandasPyArrowLayer",
    entry_point="layers/pandas_pyarrow_layer",
    compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
    description="Layer with pandas and pyarrow dependencies"
)

# Reference in Lambda function
transformation_fn = _lambda.Function(
    self,
    "DataTransformationFunction",
    runtime=_lambda.Runtime.PYTHON_3_12,
    handler="transformation.handler.lambda_handler",
    code=_lambda.Code.from_asset(str(TRANSFORMATION_BUILD_PATH)),
    timeout=Duration.minutes(10),
    role=transformation_role,
    environment={
        "BRONZE_BUCKET": f"irish-energy-bronze-{self.account}-eu-west-1",
        "SILVER_BUCKET": f"irish-energy-silver-{self.account}-eu-west-1",
        "GOLD_BUCKET": f"irish-energy-gold-{self.account}-eu-west-1",
    },
    layers=[pandas_pyarrow_layer],
)
```