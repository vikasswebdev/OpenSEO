import pytest
from pathlib import Path
from datetime import datetime, timezone

from openseo.models.site import SiteAuditResult
from openseo.models.result import AuditResult, ScoreBreakdown
from openseo.models.page import Page
from openseo.outputs.pdf import PdfRenderer


def test_pdf_report_generation(tmp_path):
    # Construct a minimal SiteAuditResult
    page = Page(
        url="https://example.com",
        title="Example Homepage",
        word_count=120,
    )
    audit_res = AuditResult(
        url="https://example.com",
        page=page,
        score=85.0,
        score_breakdown=ScoreBreakdown(title=85.0, content=90.0),
    )
    
    site_result = SiteAuditResult(
        url="https://example.com",
        timestamp=datetime.now(timezone.utc),
        duration_ms=450.0,
        pages={"https://example.com": audit_res},
        score=85.0,
        score_breakdown=ScoreBreakdown(title=85.0, content=90.0),
    )

    renderer = PdfRenderer(output_dir=tmp_path)
    file_path = renderer.generate_report(site_result)
    
    assert Path(file_path).exists()
    assert Path(file_path).name == "example_com_seo_report.pdf"
