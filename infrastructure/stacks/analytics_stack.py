from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_athena as athena,
    aws_s3 as s3,
)
from constructs import Construct


class AnalyticsStack(Stack):
    """Creates infrastructure for analytical queries."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Athena results bucket
        results_bucket = s3.Bucket(
            self,
            "AthenaResultsBucket",
            bucket_name=(
                f"irish-energy-analytics-results-{self.account}-{self.region}"
            ),
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldResults",
                    expiration=Duration.days(30),
                    enabled=True,
                )
            ],
        )

        # Athena workgroup
        athena_workgroup = athena.CfnWorkGroup(
            self,
            "AnalyticsWorkGroup",
            name="irish-energy-analytics",
            state="ENABLED",
            work_group_configuration=(
                athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                    enforce_work_group_configuration=True,
                    publish_cloud_watch_metrics_enabled=True,
                    bytes_scanned_cutoff_per_query=10 * 1024 * 1024,
                    result_configuration=(
                        athena.CfnWorkGroup.ResultConfigurationProperty(
                            output_location=(
                                f"s3://{results_bucket.bucket_name}/"
                            )
                        )
                    ),
                )
            ),
        )

        # Ensure the results bucket exists before the workgroup.
        athena_workgroup.add_dependency(
            results_bucket.node.default_child
        )
