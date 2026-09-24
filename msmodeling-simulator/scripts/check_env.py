# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
msModeling Environment Checker

Verify msModeling (liuren_modeling / tensor_cast) availability before running
simulation commands.

Usage:
    python check_env.py --repo <msmodeling_path> [--model <hf_model>] [--device <device_name>]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Check msModeling environment")
    parser.add_argument("--repo", required=True, help="Path to msmodeling repository")
    parser.add_argument("--model", default=None, help="HuggingFace model id to verify locally")
    parser.add_argument("--device", default=None, help="Target device name to check in supported list")
    return parser.parse_args()


SUPPORTED_DEVICES = [
    "A2", "A3", "A5", "H20", "H800", "H100", "H200", "B30A",
    "RTX4090", "RTX6000D", "P800", "PPU", "MLU590", "MLU690",
]


def check_repo(repo: str) -> bool:
    root = Path(repo)
    if not root.exists():
        print(f"[FAIL] repo not found: {repo}")
        return False
    print(f"[ OK ] repo exists: {repo}")

    tensor_cast = root / "tensor_cast"
    liuren = root / "liuren_modeling"
    for d in (tensor_cast, liuren):
        if d.exists():
            print(f"[ OK ] module dir exists: {d.name}")
        else:
            print(f"[WARN] module dir missing: {d.name}")

    scripts = tensor_cast / "scripts"
    if scripts.exists():
        found = [p.name for p in scripts.glob("*.py")]
        print(f"[ OK ] tensor_cast/scripts entries: {found}")
    else:
        print(f"[WARN] tensor_cast/scripts not found under {tensor_cast}")
    return True


def check_import(repo: str) -> bool:
    try:
        r = subprocess.run(
            [sys.executable, "-c", "import tensor_cast"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode == 0:
            print("[ OK ] `import tensor_cast` succeeded")
            return True
        print(f"[FAIL] import tensor_cast failed: {r.stderr.strip()[:200]}")
        return False
    except Exception as e:
        print(f"[FAIL] import check error: {e}")
        return False


def check_model(model: str) -> None:
    if not model:
        return
    print(f"[INFO] model '{model}': ensure it is downloadable from HF or exists locally")
    print("       (offline environments must pre-download; msModeling reads model structure via Transformers/Diffusers)")


def check_device(device: str) -> None:
    if not device:
        return
    hit = [k for k in SUPPORTED_DEVICES if k.lower() in device.lower()]
    if hit:
        print(f"[ OK ] device '{device}' matches supported family: {hit}")
    else:
        print(f"[WARN] device '{device}' not in supported list {SUPPORTED_DEVICES};")
        print("       use a custom hardware params file (mma_ops/gp_ops/bandwidth/topologies) for what-if analysis")


def main():
    args = parse_args()
    ok = check_repo(args.repo)
    ok = check_import(args.repo) and ok
    check_model(args.model)
    check_device(args.device)
    print("\n=== Summary ===")
    print("READY" if ok else "ENVIRONMENT INCOMPLETE — fix [FAIL] items above")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
