#!/usr/bin/env python3

"""
Main CDK application for Irish Energy Analytics Data Platform
"""

import os
from aws_cdk import (
    App,
    Environment,
)
from stacks.data_lake_stack import DataLakeStack
from stacks.ingestion_stack import IngestionStack
from stacks.monitoring_stack import MonitoringStack

# Define AWS environment
AWS_ENV = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "eu-west-1")
)

app = App()

# Create core infrastructure stacks
data_lake_stack = DataLakeStack(app, "IrishEnergyDataLake", env=AWS_ENV)
ingestion_stack = IngestionStack(app, "IrishEnergyIngestion", env=AWS_ENV)
monitoring_stack = MonitoringStack(app, "IrishEnergyMonitoring", env=AWS_ENV)

app.synth()