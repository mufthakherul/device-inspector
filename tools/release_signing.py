"""Release artifact signing helper.

Creates detached ASCII-armored signatures for release artifacts when GPG is available
and credentials are provided by CI secrets.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {
    ".zip",
    ".deb",
    ".rpm",
    ".appimage",
    ".whl",
    ".gz",
}


@dataclass(frozen=True)
class SigningResult:
    file: str
    signature: str
    status: str
    reason: str | None = None


def discover_signable_artifacts(root: Path) -> list[Path]:
    artifacts = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith(".asc"):
            continue
        suffix = path.suffix.lower()
        if suffix in SUPPORTED_SUFFIXES or path.name == "SHA256SUMS":
            artifacts.append(path)
    return artifacts


def _detached_signature_name(source: Path) -> str:
    return f"{source.name}.asc"


def sign_artifact(
    *,
    artifact: Path,
    output_dir: Path,
    gpg_passphrase: str,
    dry_run: bool,
) -> SigningResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    signature_path = output_dir / _detached_signature_name(artifact)

    if dry_run:
        signature_path.write_text("dry-run signature placeholder\n", encoding="utf-8")
        return SigningResult(
            file=str(artifact),
            signature=str(signature_path),
            status="simulated",
        )

    command = [
        "gpg",
        "--batch",
        "--yes",
        "--pinentry-mode",
        "loopback",
        "--passphrase",
        gpg_passphrase,
        "--armor",
        "--detach-sign",
        "--output",
        str(signature_path),
        str(artifact),
    ]

    completed = subprocess.run(command, capture_output=True, text=True, check=False)

    if completed.returncode != 0:
        return SigningResult(
            file=str(artifact),
            signature=str(signature_path),
            status="failed",
            reason=(completed.stderr or completed.stdout or "gpg failed").strip(),
        )

    return SigningResult(
        file=str(artifact),
        signature=str(signature_path),
        status="signed",
    )


def build_signing_report(results: list[SigningResult]) -> dict:
    signed = [r for r in results if r.status in {"signed", "simulated"}]
    failed = [r for r in results if r.status == "failed"]
    return {
        "report_version": "1.0.0",
        "total": len(results),
        "signed_or_simulated": len(signed),
        "failed": len(failed),
        "results": [
            {
                "file": r.file,
                "signature": r.signature,
                "status": r.status,
                "reason": r.reason,
            }
            for r in results
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sign release artifacts")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report", default="release-signatures/signing-report.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fail-on-error", action="store_true")
    parser.add_argument("--gpg-passphrase", default="")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    report_path = Path(args.report).resolve()

    artifacts = discover_signable_artifacts(input_dir)
    results = [
        sign_artifact(
            artifact=artifact,
            output_dir=output_dir,
            gpg_passphrase=args.gpg_passphrase,
            dry_run=args.dry_run,
        )
        for artifact in artifacts
    ]

    report = build_signing_report(results)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("[release-signing] completed")
    print(f"  artifacts: {len(artifacts)}")
    print(f"  output_dir: {output_dir}")
    print(f"  report: {report_path}")

    if args.fail_on_error and report["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
