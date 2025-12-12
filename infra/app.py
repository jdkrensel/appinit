import aws_cdk as cdk
from aws_cdk import Environment
from stacks.binary_distribution_stack import BinaryDistributionStack
import os

app = cdk.App()

# Deploy binary distribution infrastructure
BinaryDistributionStack(
    app,
    "AppInitBinaryDistribution",
    env=Environment(
        account=os.environ.get('CDK_DEFAULT_ACCOUNT'),
        region=os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')
    ),
)

app.synth()
