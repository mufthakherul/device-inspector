# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Upload client for opt-in report submission.

Provides a lightweight HTTP client (stdlib only) to upload report bundles
to a remote API endpoint.
"""

from __future__ import annotations

import json
import mimetypes
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple
from urllib import error, request


class UploadError(RuntimeError):
    """Raised when upload fails."""


def _iter_upload_files(output_dir: Path) -> Iterable[Tuple[str, Path]]:
    """Yield report files to include in upload."""
    report_json = output_dir / "report.json"
    if report_json.exists():
        yield ("report_json", report_json)

    report_pdf = output_dir / "report.pdf"
    if report_pdf.exists():
        yield ("report_pdf", report_pdf)

    report_txt = output_dir / "report.txt"
    if report_txt.exists():
        yield ("report_txt", report_txt)

    artifacts_dir = output_dir / "artifacts"
    if artifacts_dir.exists():
        for artifact in sorted(artifacts_dir.iterdir()):
            if artifact.is_file():
                yield ("artifacts", artifact)


def _build_multipart_body(
    fields: Dict[str, str], files: Iterable[Tuple[str, Path]], boundary: str
) -> bytes:
    """Build multipart/form-data payload body."""
    lines: list[bytes] = []
    sep = f"--{boundary}".encode("utf-8")

    for key, value in fields.items():
        lines.extend(
            [
                sep,
                (f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}').encode(
                    "utf-8"
                ),
            ]
        )

    for field_name, file_path in files:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or "application/octet-stream"
        lines.extend(
            [
                sep,
                (
                    f'Content-Disposition: form-data; name="{field_name}"; '
                    f'filename="{file_path.name}"\r\n'
                    f"Content-Type: {mime_type}\r\n\r\n"
                ).encode("utf-8"),
                file_path.read_bytes(),
            ]
        )

    lines.extend([f"--{boundary}--".encode("utf-8"), b""])
    return b"\r\n".join(lines)


def _normalize_upload_endpoint(upload_url: str) -> str:
    """Normalize upload URL to include /reports endpoint."""
    normalized = upload_url.rstrip("/")
    if normalized.endswith("/reports"):
        return normalized
    return f"{normalized}/reports"


def upload_report_bundle(
    upload_url: str,
    token: str,
    output_dir: Path,
    timeout: int = 30,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Upload report bundle to remote server.

    Args:
        upload_url: Base URL or /reports endpoint URL
        token: Bearer token for authentication
        output_dir: Run output directory containing report + artifacts
        timeout: HTTP timeout in seconds
        metadata: Optional metadata map to include

    Returns:
        Parsed JSON response dict (if server returns JSON), otherwise
        dict containing HTTP status and raw response text.
    """
    endpoint = _normalize_upload_endpoint(upload_url)
    files = list(_iter_upload_files(output_dir))
    if not files:
        raise UploadError(f"No uploadable files found in {output_dir}")

    payload_metadata = metadata or {}
    fields = {"metadata": json.dumps(payload_metadata, separators=(",", ":"))}
    boundary = f"inspecta-{uuid.uuid4().hex}"
    body = _build_multipart_body(fields=fields, files=files, boundary=boundary)

    req = request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json, text/plain;q=0.8, */*;q=0.5",
            "User-Agent": "inspecta-agent/0.1.0",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            raw = resp.read().decode("utf-8", errors="replace")
            if not raw:
                return {"status": status}

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {"status": status, "response": raw}

            if "status" not in data:
                data["status"] = status
            return data
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise UploadError(
            f"Upload failed with HTTP {exc.code}: {detail or exc.reason}"
        ) from exc
    except error.URLError as exc:
        raise UploadError(f"Upload connection failed: {exc.reason}") from exc
