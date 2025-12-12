#!/usr/bin/env python3
"""
Build and deploy appinit binaries to S3
"""
import subprocess
import os
import sys
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

# Build targets
TARGETS = [
    ("linux", "amd64"),
    ("linux", "arm64"),
    ("darwin", "amd64"),
    ("darwin", "arm64"),
    ("windows", "amd64"),
]

def run_command(cmd, cwd=None):
    """Run a shell command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def build_binary(goos, goarch, output_dir):
    """Build binary for specific OS/arch"""
    app_dir = Path(__file__).parent.parent.parent / "app"
    
    binary_name = "appinit"
    if goos == "windows":
        binary_name += ".exe"
    
    output_path = output_dir / f"appinit-{goos}-{goarch}"
    if goos == "windows":
        output_path = output_dir / f"appinit-{goos}-{goarch}.exe"
    
    env = os.environ.copy()
    env["GOOS"] = goos
    env["GOARCH"] = goarch
    env["CGO_ENABLED"] = "0"
    
    cmd = ["go", "build", "-o", str(output_path), "."]
    
    print(f"Building {goos}/{goarch}...")
    result = subprocess.run(cmd, cwd=app_dir, env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Build failed for {goos}/{goarch}: {result.stderr}")
        return None
    
    print(f"Built: {output_path}")
    return output_path

def get_stack_outputs():
    """Get CloudFormation stack outputs"""
    try:
        cf = boto3.client('cloudformation')
        response = cf.describe_stacks(StackName='AppInitBinaryDistribution')
        
        outputs = {}
        if 'Stacks' in response and response['Stacks']:
            stack_outputs = response['Stacks'][0].get('Outputs', [])
            for output in stack_outputs:
                outputs[output['OutputKey']] = output['OutputValue']
        
        return outputs
    except ClientError as e:
        print(f"Error getting stack outputs: {e}")
        return {}

def upload_to_s3(file_path, bucket_name, key):
    """Upload file to S3"""
    s3 = boto3.client('s3')
    
    try:
        print(f"Uploading {file_path} to s3://{bucket_name}/{key}")
        s3.upload_file(
            str(file_path), 
            bucket_name, 
            key,
            ExtraArgs={
                'ContentType': 'application/octet-stream',
                'Metadata': {
                    'version': get_version(),
                    'build-time': str(subprocess.check_output(['date'], text=True).strip())
                }
            }
        )
        print(f"Uploaded successfully")
        return True
    except ClientError as e:
        print(f"Upload failed: {e}")
        return False

def get_version():
    """Get version from git or default"""
    try:
        return subprocess.check_output(['git', 'describe', '--tags', '--always'], text=True).strip()
    except:
        return "dev"

def main():
    """Main build and deploy process"""
    # Create build directory
    build_dir = Path(__file__).parent.parent / "build"
    build_dir.mkdir(exist_ok=True)
    
    # Get bucket name from stack outputs
    outputs = get_stack_outputs()
    bucket_name = None
    
    # Try to find bucket name in outputs or use a pattern
    for key, value in outputs.items():
        if 'bucket' in key.lower():
            bucket_name = value
            break
    
    if not bucket_name:
        # Fallback: try to find bucket by name pattern
        s3 = boto3.client('s3')
        try:
            response = s3.list_buckets()
            for bucket in response['Buckets']:
                if 'appinit-binaries' in bucket['Name']:
                    bucket_name = bucket['Name']
                    break
        except ClientError:
            pass
    
    if not bucket_name:
        print("Error: Could not find S3 bucket. Make sure the stack is deployed.")
        sys.exit(1)
    
    print(f"Using bucket: {bucket_name}")
    
    # Build binaries
    built_files = []
    for goos, goarch in TARGETS:
        binary_path = build_binary(goos, goarch, build_dir)
        if binary_path:
            built_files.append((binary_path, goos, goarch))
    
    if not built_files:
        print("No binaries were built successfully")
        sys.exit(1)
    
    # Upload to S3
    print("\nUploading binaries to S3...")
    for binary_path, goos, goarch in built_files:
        key = binary_path.name
        if upload_to_s3(binary_path, bucket_name, key):
            print(f"✓ {goos}/{goarch} uploaded")
        else:
            print(f"✗ {goos}/{goarch} failed")
    
    print(f"\nDeployment complete!")
    print(f"Binaries available at your API Gateway endpoint")
    print(f"Install script: curl -sSL https://your-api-url/install | bash")

if __name__ == "__main__":
    main()