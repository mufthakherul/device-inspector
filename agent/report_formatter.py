# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Report formatting utilities for human-readable outputs.

Generates TXT and PDF reports from inspection data.
"""
from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


def format_txt_report(report: Dict[str, Any]) -> str:
    """Format a report as human-readable text.

    Args:
        report: Report dictionary from compose_report()

    Returns:
        Formatted text report as a string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("DEVICE INSPECTION REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Header information
    lines.append(f"Generated: {report.get('generated_at', 'N/A')}")
    lines.append(
        f"Agent: {report.get('agent', {}).get('name', 'N/A')} "
        f"v{report.get('agent', {}).get('version', 'N/A')}"
    )
    lines.append(f"Mode: {report.get('mode', 'N/A')}")
    lines.append(f"Profile: {report.get('profile', 'N/A')}")
    lines.append("")

    # Device Information
    lines.append("-" * 80)
    lines.append("DEVICE INFORMATION")
    lines.append("-" * 80)
    device = report.get("device", {})
    lines.append(f"Vendor:       {device.get('vendor', 'Unknown')}")
    lines.append(f"Model:        {device.get('model', 'Unknown')}")
    lines.append(f"Serial:       {device.get('serial', 'N/A')}")
    lines.append(f"BIOS Version: {device.get('bios_version', 'N/A')}")
    if device.get("sku"):
        lines.append(f"SKU:          {device.get('sku')}")
    lines.append("")

    # Summary Scores
    lines.append("-" * 80)
    lines.append("OVERALL ASSESSMENT")
    lines.append("-" * 80)
    summary = report.get("summary", {})
    overall_score = summary.get("overall_score", 0)
    grade = summary.get("grade", "Unknown")
    lines.append(f"Overall Score: {overall_score}/100")
    lines.append(f"Grade:         {grade}")
    lines.append(f"Recommendation: {summary.get('recommendation', 'N/A')}")
    lines.append("")

    # Detailed Scores
    lines.append("-" * 80)
    lines.append("COMPONENT SCORES")
    lines.append("-" * 80)
    scores = report.get("scores", {})
    for component, score in sorted(scores.items()):
        component_name = component.replace("_", " ").title()
        lines.append(f"{component_name:20s} {score:3d}/100")
    lines.append("")

    # Test Results
    tests = report.get("tests", [])
    if tests:
        lines.append("-" * 80)
        lines.append("TEST RESULTS")
        lines.append("-" * 80)
        for test in tests:
            test_name = test.get("name", "Unknown")
            status = test.get("status", "unknown")
            status_detail = test.get("status_detail", "")

            status_symbol = "✓" if status == "ok" else "✗"
            status_text = status.upper()
            if status_detail:
                status_text += f" ({status_detail})"

            lines.append(f"{status_symbol} {test_name:40s} {status_text}")

            # Show device info for SMART tests
            if status == "ok" and "data" in test:
                data = test["data"]
                if "model" in data:
                    lines.append(f"  Model: {data['model']}")
                if "serial" in data:
                    lines.append(f"  Serial: {data['serial']}")

            # Show errors
            if status == "error" and "error" in test:
                lines.append(f"  Error: {test['error']}")
        lines.append("")

    # Artifacts
    artifacts = report.get("artifacts", [])
    if artifacts:
        lines.append("-" * 80)
        lines.append(f"ARTIFACTS ({len(artifacts)} files)")
        lines.append("-" * 80)
        for artifact in sorted(artifacts):
            lines.append(f"  - {artifact}")
        lines.append("")

    # Footer
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    return "\n".join(lines)


def generate_txt_report(report: Dict[str, Any], output_path: Path) -> Path:
    """Generate a TXT report file.

    Args:
        report: Report dictionary from compose_report()
        output_path: Directory where the report should be saved

    Returns:
        Path to the generated TXT file
    """
    txt_content = format_txt_report(report)
    txt_path = output_path / "report.txt"
    txt_path.write_text(txt_content, encoding="utf-8")
    return txt_path


def generate_pdf_report(report: Dict[str, Any], output_path: Path) -> Optional[Path]:
    """Generate a PDF report file using reportlab if available.

    Args:
        report: Report dictionary from compose_report()
        output_path: Directory where the report should be saved

    Returns:
        Path to the generated PDF file, or None if reportlab is not available
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        # reportlab not available, skip PDF generation
        return None

    pdf_path = output_path / "report.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=30,
        alignment=1,  # Center
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2c5282"),
        spaceAfter=12,
        spaceBefore=12,
    )

    # Title
    story.append(Paragraph("DEVICE INSPECTION REPORT", title_style))
    story.append(Spacer(1, 0.2 * inch))

    # Header information
    header_data = [
        ["Generated:", report.get("generated_at", "N/A")],
        [
            "Agent:",
            (
                f"{report.get('agent', {}).get('name', 'N/A')} "
                f"v{report.get('agent', {}).get('version', 'N/A')}"
            ),
        ],
        ["Mode:", report.get("mode", "N/A")],
        ["Profile:", report.get("profile", "N/A")],
    ]
    header_table = Table(header_data, colWidths=[2 * inch, 4 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 0.3 * inch))

    # Device Information
    story.append(Paragraph("DEVICE INFORMATION", heading_style))
    device = report.get("device", {})
    device_data = [
        ["Vendor:", device.get("vendor", "Unknown")],
        ["Model:", device.get("model", "Unknown")],
        ["Serial:", device.get("serial", "N/A")],
        ["BIOS Version:", device.get("bios_version", "N/A")],
    ]
    if device.get("sku"):
        device_data.append(["SKU:", device.get("sku")])

    device_table = Table(device_data, colWidths=[2 * inch, 4 * inch])
    device_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(device_table)
    story.append(Spacer(1, 0.3 * inch))

    # Overall Assessment
    story.append(Paragraph("OVERALL ASSESSMENT", heading_style))
    summary = report.get("summary", {})
    overall_score = summary.get("overall_score", 0)
    grade = summary.get("grade", "Unknown")

    # Color code the grade
    grade_color = colors.green
    if overall_score < 50:
        grade_color = colors.red
    elif overall_score < 75:
        grade_color = colors.orange

    assessment_data = [
        ["Overall Score:", f"{overall_score}/100"],
        ["Grade:", grade],
        ["Recommendation:", summary.get("recommendation", "N/A")],
    ]
    assessment_table = Table(assessment_data, colWidths=[2 * inch, 4 * inch])
    assessment_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TEXTCOLOR", (1, 1), (1, 1), grade_color),
                ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(assessment_table)
    story.append(Spacer(1, 0.3 * inch))

    # Component Scores
    story.append(Paragraph("COMPONENT SCORES", heading_style))
    scores = report.get("scores", {})
    score_data = [["Component", "Score"]]
    for component, score in sorted(scores.items()):
        component_name = component.replace("_", " ").title()
        score_data.append([component_name, f"{score}/100"])

    score_table = Table(score_data, colWidths=[3 * inch, 2 * inch])
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]
        )
    )
    story.append(score_table)

    # Test Results (if available)
    tests = report.get("tests", [])
    if tests:
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("TEST RESULTS", heading_style))

        test_data = [["Test", "Status"]]
        for test in tests:
            test_name = test.get("name", "Unknown")
            status = test.get("status", "unknown")
            status_detail = test.get("status_detail", "")

            status_text = status.upper()
            if status_detail:
                status_text += f" ({status_detail})"

            test_data.append([test_name, status_text])

        test_table = Table(test_data, colWidths=[4 * inch, 2 * inch])
        test_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ]
            )
        )
        story.append(test_table)

    # Build PDF
    doc.build(story)
    return pdf_path


def open_file(file_path: Path) -> bool:
    """Open a file using the system's default application.

    Args:
        file_path: Path to the file to open

    Returns:
        True if the file was opened successfully, False otherwise
    """
    try:
        system = platform.system()
        file_str = str(file_path.resolve())

        if system == "Darwin":  # macOS
            subprocess.run(["open", file_str], check=True)
        elif system == "Windows":
            os.startfile(file_str)
        else:  # Linux and other Unix-like systems
            subprocess.run(["xdg-open", file_str], check=True)

        return True
    except Exception:
        return False
