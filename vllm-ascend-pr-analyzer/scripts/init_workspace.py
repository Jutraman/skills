"""
Initialize Workspace Script

Create a new workspace directory for vLLM Ascend PR analysis tasks.

Usage:
    python init_workspace.py --output <path>

Example:
    python init_workspace.py --output "path/to/results"
"""

import argparse
import random
import string
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Initialize workspace for vLLM Ascend PR analysis")
    parser.add_argument("--output", default=None, help="Output directory (default: current directory)")
    return parser.parse_args()


def generate_run_id() -> str:
    """Generate an 8-character unique run ID using uppercase letters and digits."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def create_workspace(output_path: str | None) -> Path:
    """Create workspace directory with timestamp_slug and run_id.

    timestamp_slug format: YYYY-MM-DD-HH-MM (e.g., 2026-04-08-14-35)
    run_id: 8-character alphanumeric string (e.g., 2PMYHAU1)
    """
    timestamp_slug = datetime.now().strftime("%Y-%m-%d-%H-%M")
    run_id = generate_run_id()

    if output_path:
        base_dir = Path(output_path)
    else:
        base_dir = Path.cwd()

    work_dir = base_dir / f"miner_{timestamp_slug}_{run_id}"
    input_dir = work_dir / "input"

    work_dir.mkdir(parents=True, exist_ok=True)
    input_dir.mkdir(parents=True, exist_ok=True)

    return work_dir


def main(output_path: str | None = None) -> Path:
    """Main function to create workspace."""
    work_dir = create_workspace(output_path)
    print(f"<WORKSPACE> created at: {work_dir}")
    return work_dir


def cli_main():
    """CLI entry point."""
    args = parse_args()
    main(output_path=args.output)


if __name__ == "__main__":
    cli_main()
