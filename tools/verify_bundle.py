# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Verify inspecta output bundle integrity via evidence manifest.

Validates `artifacts/manifest.json` hashes against files in the bundle.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent.evidence import verify_evidence_manifest


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Verify an inspecta artifact bundle using SHA256 manifest"
    )
    parser.add_argument("bundle", help="Path to bundle directory")
    parser.add_argument(
        "--manifest",
        default="artifacts/manifest.json",
        help="Relative path to manifest file (default: artifacts/manifest.json)",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Print JSON output instead of human-readable text",
    )
    args = parser.parse_args(argv[1:])

    bundle_dir = Path(args.bundle)
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        print(f"ERROR: bundle directory not found: {bundle_dir}")
        return 2

    result = verify_evidence_manifest(bundle_dir, args.manifest)

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print("Bundle:", bundle_dir)
        print("Manifest:", args.manifest)
        print("Checked files:", result.get("checked", 0))
        print("Integrity OK:" if result.get("ok") else "Integrity FAILED")
        if result.get("mismatches"):
            print("Mismatches:")
            for item in result["mismatches"]:
                print(f"  - {item.get('path')}: {item.get('reason')}")
        if result.get("error"):
            print("Error:", result["error"])

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
