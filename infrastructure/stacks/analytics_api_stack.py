from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigw2,
    aws_apigatewayv2_integrations as apigw2_integrations,
    aws_iam as iam,
    Duration,
    aws_s3 as s3,
    aws_ecr_assets as ecr_assets,
)
from constructs import Construct
import os

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
API_IMAGE_CONTEXT = os.path.join(
    PROJECT_ROOT, "build", "api_container_context"
)

class AnalyticsApiStack(Stack):
    """Creates infrastructure for the Analytics API"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get environment variables
        account = self.account
        region = self.region

        # Get existing Gold bucket name from environment or use default
        gold_bucket_name = os.getenv('GOLD_BUCKET_NAME', f'irish-energy-gold-{account}-{region}')

        # Create IAM role for Lambda
        api_role = iam.Role(
            self,
            "AnalyticsApiLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Grant Lambda read access to Gold bucket
        gold_bucket = s3.Bucket.from_bucket_name(self, "GoldBucket", gold_bucket_name)
        gold_bucket.grant_read(api_role)

        # Deploy the API as a Lambda container image.
        # Dependencies are included in the image; no external Lambda layer is needed.
        api_function = _lambda.DockerImageFunction(
            self,
            "AnalyticsApiFunction",
            code=_lambda.DockerImageCode.from_image_asset(
                directory=API_IMAGE_CONTEXT,
                platform=ecr_assets.Platform.LINUX_AMD64,
            ),
            role=api_role,
            timeout=Duration.seconds(30),
            memory_size=2048,
            architecture=_lambda.Architecture.X86_64,
            environment={
                "GOLD_BUCKET": gold_bucket_name,
                "AWS_NODEJS_CONNECTION_REUSE_ENABLED": "1"
            },
        )

        # Create API Gateway HTTP API
        http_api = apigw2.HttpApi(
            self,
            "AnalyticsHttpApi",
            api_name="IrishEnergyAnalyticsApi"
        )

        # Add routes to API Gateway
        http_api.add_routes(
            path="/health",
            methods=[apigw2.HttpMethod.GET],
            integration=apigw2_integrations.HttpLambdaIntegration(
                "HealthLambdaIntegration",
                handler=api_function
            )
        )

        http_api.add_routes(
            path="/demand",
            methods=[apigw2.HttpMethod.GET],
            integration=apigw2_integrations.HttpLambdaIntegration(
                "DemandLambdaIntegration",
                handler=api_function
            )
        )

        http_api.add_routes(
            path="/weather",
            methods=[apigw2.HttpMethod.GET],
            integration=apigw2_integrations.HttpLambdaIntegration(
                "WeatherLambdaIntegration",
                handler=api_function
            )
        )

        http_api.add_routes(
            path="/generation",
            methods=[apigw2.HttpMethod.GET],
            integration=apigw2_integrations.HttpLambdaIntegration(
                "GenerationLambdaIntegration",
                handler=api_function
            )
        )

        http_api.add_routes(
            path="/quality",
            methods=[apigw2.HttpMethod.GET],
            integration=apigw2_integrations.HttpLambdaIntegration(
                "QualityLambdaIntegration",
                handler=api_function
            )
        )

        http_api.add_routes(
            path="/summary",
            methods=[apigw2.HttpMethod.GET],
            integration=apigw2_integrations.HttpLambdaIntegration(
                "SummaryLambdaIntegration",
                handler=api_function
            )
        )

        # Output API endpoint
        self.api_url = http_api.api_endpoint