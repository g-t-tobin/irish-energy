from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Tags,
    aws_ecr as ecr,
)
from constructs import Construct


class ApiRegistryStack(Stack):
    """Creates the ECR repository used to store API images."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repository = ecr.Repository(
            self,
            "ApiRepository",
            repository_name="irish-energy-api",
            image_scan_on_push=True,
            image_tag_mutability=ecr.TagMutability.IMMUTABLE,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Remove untagged images after 14 days",
                    rule_priority=1,
                    tag_status=ecr.TagStatus.UNTAGGED,
                    max_image_age=Duration.days(14),
                ),
                ecr.LifecycleRule(
                    description="Keep the 30 newest images",
                    rule_priority=2,
                    tag_status=ecr.TagStatus.ANY,
                    max_image_count=30,
                ),
            ],
        )

        Tags.of(repository).add("Component", "api-registry")
        Tags.of(repository).add("Project", "irish-energy-data-platform")

        CfnOutput(self, "RepositoryUri", value=repository.repository_uri)
        CfnOutput(self, "RepositoryName", value=repository.repository_name)
