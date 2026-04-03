from __future__ import annotations

import argparse
import gzip
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_deb_index(dist_dir: Path, output_dir: Path) -> Path:
    deb_files = sorted(dist_dir.glob("*.deb"))
    output_dir.mkdir(parents=True, exist_ok=True)
    packages_path = output_dir / "Packages"

    lines: list[str] = []
    for deb in deb_files:
        lines.extend(
            [
                f"Package: {deb.stem}",
                "Version: unknown",
                "Architecture: amd64",
                f"Filename: {deb.name}",
                f"Size: {deb.stat().st_size}",
                f"SHA256: {sha256_file(deb)}",
                "",
            ]
        )

    packages_path.write_text("\n".join(lines), encoding="utf-8")

    packages_gz = output_dir / "Packages.gz"
    with gzip.open(packages_gz, "wt", encoding="utf-8") as gz:
        gz.write(packages_path.read_text(encoding="utf-8"))

    return packages_gz


def write_rpm_index(dist_dir: Path, output_dir: Path) -> Path:
    rpm_files = sorted(dist_dir.glob("*.rpm"))
    repodata_dir = output_dir / "repodata"
    repodata_dir.mkdir(parents=True, exist_ok=True)

    index_path = repodata_dir / "INDEX.txt"
    lines = ["# Lightweight RPM publication index", ""]
    for rpm in rpm_files:
        lines.append(f"{rpm.name} size={rpm.stat().st_size} sha256={sha256_file(rpm)}")

    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate lightweight Debian/RPM repository publication indexes"
    )
    parser.add_argument(
        "--dist", default="dist", help="Directory containing built artifacts"
    )
    parser.add_argument(
        "--output",
        default="packaging/linux-repo/index",
        help="Directory for generated repo index files",
    )
    args = parser.parse_args()

    dist_dir = Path(args.dist)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    deb_count = len(list(dist_dir.glob("*.deb"))) if dist_dir.exists() else 0
    rpm_count = len(list(dist_dir.glob("*.rpm"))) if dist_dir.exists() else 0

    summary = output_dir / "SUMMARY.txt"

    if not dist_dir.exists() or (deb_count == 0 and rpm_count == 0):
        summary.write_text(
            "No .deb/.rpm artifacts found. Index generation skipped.\n",
            encoding="utf-8",
        )
        print(summary.read_text(encoding="utf-8").strip())
        return 0

    generated = []
    if deb_count:
        generated.append(str(write_deb_index(dist_dir, output_dir)))
    if rpm_count:
        generated.append(str(write_rpm_index(dist_dir, output_dir)))

    summary.write_text(
        "Generated Linux repo index artifacts:\n" + "\n".join(generated) + "\n",
        encoding="utf-8",
    )
    print(summary.read_text(encoding="utf-8").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
