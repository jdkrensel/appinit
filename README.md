# appinit

CLI tool to scaffold new projects with a standardized directory structure for application and infrastructure code.

## Installation

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

## Development

```bash
go run main.go create --name test-app
DEBUG=1 go run main.go create --name test-app  # with debug logging
```
