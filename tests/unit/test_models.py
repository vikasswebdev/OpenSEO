import pytest
from openseo.models.page import Page, HeadingNode, ImageData, LinkData
from openseo.models.issue import Issue, Severity, Category
from openseo.models.result import AuditResult, ScoreBreakdown

def test_page_model_links():
    page = Page(
        url="https://example.com",
        headings=[HeadingNode(level=1, text="Main Page Heading")],
        images=[
            ImageData(src="https://example.com/img1.png", alt="First"),
            ImageData(src="https://example.com/img2.png")
        ],
        links=[
            LinkData(href="https://example.com/about", is_external=False),
            LinkData(href="https://google.com", is_external=True)
        ]
    )
    assert len(page.h1_tags) == 1
    assert page.h1_tags[0] == "Main Page Heading"
    assert len(page.internal_links) == 1
    assert len(page.external_links) == 1
    assert len(page.images_without_alt) == 1

def test_audit_result_properties():
    page = Page(url="https://example.com")
    issues = [
        Issue(
            id="test_issue_1",
            title="Critical Problem",
            description="Details",
            severity=Severity.CRITICAL,
            category=Category.TECHNICAL
        ),
        Issue(
            id="test_issue_2",
            title="A Warning",
            description="Details",
            severity=Severity.WARNING,
            category=Category.TECHNICAL
        ),
        Issue(
            id="test_issue_3",
            title="Passing Check",
            description="Details",
            severity=Severity.PASS,
            category=Category.TECHNICAL
        )
    ]
    result = AuditResult(
        url="https://example.com",
        page=page,
        issues=issues,
        score=75.0,
        score_breakdown=ScoreBreakdown()
    )
    
    assert len(result.critical_issues) == 1
    assert len(result.warnings) == 1
    assert len(result.passed_checks) == 1
    assert result.grade == "C"
