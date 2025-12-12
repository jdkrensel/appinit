# appinit

CLI tool to scaffold new projects with a standardized directory structure for application and infrastructure code.

## Installation

### Download Binary (Recommended)

Choose the command for your platform:

**macOS (Apple Silicon / M1/M2/M3)**
```bash
curl -L $(cd infra && uv run awscurl --service execute-api "https://8o62fpbbn5.execute-api.us-east-1.amazonaws.com/prod/download?platform=darwin&arch=arm64" | jq -r .url) -o appinit && chmod +x appinit && sudo mv appinit /usr/local/bin/
```

**macOS (Intel)**
```bash
curl -L $(cd infra && uv run awscurl --service execute-api "https://8o62fpbbn5.execute-api.us-east-1.amazonaws.com/prod/download?platform=darwin&arch=amd64" | jq -r .url) -o appinit && chmod +x appinit && sudo mv appinit /usr/local/bin/
```

**Linux (x86_64 / amd64)**
```bash
curl -L $(cd infra && uv run awscurl --service execute-api "https://8o62fpbbn5.execute-api.us-east-1.amazonaws.com/prod/download?platform=linux&arch=amd64" | jq -r .url) -o appinit && chmod +x appinit && sudo mv appinit /usr/local/bin/
```

**Linux (ARM64 / aarch64)**
```bash
curl -L $(cd infra && uv run awscurl --service execute-api "https://8o62fpbbn5.execute-api.us-east-1.amazonaws.com/prod/download?platform=linux&arch=arm64" | jq -r .url) -o appinit && chmod +x appinit && sudo mv appinit /usr/local/bin/
```

**Windows (x86_64)**
```powershell
# PowerShell
$url = (cd infra; uv run awscurl --service execute-api "https://8o62fpbbn5.execute-api.us-east-1.amazonaws.com/prod/download?platform=windows&arch=amd64" | jq -r .url)
curl -L $url -o appinit.exe
# Move to a directory in your PATH
```

**Windows (ARM64)**
```powershell
# PowerShell
$url = (cd infra; uv run awscurl --service execute-api "https://8o62fpbbn5.execute-api.us-east-1.amazonaws.com/prod/download?platform=windows&arch=arm64" | jq -r .url)
curl -L $url -o appinit.exe
# Move to a directory in your PATH
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

```bash
# List available binaries
cd infra && uv run awscurl --service execute-api https://8o62fpbbn5.execute-api.us-east-1.amazonaws.com/prod/list | jq

# Test download endpoint
cd infra && uv run awscurl --service execute-api "https://8o62fpbbn5.execute-api.us-east-1.amazonaws.com/prod/download?platform=darwin&arch=arm64" | jq
```

## Development

```bash
go run main.go create --name test-app
DEBUG=1 go run main.go create --name test-app  # with debug logging
```
