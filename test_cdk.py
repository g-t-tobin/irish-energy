#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import CDK modules
from aws_cdk import App
from infrastructure.stacks.ingestion_stack import IngestionStack

# Create CDK app
app = App()

# Create the stack
IngestionStack(app, "TestIngestionStack")

# Synthesize
app.synth()

print("CDK synthesis completed successfully")