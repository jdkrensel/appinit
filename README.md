# appinit

CLI tool to scaffold new projects with a standardized directory structure for application and infrastructure code.

## Installation

### Quick Install (Recommended)
```bash
curl -sSL https://kkklfsac6b.execute-api.us-east-1.amazonaws.com/prod/install | bash
```

### Manual Build
```bash
go build -o /usr/local/bin/appinit
```

## Quick Start

```bash
appinit create --name my-app
```

Creates a project with:
- `app/` - Application code with Docker support
- `infra/` - AWS CDK infrastructure with staging/prod configs
- Pre-configured `pyproject.toml` for both layers
- Embedded templates ready to customize

## Project Structure

```
my-app/
├── app/
│   ├── src/
│   ├── tests/
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── docker-compose.yml
├── infra/
│   ├── stacks/
│   ├── pyproject.toml
│   ├── app.py
│   ├── cdk.json
│   └── config/
│       ├── staging.json
│       └── prod.json
├── .gitignore
└── README.md
```

## Development Setup

### For appinit CLI Development

1. Clone the repository
2. Build and test locally:
   ```bash
   go run main.go create --name test-app
   DEBUG=1 go run main.go create --name test-app  # with debug logging
   ```

### For Binary Distribution Infrastructure

If working on the AWS deployment system:

1. Open the workspace file (`repo.code-workspace`) in your IDE
2. Install dependencies:
   ```bash
   cd infra && uv sync && cd ..
   ```
3. Install AWS CDK: `npm install -g aws-cdk`
4. Configure AWS CLI with appropriate permissions

**Note**: Binaries are automatically built and deployed via GitHub Actions. Manual deployment is rarely needed.

### Testing Binary Distribution Endpoints

The binary distribution system provides three endpoints for testing:

```bash
# Test the /list endpoint - shows available binaries
curl -s https://kkklfsac6b.execute-api.us-east-1.amazonaws.com/prod/list | jq

# Test the /install endpoint - returns installation script
curl -s https://kkklfsac6b.execute-api.us-east-1.amazonaws.com/prod/install

# Test the /download endpoint - downloads binary for current platform
curl -L -o appinit https://kkklfsac6b.execute-api.us-east-1.amazonaws.com/prod/download

# Test download with specific platform/architecture
curl -L -o appinit-linux https://kkklfsac6b.execute-api.us-east-1.amazonaws.com/prod/download?platform=linux&arch=amd64
curl -L -o appinit-mac-arm https://kkklfsac6b.execute-api.us-east-1.amazonaws.com/prod/download?platform=darwin&arch=arm64

# Test the complete installation flow
curl -fsSL https://kkklfsac6b.execute-api.us-east-1.amazonaws.com/prod/install | sh
```

## Development

```bash
go run main.go create --name test-app
DEBUG=1 go run main.go create --name test-app  # with debug logging
```
