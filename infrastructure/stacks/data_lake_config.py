"""Configuration utilities for the data lake infrastructure"""

import os
from aws_cdk import (
    Stack,
    CfnParameter,
    CfnOutput
)
from constructs import Construct


class DataLakeConfig:
    """Configuration class for data lake settings"""

    def __init__(self, scope: Construct, stack: Stack):
        # Parameters for configuration
        self.project_identifier = CfnParameter(
            scope,
            "ProjectIdentifier",
            type="String",
            default="irish-energy",
            description="Project identifier for resource naming"
        )

        self.environment_identifier = CfnParameter(
            scope,
            "EnvironmentIdentifier",
            type="String",
            default="dev",
            description="Environment identifier (dev, staging, prod)"
        )

        # Output configuration values
        CfnOutput(
            scope,
            "ProjectIdentifierOutput",
            value=self.project_identifier.value_as_string,
            description="Project identifier"
        )

        CfnOutput(
            scope,
            "EnvironmentIdentifierOutput",
            value=self.environment_identifier.value_as_string,
            description="Environment identifier"
        )