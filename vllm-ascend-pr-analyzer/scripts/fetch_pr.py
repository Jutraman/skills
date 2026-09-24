# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
GitHub PR Data Fetcher Script for vLLM Ascend

Fetch PR information (title, description and code diff) from GitHub via gh CLI.
Falls back to anonymous GitHub API access if gh is unavailable (rate limited).

Usage:
    python fetch_pr.py --repo <owner/repo> --ids <pr_id1> [pr_id2 ...] --workspace <workspace>

Example:
    python fetch_pr.py --repo vllm-project/vllm-ascend --ids 100 200 --workspace "path/to/miner_2026-04-10-18-06_xxx"
"""

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

DEFAULT_REPO = "vllm-project/vllm-ascend"


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch GitHub PR data")
    parser.add_argument("--repo", default=DEFAULT_REPO, help=f"GitHub repository (default: {DEFAULT_REPO})")
    parser.add_argument("--ids", required=True, nargs="+", help="PR IDs to fetch (space separated)")
    parser.add_argument("--workspace", required=True, help="Workspace directory to use")
    return parser.parse_args()


def get_workspace(workspace_path: str) -> tuple[Path, Path]:
    """Get workspace directory and ensure input/ exists."""
    work_dir = Path(workspace_path)
    input_dir = work_dir / "input"
    work_dir.mkdir(parents=True, exist_ok=True)
    input_dir.mkdir(parents=True, exist_ok=True)
    return work_dir, input_dir


def gh_available() -> bool:
    """Check if gh CLI is available and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def fetch_via_gh(repo: str, pr_id: str) -> dict:
    """Fetch PR title, body and diff via gh CLI."""
    try:
        view_result = subprocess.run(
            ["gh", "pr", "view", str(pr_id), "--repo", repo, "--json", "title,body,url,state,author,labels"],
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
        )
        if view_result.returncode != 0:
            return {"success": False, "error": f"gh pr view failed: {view_result.stderr.strip()}"}

        meta = json.loads(view_result.stdout)

        diff_result = subprocess.run(
            ["gh", "pr", "diff", str(pr_id), "--repo", repo],
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
        )
        if diff_result.returncode != 0:
            return {"success": False, "error": f"gh pr diff failed: {diff_result.stderr.strip()}"}

        return {
            "success": True,
            "meta": meta,
            "diff": diff_result.stdout,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "gh command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_via_api(repo: str, pr_id: str) -> dict:
    """Fetch PR title, body and diff via anonymous GitHub API."""
    base = f"https://api.github.com/repos/{repo}/pulls/{pr_id}"
    try:
        # Fetch metadata
        req = urllib.request.Request(base, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            meta = json.loads(resp.read().decode("utf-8"))

        # Fetch diff
        req_diff = urllib.request.Request(base, headers={"Accept": "application/vnd.github.v3.diff"})
        with urllib.request.urlopen(req_diff, timeout=60) as resp_diff:
            diff = resp_diff.read().decode("utf-8", errors="replace")

        return {
            "success": True,
            "meta": {
                "title": meta.get("title", ""),
                "body": meta.get("body", "") or "",
                "url": meta.get("html_url", ""),
                "state": meta.get("state", ""),
                "author": (meta.get("user") or {}).get("login", ""),
                "labels": [l.get("name", "") for l in meta.get("labels", [])],
            },
            "diff": diff,
        }
    except Exception as e:
        return {"success": False, "error": f"GitHub API failed: {e}"}


def fetch_single_pr(repo: str, pr_id: str) -> dict:
    """Fetch single PR data, preferring gh CLI over anonymous API."""
    if gh_available():
        result = fetch_via_gh(repo, pr_id)
        if result["success"]:
            return result
        print(f"  - gh CLI failed ({result['error']}), trying GitHub API...")

    return fetch_via_api(repo, pr_id)


def format_pr_markdown(repo: str, pr_id: str, meta: dict, diff: str) -> str:
    """Format PR metadata and diff into a single markdown file content."""
    labels = ", ".join(meta.get("labels", []) or [])
    body = meta.get("body", "") or ""

    return f"""# PR-{pr_id} Metadata ({repo})

- Title: {meta.get('title', '')}
- URL: {meta.get('url', '')}
- State: {meta.get('state', '')}
- Author: {meta.get('author', '')}
- Labels: {labels}

## Description

{body}

---

# PR-{pr_id} Diff

```diff
{diff}
```
"""


def save_pr_data(content: str, save_dir: Path, repo: str, pr_id: str) -> Path:
    """Save PR metadata and diff to markdown file: {repo}_{pr_id}.md"""
    repo_slug = repo.replace("/", "_")
    md_file = save_dir / f"{repo_slug}_{pr_id}.md"
    md_file.write_text(content, encoding="utf-8")
    return md_file


def main(repo: str, pr_ids: list[str], workspace_path: str) -> Path:
    work_dir, input_dir = get_workspace(workspace_path)

    print(f"Repository: {repo}")
    print(f"PR IDs: {pr_ids}")

    results = []
    for pr_id in pr_ids:
        print(f"\nFetching PR {pr_id} from {repo}...")
        result = fetch_single_pr(repo, str(pr_id))
        results.append(result)

        if result["success"]:
            content = format_pr_markdown(repo, str(pr_id), result["meta"], result["diff"])
            saved = save_pr_data(content, input_dir, repo, str(pr_id))
            print(f"  - Saved: {saved}")
        else:
            print(f"  - Error: {result.get('error', 'Unknown error')}")

    success_count = sum(1 for r in results if r["success"])
    print("\n=== Summary ===")
    print(f"Total PRs: {len(pr_ids)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(pr_ids) - success_count}")
    print(f"\nResults saved to WORKSPACE: {work_dir}")

    return work_dir


def cli_main():
    """CLI entry point."""
    args = parse_args()
    sys.exit(main(repo=args.repo, pr_ids=args.ids, workspace_path=args.workspace))


if __name__ == "__main__":
    cli_main()
