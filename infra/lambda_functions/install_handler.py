"""Lambda function for generating installation scripts.

This function handles GET requests to the /install endpoint and returns a
bash script that users can pipe to bash for automatic installation of the
AppInit binary. The script detects the user's platform and architecture
automatically and downloads the appropriate binary.

The generated script:
- Detects OS (Linux, macOS) and architecture (amd64, arm64)
- Downloads the appropriate binary using the /download endpoint
- Makes the binary executable
- Attempts to install to /usr/local/bin or current directory
- Provides user feedback throughout the process

Returns:
    Plain text bash script for installation
"""

from typing import Any


def _generate_install_script(domain_name: str, stage: str) -> str:
    """Generate the bash installation script content."""
    return f"""#!/bin/bash
set -e

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case $ARCH in
    x86_64) ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

case $OS in
    darwin) OS="darwin" ;;
    linux) OS="linux" ;;
    *) echo "Unsupported OS: $OS"; exit 1 ;;
esac

echo "Downloading appinit for $OS/$ARCH..."

DOWNLOAD_URL="https://{domain_name}/{stage}/download?platform=$OS&arch=$ARCH"
curl -L -o appinit "$DOWNLOAD_URL"

chmod +x appinit

if [ -w "/usr/local/bin" ]; then
    mv appinit /usr/local/bin/
    echo "appinit installed to /usr/local/bin/appinit"
else
    echo "appinit downloaded to current directory"
    echo "To install globally, run: sudo mv appinit /usr/local/bin/"
fi

echo "Installation complete! Run 'appinit --help' to get started."
"""


def lambda_handler(
    event: dict[str, Any],
    _context: Any,
) -> dict[str, Any]:
    """Generate installation script for AppInit binary.

    Args:
        event: API Gateway event containing request context with domain name and stage
        _context: Lambda context object (unused)

    Returns:
        HTTP response with plain text bash script for automatic installation
        of the AppInit binary with platform/architecture detection
    """
    request_context = event.get("requestContext", {})
    domain_name = request_context.get("domainName", "localhost")
    stage = request_context.get("stage", "dev")

    install_script: str = _generate_install_script(domain_name, stage)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain",
            "Content-Disposition": 'attachment; filename="install.sh"',
        },
        "body": install_script,
    }
