"""AWS CDK stack for AppInit binary distribution system.

Creates serverless infrastructure with S3 storage, API Gateway endpoints
(/list, /download, /install), and Lambda functions for binary distribution
with automatic platform detection.

When to use:
    - Initial deployment of binary distribution infrastructure
    - Setting up new environments (staging, production)
    - Recreating infrastructure after stack deletion
"""

from typing import Any

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_resourcegroups as resourcegroups,
    RemovalPolicy,
    Duration,
    Tags,
)
from aws_cdk.aws_apigateway import RestApi
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_lambda import Function
from constructs import Construct

from config import CONFIG


class BinaryDistributionStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Tags.of(self).add("Project", CONFIG.project.name)
        Tags.of(self).add("Component", CONFIG.project.component)
        Tags.of(self).add("Environment", CONFIG.project.environment)
        Tags.of(self).add("ManagedBy", CONFIG.project.managed_by)

        self.binary_bucket: Bucket = s3.Bucket(
            scope=self,
            id="AppInitBinariesBucket",
            bucket_name=CONFIG.s3.bucket_name,
            versioned=True,
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.download_lambda: Function = _lambda.Function(
            scope=self,
            id="AppInitDownloadHandler",
            function_name=CONFIG.lambda_config.function_names["download"],
            handler=CONFIG.lambda_config.handlers["download"],
            runtime=CONFIG.lambda_config.runtime,
            code=_lambda.Code.from_asset(CONFIG.lambda_config.code_path),
            environment={
                "BUCKET_NAME": self.binary_bucket.bucket_name,
                "PRESIGNED_URL_EXPIRY": str(CONFIG.lambda_config.presigned_url_expiry_seconds),
            },
            timeout=Duration.seconds(CONFIG.lambda_config.timeout_seconds),
        )
        _ = self.binary_bucket.grant_read(identity=self.download_lambda)

        self.list_lambda: Function = _lambda.Function(
            scope=self,
            id="AppInitListHandler",
            function_name=CONFIG.lambda_config.function_names["list"],
            handler=CONFIG.lambda_config.handlers["list"],
            runtime=CONFIG.lambda_config.runtime,
            code=_lambda.Code.from_asset(CONFIG.lambda_config.code_path),
            environment={"BUCKET_NAME": self.binary_bucket.bucket_name},
            timeout=Duration.seconds(CONFIG.lambda_config.timeout_seconds),
        )
        _ = self.binary_bucket.grant_read(identity=self.list_lambda)

        self.install_script_lambda: Function = _lambda.Function(
            scope=self,
            id="AppInitInstallHandler",
            function_name=CONFIG.lambda_config.function_names["install"],
            handler=CONFIG.lambda_config.handlers["install"],
            runtime=CONFIG.lambda_config.runtime,
            code=_lambda.Code.from_asset(CONFIG.lambda_config.code_path),
            timeout=Duration.seconds(CONFIG.lambda_config.timeout_seconds),
        )

        self.api: RestApi = apigateway.RestApi(
            scope=self,
            id="AppInitBinariesApi",
            rest_api_name=CONFIG.api.name,
            description=CONFIG.api.description,
            endpoint_configuration=apigateway.EndpointConfiguration(types=[apigateway.EndpointType.REGIONAL]),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
            ),
        )

        _ = self.api.root.add_resource(path_part="download").add_method(
            http_method="GET",
            integration=apigateway.LambdaIntegration(
                handler=self.download_lambda, # pyright: ignore[reportArgumentType]
            ),
        )
        _ = self.api.root.add_resource(path_part="list").add_method(
            http_method="GET",
            integration=apigateway.LambdaIntegration(
                handler=self.list_lambda, # pyright: ignore[reportArgumentType]
            ),
        )
        _ = self.api.root.add_resource(path_part="install").add_method(
            http_method="GET",
            integration=apigateway.LambdaIntegration(
                handler=self.install_script_lambda, # pyright: ignore[reportArgumentType]
                proxy=True,
            ),
        )

        _ = resourcegroups.CfnGroup(
            scope=self,
            id="AppInitResourceGroup",
            name=CONFIG.resource_group.name,
            description=CONFIG.resource_group.description,
            resource_query=resourcegroups.CfnGroup.ResourceQueryProperty(
                type="TAG_FILTERS_1_0",
                query=resourcegroups.CfnGroup.QueryProperty(
                    resource_type_filters=["AWS::AllSupported"],
                    tag_filters=[resourcegroups.CfnGroup.TagFilterProperty(key="Project", values=[CONFIG.project.name])],
                ),
            ),
            tags=[{"key": "Project", "value": CONFIG.project.name}, {"key": "Component", "value": CONFIG.project.component}],
        )
