from aws_cdk import (
    Stack,
    aws_s3 as s3,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct

class DataLakeStack(Stack):
    """Creates a unified S3 data lake with Bronze, Silver, and Gold layers using a single bucket"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a single data lake bucket with prefixes for each layer
        self.data_lake_bucket = s3.Bucket(
            self, "DataLakeBucket",
            bucket_name=f"irish-energy-data-lake-{self.account}-{self.region}",
            versioned=False,  # Versioning not required for this phase
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            enforce_ssl=True  # Enforce HTTPS access
        )

        # Define prefixes for each data layer
        self.bronze_prefix = "bronze/"
        self.silver_prefix = "silver/"
        self.gold_prefix = "gold/"
        self.metadata_prefix = "metadata/"
        self.quarantine_prefix = "quarantine/"

        # Export stack outputs
        CfnOutput(
            self,
            "DataLakeBucketName",
            value=self.data_lake_bucket.bucket_name,
            description="Name of the data lake S3 bucket"
        )

        CfnOutput(
            self,
            "DataLakeBucketArn",
            value=self.data_lake_bucket.bucket_arn,
            description="ARN of the data lake S3 bucket"
        )

        CfnOutput(
            self,
            "BronzePrefix",
            value=self.bronze_prefix,
            description="Prefix for Bronze layer data"
        )

        CfnOutput(
            self,
            "SilverPrefix",
            value=self.silver_prefix,
            description="Prefix for Silver layer data"
        )

        CfnOutput(
            self,
            "GoldPrefix",
            value=self.gold_prefix,
            description="Prefix for Gold layer data"
        )