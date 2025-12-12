"""Configuration module for AppInit binary distribution system.

Centralizes all configuration constants using dataclasses for better
type safety and maintainability.
"""

from dataclasses import dataclass

from aws_cdk import aws_lambda as _lambda


@dataclass(frozen=True)
class ProjectConfig:
    """Core project configuration."""
    name: str = "AppInit"
    component: str = "BinaryDistribution"
    environment: str = "Production"
    managed_by: str = "CDK"


@dataclass(frozen=True)
class S3Config:
    """S3 bucket configuration."""
    bucket_name: str = "appinit-binaries"


@dataclass(frozen=True)
class ApiConfig:
    """API Gateway configuration."""
    name: str = "appinit-binaries"
    description: str = "AppInit binary distribution API"


@dataclass(frozen=True)
class LambdaConfig:
    """Lambda function configuration."""
    timeout_seconds: int = 30
    runtime: _lambda.Runtime = _lambda.Runtime.PYTHON_3_14
    code_path: str = "lambda_functions"
    presigned_url_expiry_seconds: int = 3600
    
    @property
    def function_names(self) -> dict[str, str]:
        return {
            "download": "appinit-download-handler",
            "list": "appinit-list-handler",
        }
    
    @property
    def handlers(self) -> dict[str, str]:
        return {
            "download": "download_handler.lambda_handler",
            "list": "list_handler.lambda_handler",
        }


@dataclass(frozen=True)
class ResourceGroupConfig:
    """Resource group configuration."""
    project_name: str
    component_name: str
    
    @property
    def name(self) -> str:
        return f"{self.project_name}-{self.component_name}"
    
    @property
    def description(self) -> str:
        return f"All resources for {self.project_name} binary distribution system"


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration combining all sub-configs."""
    project: ProjectConfig = ProjectConfig()
    s3: S3Config = S3Config()
    api: ApiConfig = ApiConfig()
    lambda_config: LambdaConfig = LambdaConfig()
    
    @property
    def resource_group(self) -> ResourceGroupConfig:
        return ResourceGroupConfig(
            project_name=self.project.name,
            component_name=self.project.component
        )


# Global configuration instance
CONFIG: AppConfig = AppConfig()