#!/usr/bin/env python3
"""GitHub OIDC Setup for AppInit Binary Deployment.

This module configures AWS IAM roles and OIDC providers to enable secure,
keyless authentication from GitHub Actions to AWS services. It creates the
necessary IAM infrastructure for automated binary deployment without requiring
long-lived AWS access keys.

The script creates:
    - GitHub OIDC Identity Provider (if not exists)
    - IAM Role with trust policy for the specified GitHub repository
    - Inline policy with minimal S3 and CloudFormation permissions
    - Proper resource tagging for compliance and management

Security Features:
    - Uses OIDC for keyless authentication
    - Restricts access to specific GitHub repository
    - Implements least-privilege access principles
    - Supports only the specific S3 bucket and CloudFormation stack

When to use this script:
    - Initial setup of a new GitHub repository for AppInit deployment
    - Setting up CI/CD for a forked repository
    - Recreating IAM roles after accidental deletion
    - Migrating to a new GitHub repository
    - Troubleshooting GitHub Actions authentication issues
    - Setting up deployment access for additional repositories

Note: This is a one-time setup script. Once the OIDC provider and IAM role
are created, GitHub Actions will automatically use them for deployments.

Typical usage example:
    $ cd infra
    $ uv run python scripts/setup_github_oidc.py username/repository-name

The script will output the Role ARN that needs to be added as a GitHub
repository secret named 'AWS_ROLE_ARN'.

Requirements:
    - AWS CLI configured with IAM administrative permissions
    - boto3 installed
    - Valid GitHub repository name in format 'owner/repo'

Security Note:
    This script requires elevated IAM permissions to create roles and OIDC
    providers. Run only in trusted environments with appropriate AWS credentials.
"""
import boto3
import json
import sys

def create_github_oidc_role(github_repo, account_id):
    """Create IAM role for GitHub Actions OIDC"""
    iam = boto3.client('iam')
    
    # OIDC provider ARN (GitHub's OIDC provider)
    oidc_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    
    # Trust policy for GitHub Actions
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": oidc_provider_arn
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{github_repo}:*"
                    }
                }
            }
        ]
    }
    
    # Permissions policy for binary deployment
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::appinit-binaries",
                    "arn:aws:s3:::appinit-binaries/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cloudformation:DescribeStacks"
                ],
                "Resource": f"arn:aws:cloudformation:us-east-1:{account_id}:stack/AppInitBinaryDistribution/*"
            }
        ]
    }
    
    role_name = "GitHubActions-AppInitBinaryDeploy"
    
    try:
        # Create the role
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for GitHub Actions to deploy AppInit binaries",
            Tags=[
                {"Key": "Project", "Value": "AppInit"},
                {"Key": "Component", "Value": "CI/CD"},
                {"Key": "ManagedBy", "Value": "Script"}
            ]
        )
        
        print(f"✅ Created IAM role: {role_name}")
        role_arn = response['Role']['Arn']
        
        # Attach inline policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="BinaryDeploymentPolicy",
            PolicyDocument=json.dumps(permissions_policy)
        )
        
        print(f"✅ Attached permissions policy")
        print(f"\n🔑 Role ARN: {role_arn}")
        print(f"\n📝 Add this to your GitHub repository secrets:")
        print(f"   Secret name: AWS_ROLE_ARN")
        print(f"   Secret value: {role_arn}")
        
        return role_arn
        
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"⚠️  Role {role_name} already exists")
        role = iam.get_role(RoleName=role_name)
        role_arn = role['Role']['Arn']
        print(f"🔑 Existing Role ARN: {role_arn}")
        return role_arn
    
    except Exception as e:
        print(f"❌ Error creating role: {e}")
        return None

def setup_oidc_provider(account_id):
    """Setup GitHub OIDC provider if it doesn't exist"""
    iam = boto3.client('iam')
    
    try:
        # Check if OIDC provider exists
        iam.get_open_id_connect_provider(
            OpenIDConnectProviderArn=f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
        )
        print("✅ GitHub OIDC provider already exists")
        return True
        
    except iam.exceptions.NoSuchEntityException:
        # Create OIDC provider
        try:
            response = iam.create_open_id_connect_provider(
                Url='https://token.actions.githubusercontent.com',
                ClientIDList=['sts.amazonaws.com'],
                ThumbprintList=['6938fd4d98bab03faadb97b34396831e3780aea1']  # GitHub's thumbprint
            )
            print("✅ Created GitHub OIDC provider")
            return True
            
        except Exception as e:
            print(f"❌ Error creating OIDC provider: {e}")
            return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python setup_github_oidc.py <github-repo>")
        print("Example: python setup_github_oidc.py username/appinit")
        sys.exit(1)
    
    github_repo = sys.argv[1]
    
    # Get AWS account ID
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    print(f"🚀 Setting up GitHub OIDC for repository: {github_repo}")
    print(f"📋 AWS Account ID: {account_id}")
    
    # Setup OIDC provider
    if not setup_oidc_provider(account_id):
        sys.exit(1)
    
    # Create role
    role_arn = create_github_oidc_role(github_repo, account_id)
    if not role_arn:
        sys.exit(1)
    
    print(f"\n🎉 Setup complete!")
    print(f"\n📋 Next steps:")
    print(f"1. Go to your GitHub repository settings")
    print(f"2. Navigate to Secrets and variables → Actions")
    print(f"3. Add a new repository secret:")
    print(f"   Name: AWS_ROLE_ARN")
    print(f"   Value: {role_arn}")
    print(f"4. Push changes to main branch or merge a PR to trigger deployment")

if __name__ == "__main__":
    main()