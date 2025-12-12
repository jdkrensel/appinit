"""AWS CDK application entry point for AppInit binary distribution system.

This module defines the main CDK application that deploys the binary distribution
infrastructure including S3 storage, API Gateway endpoints, and Lambda functions
for serving AppInit CLI binaries with automatic platform detection.

The application creates:
- S3 bucket for binary storage with versioning
- API Gateway with IAM-secured endpoints (/list, /download, /install)
- Lambda functions for handling requests
- IAM policies for secure access control
"""

import os

import aws_cdk as cdk
from aws_cdk import App, Environment

from stacks.binary_distribution_stack import BinaryDistributionStack

app: App = cdk.App()

_ = BinaryDistributionStack(
    scope=app,
    construct_id="AppInitBinaryDistribution",
    env=Environment(
        account=os.environ.get('CDK_DEFAULT_ACCOUNT'),
        region=os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')
    ),
)

_ = app.synth()
