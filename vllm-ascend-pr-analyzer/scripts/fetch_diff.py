"""
Diff File Processor Script

Process local code change files (.diff, .patch) for vLLM Ascend PR analysis tasks.
Converts diff files to markdown format with repo root information.

Usage:
    python fetch_diff.py --file <file> --repo <repo_path> --workspace <workspace>

Example:
    python fetch_diff.py --file "path/to/changes.diff" --repo "path/to/repo" --workspace "path/to/miner_2026-04-10-18-06_xxx"
"""

import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Process local diff/patch files for vLLM Ascend PR analysis")
    parser.add_argument("--file", required=True, help="Local diff/patch file path")
    parser.add_argument("--repo", default="unknown", help="Git repository root path (default: unknown)")
    parser.add_argument("--workspace", required=True, help="Workspace directory to use")
    return parser.parse_args()


def get_workspace(workspace_path: str) -> tuple[Path, Path]:
    """Get workspace directory.

    Args:
        workspace_path: Workspace directory path from init_workspace.py

    Returns:
        Tuple of (workspace_dir, input_dir)
    """
    work_dir = Path(workspace_path)
    input_dir = work_dir / "input"
    work_dir.mkdir(parents=True, exist_ok=True)
    input_dir.mkdir(parents=True, exist_ok=True)

    return work_dir, input_dir


def convert_diff_to_md(file_path: str, repo_root: str, input_dir: Path) -> dict:
    """Convert diff/patch file to markdown format.

    Output format:
    repo_root: {repo_root}
    ---

    ```{diff content}```

    Args:
        file_path: Source diff/patch file path
        repo_root: Git repository root path
        input_dir: Target input directory

    Returns:
        Dict with file info: {'original_path': str, 'filename': str, 'success': bool}
    """
    src = Path(file_path)

    if not src.exists():
        return {
            "original_path": file_path,
            "filename": "",
            "success": False,
            "error": f"File not found: {file_path}"
        }

    try:
        # Read diff content
        diff_content = src.read_text(encoding="utf-8")

        # Generate markdown content
        stem = src.stem
        filename = f"diff_{stem}.md"

        dst = input_dir / filename

        # Handle filename conflicts
        counter = 1
        while dst.exists():
            filename = f"diff_{stem}_{counter}.md"
            dst = input_dir / filename
            counter += 1

        # Create markdown file
        md_content = f"repo_root: {repo_root}\n\n---\n\n```{diff_content}\n```"
        dst.write_text(md_content, encoding="utf-8")

        return {
            "original_path": file_path,
            "filename": filename,
            "success": True
        }
    except Exception as e:
        return {
            "original_path": file_path,
            "filename": "",
            "success": False,
            "error": str(e)
        }


def main(
    diff_file: str,
    repo_root: str,
    workspace_path: str,
) -> Path:
    """Main function to process diff file."""
    # Get workspace directory
    work_dir, input_dir = get_workspace(workspace_path)

    print(f"Diff file: {diff_file}")
    print(f"Repo root: {repo_root}")

    # Convert diff file to markdown
    result = convert_diff_to_md(diff_file, repo_root, input_dir)

    if result["success"]:
        print(f"  - Created: {input_dir / result['filename']}")
    else:
        print(f"  - Error: {result.get('error', 'Unknown error')}")

    return work_dir


def cli_main():
    """CLI entry point."""
    args = parse_args()
    main(
        diff_file=args.file,
        repo_root=args.repo,
        workspace_path=args.workspace,
    )


if __name__ == "__main__":
    cli_main()
