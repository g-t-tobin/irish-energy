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
from stacks.api_registry_stack import ApiRegistryStack
from stacks.analytics_api_stack import AnalyticsApiStack
from stacks.orchestration_stack import OrchestrationStack

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
api_registry_stack = ApiRegistryStack(app, "IrishEnergyApiRegistryStack", env=AWS_ENV)
analytics_api_stack = AnalyticsApiStack(app, "IrishEnergyAnalyticsApi", env=AWS_ENV)
orchestration_stack = OrchestrationStack(app, "IrishEnergyOrchestration", eirgrid_ingestion_fn=ingestion_stack.eirgrid_ingestion_fn, openmeteo_ingestion_fn=ingestion_stack.openmeteo_ingestion_fn, transformation_fn=ingestion_stack.transformation_fn, env=AWS_ENV)

app.synth()