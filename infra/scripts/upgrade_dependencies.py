#!/usr/bin/env python3
"""Upgrades the Python runtime and unpinned dependencies to latest versions.

This script performs a full project modernization by updating both the 
Python language version (runtime) and the project dependencies. It uses `uv`
to enforce these updates by modifying `pyproject.toml` in place.

Logic for upgrades:
    * **Python Runtime:** Checks the `requires-python` constraint against the
        latest stable CPython release available via `uv`. If a newer stable
        version exists (e.g., 3.12 -> 3.13), it updates the project configuration
        and installs the new runtime.
    * **Dependencies (Protected):** Packages with strict locks (`==`, `^`,
        `~=`, or `<`) are skipped to preserve compatibility.
    * **Dependencies (Targeted):** Packages with open constraints (`>=`) or
        no constraints are cycled (`uv remove` -> `uv add`) to force a resolution 
        to the absolute latest upstream version.

The automation sequence is:
    1.  Updates the `uv` binary (`uv self update`).
    2.  Checks for and installs the latest stable Python version.
    3.  Filters dependencies based on locking constraints.
    4.  Cycles target dependencies to fetch latest versions.
    5.  Generates a delta report of version changes.
    6.  Optionally relocks and rebuilds the virtual environment.

Usage:
    Run via `uv` from the project root:
    $ uv run -m scripts.upgrade_dependencies [flags]

Args:
    --relock (flag): Force regeneration of `uv.lock` after the update cycle.
    --rebuild-venv (flag): Delete and recreate the `.venv` directory.

Examples:
    Update Python and unpinned deps (safest):
    $ uv run -m scripts.upgrade_dependencies

    Update and guarantee a fresh lockfile:
    $ uv run -m scripts.upgrade_dependencies --relock

    Full system reset (Runtime, Deps, Lock, Venv):
    $ uv run -m scripts.upgrade_dependencies --relock --rebuild-venv

Requires:
    * `uv` package manager installed and in PATH.
    * `pyproject.toml` in the current working directory.
    * `tomli` (if using Python < 3.11).

Warning:
    This script modifies `pyproject.toml` in place. Ensure you have a clean
    git state before running to allow for easy rollback.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime

import tomli


class DependencyRefresher:
    def __init__(self, relock: bool = False, rebuild_venv: bool = False, skip_confirm: bool = False) -> None:
        self.version_changes: list[tuple[str, str, str | None, str | None]] = []
        self.failed: list[tuple[str, str, str]] = []
        self.start_time: datetime = datetime.now()
        self.relock: bool = relock
        self.rebuild_venv: bool = rebuild_venv
        self.skip_confirm: bool = skip_confirm

    def run_command(
        self, cmd: list[str], capture_output: bool = True, show_command: bool = False
    ) -> bool | tuple[bool, str, str]:
        if show_command:
            print(f"$ {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=capture_output, text=True)
        if not capture_output:
            return result.returncode == 0
        return result.returncode == 0, result.stdout, result.stderr

    def extract_version_from_dep(self, dep_string: str) -> str | None:
        for sep in [">=", "<=", "==", "!=", ">", "<", "~="]:
            if sep in dep_string:
                return dep_string.split(sep, 1)[1].strip()
        return None

    def should_update_dependency(self, dep_string: str) -> bool:
        """Check if dependency should be updated based on its constraint."""
        if "==" in dep_string:
            return False
        if "^" in dep_string:
            return False
        if "~=" in dep_string:
            return False
        if "<" in dep_string and ">=" not in dep_string:
            return False
        return True

    def get_installed_version(self, package_name: str) -> str | None:
        # Strip extras for version checking (e.g., "botocore[crt]" → "botocore")
        base_package = package_name.split('[')[0]
        result = self.run_command(["uv", "pip", "show", base_package])
        if isinstance(result, tuple) and result[0]:
            for line in result[1].split("\n"):
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
        return None

    def is_stable_python_version(self, version: str) -> bool:
        """Check if a Python version is a stable release (no alpha, beta, rc)."""
        # Stable versions should only contain digits and dots
        import re

        return bool(re.match(r"^\d+\.\d+\.\d+$", version))

    def get_latest_python_version(self) -> str | None:
        """Get the latest stable Python version from uv."""
        result = self.run_command(["uv", "python", "list"])
        if isinstance(result, tuple) and result[0]:
            versions = []
            for line in result[1].split("\n"):
                if "cpython-" in line:
                    # Extract version from lines like "cpython-3.12.7-macos-aarch64-none"
                    parts = line.split()
                    if parts:
                        version_part = parts[0]
                        if "cpython-" in version_part:
                            version = version_part.split("cpython-")[1].split("-")[0]
                            # Only include stable releases
                            if self.is_stable_python_version(version):
                                versions.append(version)

            if versions:
                # Sort versions and return the latest stable one
                versions.sort(key=lambda x: tuple(map(int, x.split("."))))
                return versions[-1]
        return None

    def update_python_version(self) -> None:
        """Update the Python version in pyproject.toml if a newer version is available."""
        pyproject_path = Path("pyproject.toml")

        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        current_python = data.get("project", {}).get("requires-python", "")
        if not current_python:
            print("No requires-python found in pyproject.toml")
            return

        # Extract current minimum version (e.g., ">=3.12.0" -> "3.12.0")
        current_version = None
        for prefix in [">=", ">", "==", "~="]:
            if current_python.startswith(prefix):
                current_version = current_python[len(prefix) :].strip()
                break

        if not current_version:
            print(f"Could not parse current Python version: {current_python}")
            return

        print("Checking for latest Python version...")
        latest_version = self.get_latest_python_version()
        if not latest_version:
            print("Could not determine latest Python version")
            return

        # Compare versions
        current_parts = tuple(map(int, current_version.split(".")))
        latest_parts = tuple(map(int, latest_version.split(".")))

        if latest_parts > current_parts:
            print(f"Python version: {current_version} → {latest_version}")

            if not self.skip_confirm:
                response = input(f"Upgrade from Python {current_version} to Python {latest_version}? [y/N]: ")
                if response.lower() != "y":
                    print("Skipping Python upgrade.")
                    return

            # Install the latest Python version
            print(f"Installing Python {latest_version}...")
            install_result = self.run_command(["uv", "python", "install", latest_version])
            if not (isinstance(install_result, tuple) and install_result[0]):
                print(f"Warning: Failed to install Python {latest_version}")
                return

            # Update pyproject.toml
            new_python_req = current_python.replace(current_version, latest_version)

            # Read the file as text to preserve formatting
            with open(pyproject_path, "r") as f:
                content = f.read()

            # Replace the requires-python line
            content = content.replace(f'requires-python = "{current_python}"', f'requires-python = "{new_python_req}"')

            with open(pyproject_path, "w") as f:
                f.write(content)

            print(f"Updated requires-python to: {new_python_req}")
        else:
            print(f"Python version {current_version} is already up to date")

    def parse_pyproject(self) -> tuple[list[str], list[str]]:
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            print("Error: pyproject.toml not found in current directory")
            sys.exit(1)

        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        regular_deps: list[str] = data.get("project", {}).get("dependencies", [])
        dev_deps: list[str] = data.get("dependency-groups", {}).get("dev", [])
        return regular_deps, dev_deps

    def extract_package_name(self, dep_string: str) -> str:
        for sep in [">=", "<=", "==", "!=", ">", "<", "~=", "[", "@"]:
            if sep in dep_string:
                return dep_string.split(sep)[0].strip()
        return dep_string.strip()

    def refresh_dependencies(self, deps: list[str], is_dev: bool = False) -> None:
        if not deps:
            return

        dep_type = "dev" if is_dev else "regular"
        updatable_deps = [dep for dep in deps if self.should_update_dependency(dep)]
        skipped_deps = [dep for dep in deps if not self.should_update_dependency(dep)]

        print(f"\nProcessing {len(updatable_deps)} {dep_type} dependencies...")
        if skipped_deps:
            print(f"Skipping {len(skipped_deps)} pinned {dep_type} dependencies:")
            for dep in skipped_deps:
                pkg_name = self.extract_package_name(dep)
                constraint = dep.replace(pkg_name, "", 1)
                print(f"  - {pkg_name}{constraint}")

        for dep in updatable_deps:
            pkg_name = self.extract_package_name(dep)
            old_version = self.extract_version_from_dep(dep)

            remove_cmd = ["uv", "remove"]
            if is_dev:
                remove_cmd.append("--dev")
            remove_cmd.append(pkg_name)

            result = self.run_command(remove_cmd)
            success = result if isinstance(result, bool) else result[0]
            if not success:
                print(f"  ✗ Failed to remove {pkg_name}")
                self.failed.append((pkg_name, dep_type, "remove"))
                continue

            add_cmd = ["uv", "add"]
            if is_dev:
                add_cmd.append("--dev")
            add_cmd.append(pkg_name)

            result = self.run_command(add_cmd)
            success = result if isinstance(result, bool) else result[0]
            if not success:
                print(f"  ✗ Failed to re-add {pkg_name}")
                self.failed.append((pkg_name, dep_type, "add"))
            else:
                new_version = self.get_installed_version(pkg_name)
                self.version_changes.append((pkg_name, dep_type, old_version, new_version))

                if old_version and new_version and old_version != new_version:
                    print(f"  ↑ {pkg_name}: {old_version} → {new_version}")
                elif old_version and new_version:
                    print(f"  = {pkg_name}: {old_version} (no change)")
                else:
                    print(f"  ✓ {pkg_name}: installed {new_version}")

    def print_report(self) -> bool:
        duration = datetime.now() - self.start_time

        print("\n" + "=" * 50)
        print("DEPENDENCY REFRESH SUMMARY")
        print("=" * 50)
        print(f"Duration: {duration.total_seconds():.1f} seconds")

        upgrades = [v for v in self.version_changes if v[2] != v[3]]
        no_changes = [v for v in self.version_changes if v[2] == v[3]]

        if upgrades:
            print(f"\n✓ Upgraded ({len(upgrades)}):")
            for pkg_name, _, old_ver, new_ver in upgrades:
                print(f"  {pkg_name}: {old_ver} → {new_ver}")

        if no_changes:
            print(f"\n= No change ({len(no_changes)}):")
            for pkg_name, _, old_ver, _ in no_changes:
                print(f"  {pkg_name}: {old_ver}")

        if self.failed:
            print(f"\n✗ Failed ({len(self.failed)}):")
            for pkg_name, dep_type, operation in self.failed:
                print(f"  {pkg_name} ({dep_type}) - failed to {operation}")

        print("=" * 50)
        total = len(self.version_changes) + len(self.failed)
        print(f"Total: {total} | Upgraded: {len(upgrades)} | Failed: {len(self.failed)}")

        if self.failed:
            print("\n⚠ Warning: Some dependencies failed to refresh.")
            return False
        return True

    def check_prerequisites(self) -> None:
        result = self.run_command(["uv", "--version"])
        if not (isinstance(result, tuple) and result[0]):
            print("Error: uv is not installed or not in PATH")
            print("Install from: https://docs.astral.sh/uv/")
            sys.exit(1)

        if not Path("pyproject.toml").exists():
            print("Error: pyproject.toml not found in current directory")
            sys.exit(1)

        git_result = self.run_command(["git", "status"])
        if not (isinstance(git_result, tuple) and git_result[0]):
            print("Warning: Not in a git repository - consider initializing git for easy rollback")
            if not self.skip_confirm:
                response = input("Continue anyway? [y/N]: ")
                if response.lower() != "y":
                    print("Aborted.")
                    sys.exit(0)

    def run(self) -> None:
        print("UV Dependency Refresh Script")
        print("=" * 50)
        print(f"Working directory: {Path.cwd()}")

        self.check_prerequisites()

        if self.rebuild_venv:
            print("Rebuilding virtual environment...")
            _ = self.run_command(["uv", "venv", "--force"], capture_output=False, show_command=True)

        print("Updating uv...")
        success = self.run_command(["uv", "self", "update"], capture_output=False, show_command=True)
        if not success:
            print("Warning: Failed to update uv")

        self.update_python_version()

        regular_deps, dev_deps = self.parse_pyproject()

        print(f"\ndependencies = [")
        for dep in regular_deps:
            print(f'    "{dep}",')
        print("]")

        print(f"\n[dependency-groups]")
        print(f"dev = [")
        for dep in dev_deps:
            print(f'    "{dep}",')
        print("]")

        if not self.skip_confirm:
            flags: list[str] = []
            if self.relock:
                flags.append("relock")
            if self.rebuild_venv:
                flags.append("rebuild-venv")
            flag_text = f" ({', '.join(flags)})" if flags else ""

            print(f"\n⚠  This will remove and re-add all dependencies to get latest versions{flag_text}")
            response = input("Proceed? [y/N]: ")
            if response.lower() != "y":
                print("Aborted.")
                sys.exit(0)

        self.start_time = datetime.now()

        if regular_deps:
            self.refresh_dependencies(regular_deps, is_dev=False)
        if dev_deps:
            self.refresh_dependencies(dev_deps, is_dev=True)

        if self.relock:
            print("\nRegenerating lock file...")
            _ = self.run_command(["uv", "lock", "--upgrade"], capture_output=False, show_command=True)

        print("\nRunning final uv sync...")
        _ = self.run_command(["uv", "sync"], capture_output=False)

        success = self.print_report()
        if success:
            print("\n✓ All dependencies refreshed successfully!")
        else:
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UV Dependency Refresh Script - refreshes all dependencies to latest versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run -m scripts.upgrade_dependencies                              
  uv run -m scripts.upgrade_dependencies --relock                     
  uv run -m scripts.upgrade_dependencies --relock --rebuild-venv
        """,
    )
    _ = parser.add_argument("--relock", action="store_true", help="Force regenerate uv.lock file after refresh")
    _ = parser.add_argument("--rebuild-venv", action="store_true", help="Remove and recreate virtual environment")

    args = parser.parse_args()

    refresher = DependencyRefresher(relock=args.relock, rebuild_venv=args.rebuild_venv, skip_confirm=False)
    refresher.run()


if __name__ == "__main__":
    main()
