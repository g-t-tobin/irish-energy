from pathlib import Path

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_PATH = PROJECT_ROOT / "build" / "lambda_package"
TRANSFORMATION_BUILD_PATH = PROJECT_ROOT / "build" / "transformation_package"
LAYER_BUILD_PATH = PROJECT_ROOT / "build" / "pandas_pyarrow_layer.zip"


class IngestionStack(Stack):
    """Creates infrastructure for data ingestion."""

    def __init__(self, scope: Construct, construct_id: str, bronze_bucket=None, silver_bucket=None, gold_bucket=None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # If buckets are not provided, import existing ones
        if bronze_bucket is None:
            bronze_bucket = s3.Bucket.from_bucket_name(self, "ImportedBronzeBucket", "irish-energy-bronze-851725545966-eu-west-1")
        if silver_bucket is None:
            silver_bucket = s3.Bucket.from_bucket_name(self, "ImportedSilverBucket", "irish-energy-silver-851725545966-eu-west-1")
        if gold_bucket is None:
            gold_bucket = s3.Bucket.from_bucket_name(self, "ImportedGoldBucket", "irish-energy-gold-851725545966-eu-west-1")

        if not BUILD_PATH.is_dir():
            raise FileNotFoundError(
                f"Lambda build directory not found: {BUILD_PATH}"
            )

        if not TRANSFORMATION_BUILD_PATH.is_dir():
            raise FileNotFoundError(
                f"Transformation Lambda build directory not found: {TRANSFORMATION_BUILD_PATH}"
            )

        ingestion_role = iam.Role(
            self,
            "IngestionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        ingestion_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"],
                resources=[
                    f"{bronze_bucket.bucket_arn}/*",
                    f"{silver_bucket.bucket_arn}/*",
                ],
            )
        )

        # Add EventBridge permission for emitting events
        ingestion_role.add_to_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=["arn:aws:events:eu-west-1:{}:event-bus/default".format(self.account)],
            )
        )

        # Add transformation role with appropriate permissions
        transformation_role = iam.Role(
            self,
            "TransformationRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        transformation_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"],
                resources=[
                    f"{bronze_bucket.bucket_arn}/*",
                    f"{silver_bucket.bucket_arn}/*",
                    f"{gold_bucket.bucket_arn}/*",
                ],
            )
        )

        # Add ListBucket permission for transformation role
        transformation_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"],
                resources=[
                    bronze_bucket.bucket_arn,
                    silver_bucket.bucket_arn,
                    gold_bucket.bucket_arn,
                ],
            )
        )

        # Create Lambda functions with proper directory structure
        eirgrid_ingestion_fn = _lambda.Function(
            self,
            "EirGridIngestionFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="src.ingestion.eirgrid_ingestion.lambda_handler",
            code=_lambda.Code.from_asset(str(BUILD_PATH)),
            timeout=Duration.minutes(5),
            role=ingestion_role,
            environment={
                "BRONZE_BUCKET": bronze_bucket.bucket_name,
                "SILVER_BUCKET": silver_bucket.bucket_name,
            },
        )

        openmeteo_ingestion_fn = _lambda.Function(
            self,
            "OpenMeteoIngestionFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="src.ingestion.openmeteo_ingestion.lambda_handler",
            code=_lambda.Code.from_asset(str(BUILD_PATH)),
            timeout=Duration.minutes(5),
            role=ingestion_role,
            environment={
                "BRONZE_BUCKET": bronze_bucket.bucket_name,
                "SILVER_BUCKET": silver_bucket.bucket_name,
            },
        )

        # Create Lambda layer for pandas, numpy and pyarrow
        pandas_pyarrow_layer = _lambda.LayerVersion(
            self,
            "PandasPyArrowLayer",
            code=_lambda.Code.from_asset(str(LAYER_BUILD_PATH)),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.X86_64],
            description="Layer with pandas, numpy and pyarrow dependencies"
        )

        # Create separate Silver transformation Lambda function
        silver_transformation_fn = _lambda.Function(
            self,
            "SilverTransformationFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="transformation.silver_lambda_handler.lambda_handler",
            code=_lambda.Code.from_asset(str(TRANSFORMATION_BUILD_PATH)),
            timeout=Duration.minutes(10),
            role=transformation_role,
            environment={
                "BRONZE_BUCKET": bronze_bucket.bucket_name,
                "SILVER_BUCKET": silver_bucket.bucket_name,
                "GOLD_BUCKET": gold_bucket.bucket_name,
            },
            layers=[pandas_pyarrow_layer],
        )

        # Create separate Gold transformation Lambda function
        gold_transformation_fn = _lambda.Function(
            self,
            "GoldTransformationFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="transformation.gold_lambda_handler.lambda_handler",
            code=_lambda.Code.from_asset(str(TRANSFORMATION_BUILD_PATH)),
            timeout=Duration.minutes(10),
            role=transformation_role,
            environment={
                "BRONZE_BUCKET": bronze_bucket.bucket_name,
                "SILVER_BUCKET": silver_bucket.bucket_name,
                "GOLD_BUCKET": gold_bucket.bucket_name,
            },
            layers=[pandas_pyarrow_layer],
        )

        # Keep the existing combined transformation function for now
        transformation_fn = _lambda.Function(
            self,
            "DataTransformationFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="transformation.handler.lambda_handler",
            code=_lambda.Code.from_asset(str(TRANSFORMATION_BUILD_PATH)),
            timeout=Duration.minutes(10),
            role=transformation_role,
            environment={
                "BRONZE_BUCKET": bronze_bucket.bucket_name,
                "SILVER_BUCKET": silver_bucket.bucket_name,
                "GOLD_BUCKET": gold_bucket.bucket_name,
            },
            layers=[pandas_pyarrow_layer],
        )

        # Expose the functions for cross-stack references
        self.eirgrid_ingestion_fn = eirgrid_ingestion_fn
        self.openmeteo_ingestion_fn = openmeteo_ingestion_fn
        self.transformation_fn = transformation_fn

        # Create EventBridge rule for triggering transformation
        transformation_rule = events.Rule(
            self,
            "TransformationTriggerRule",
            description="Trigger transformation function when ingestion completes",
            event_pattern=events.EventPattern(
                source=["irish-energy.ingestion"],
                detail_type=["EirGrid Ingestion Complete", "OpenMeteo Ingestion Complete"]
            )
        )

        # Add targets for ingestion completion events
        transformation_rule.add_target(targets.LambdaFunction(transformation_fn))

      


        ingestion_rule = events.Rule(
            self,
            "DailyIngestionSchedule",
            schedule=events.Schedule.rate(Duration.days(1)),
        )

        ingestion_rule.add_target(targets.LambdaFunction(eirgrid_ingestion_fn))
        ingestion_rule.add_target(targets.LambdaFunction(openmeteo_ingestion_fn))
