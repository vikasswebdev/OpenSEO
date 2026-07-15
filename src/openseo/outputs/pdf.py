"""
PDF Report Generator using ReportLab.
"""

from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class PdfRenderer:
    """Generates beautiful, professional PDF reports for website audits."""

    def __init__(self, output_dir: Path | None = None) -> None:
        # Default to "Downloads" folder in the user's home directory
        self.output_dir = output_dir or Path.home() / "Downloads"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, result: Any) -> str:
        """
        Generate a PDF report from a SiteAuditResult.

        Returns:
            The absolute path to the generated PDF file.
        """
        from openseo.models.site import SiteAuditResult

        if not isinstance(result, SiteAuditResult):
            raise ValueError("Invalid result type for PDF generator.")

        # Determine filename based on domain
        parsed_url = urlparse(result.url)
        domain = parsed_url.netloc.replace(".", "_") or "site"
        pdf_path = self.output_dir / f"{domain}_seo_report.pdf"

        # Initialize document
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        primary_color = colors.HexColor("#1A365D")  # Deep Blue
        secondary_color = colors.HexColor("#2B6CB0")  # Lighter Blue
        text_color = colors.HexColor("#2D3748")  # Dark Grey
        light_bg = colors.HexColor("#F7FAFC")  # Light Grey
        border_color = colors.HexColor("#E2E8F0")

        title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=32,
            leading=38,
            textColor=primary_color,
            spaceAfter=15,
        )

        subtitle_style = ParagraphStyle(
            "CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=16,
            leading=20,
            textColor=secondary_color,
            spaceAfter=40,
        )

        h1_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=primary_color,
            spaceBefore=20,
            spaceAfter=12,
            keepWithNext=True,
        )

        h2_style = ParagraphStyle(
            "SubSectionHeader",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=secondary_color,
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
        )

        body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=text_color,
            spaceAfter=8,
        )

        bold_style = ParagraphStyle(
            "BoldTextCustom",
            parent=body_style,
            fontName="Helvetica-Bold",
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.whitesmoke,
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=text_color,
        )

        story = []

        # ── COVER PAGE ────────────────────────────────────────────────────────
        story.append(Spacer(1, 100))
        story.append(Paragraph("OpenSEO", ParagraphStyle("Logo", parent=title_style, fontSize=16, textColor=secondary_color)))
        story.append(Paragraph("Website SEO Audit Report", title_style))
        story.append(Paragraph(result.url, subtitle_style))
        story.append(Spacer(1, 100))

        # Metadata block
        meta_data = [
            [Paragraph("Crawl Date:", bold_style), Paragraph(result.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"), body_style)],
            [Paragraph("Pages Crawled:", bold_style), Paragraph(str(result.total_pages), body_style)],
            [Paragraph("Overall Score:", bold_style), Paragraph(f"{result.score:.0f}/100", bold_style)],
            [Paragraph("Audit Duration:", bold_style), Paragraph(f"{result.duration_ms / 1000:.1f}s", body_style)],
        ]
        if result.provider_used:
            meta_data.append([
                Paragraph("AI Advisor:", bold_style),
                Paragraph(f"{result.provider_used} ({result.model_used})", body_style)
            ])

        meta_table = Table(meta_data, colWidths=[120, 300])
        meta_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, border_color),
            ])
        )
        story.append(meta_table)
        story.append(Spacer(1, 200)) # Simple doc templates handle pages dynamically

        # ── EXECUTIVE SUMMARY & SCORE BREAKDOWN ──────────────────────────────
        story.append(Paragraph("Executive Summary", h1_style))
        story.append(
            Paragraph(
                "This report compiles technical SEO performance, heading distributions, image tags, sitemap alignment, "
                "and link graph matrices for the site. Strategic recommendations are generated using advanced LLM analysis.",
                body_style,
            )
        )
        story.append(Spacer(1, 15))

        # Score Summary Table
        breakdown = result.score_breakdown
        score_data = [
            [Paragraph("SEO Category", table_header_style), Paragraph("Score", table_header_style)]
        ]
        for field in ["technical", "content", "title", "meta", "headings", "links", "images", "schema_org"]:
            val = getattr(breakdown, field, 0)
            score_data.append([
                Paragraph(field.replace("_", " ").title(), table_cell_style),
                Paragraph(f"{val:.0f}/100", ParagraphStyle("ScoreVal", parent=table_cell_style, fontName="Helvetica-Bold", textColor=colors.HexColor("#2F855A") if val >= 80 else colors.HexColor("#C05621") if val >= 60 else colors.HexColor("#9B2C2C"))),
            ])

        score_table = Table(score_data, colWidths=[200, 100])
        score_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
                ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(score_table)
        story.append(Spacer(1, 25))

        # ── SITE-WIDE / GLOBAL ISSUES ─────────────────────────────────────────
        story.append(Paragraph("Site-Wide / Global SEO Issues", h1_style))
        
        if result.site_issues:
            global_data = [
                [
                    Paragraph("Severity", table_header_style),
                    Paragraph("Issue Type", table_header_style),
                    Paragraph("Details / Problem", table_header_style),
                    Paragraph("Solution / Fix", table_header_style)
                ]
            ]
            for issue in result.site_issues:
                sev_str = issue.severity.value.upper()
                sev_color = colors.HexColor("#9B2C2C") if sev_str == "CRITICAL" else colors.HexColor("#C05621") if sev_str == "WARNING" else text_color
                global_data.append([
                    Paragraph(sev_str, ParagraphStyle("GlobalSev", parent=table_cell_style, fontName="Helvetica-Bold", textColor=sev_color)),
                    Paragraph(html.escape(issue.title), table_cell_style),
                    Paragraph(html.escape(issue.description), table_cell_style),
                    Paragraph(html.escape(issue.recommendation or "Review and fix configuration."), table_cell_style),
                ])
                
            global_table = Table(global_data, colWidths=[70, 130, 180, 120])
            global_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), secondary_color),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
                    ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            story.append(global_table)
        else:
            story.append(Paragraph("✓ No site-wide technical configuration issues detected.", body_style))
            
        story.append(Spacer(1, 20))

        # ── CRAWLED PAGES DIRECTORY ───────────────────────────────────────────
        story.append(Paragraph("Crawled Pages Summary Index", h1_style))
        dir_data = [
            [
                Paragraph("Page URL Path", table_header_style),
                Paragraph("HTTP Status", table_header_style),
                Paragraph("Page Score", table_header_style),
                Paragraph("Words", table_header_style)
            ]
        ]
        for url, res in result.pages.items():
            parsed_u = urlparse(url)
            path = parsed_u.path or "/"
            dir_data.append([
                Paragraph(path, table_cell_style),
                Paragraph(str(res.page.status_code or "?"), table_cell_style),
                Paragraph(f"{res.score:.0f}", table_cell_style),
                Paragraph(str(res.page.word_count), table_cell_style),
            ])

        dir_table = Table(dir_data, colWidths=[240, 80, 80, 100])
        dir_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
                ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(dir_table)
        story.append(Spacer(1, 25))

        # ── DETAILED PAGE-BY-PAGE AUDITS ──────────────────────────────────────
        story.append(Paragraph("Detailed Page-by-Page Audit Findings", h1_style))
        
        for idx, (url, res) in enumerate(result.pages.items(), 1):
            page_block = []
            page_block.append(Paragraph(f"Page {idx}: {url}", h2_style))
            
            # Metadata table for this page
            p_data = [
                [Paragraph("Status Code:", bold_style), Paragraph(str(res.page.status_code or "200"), body_style)],
                [Paragraph("Word Count:", bold_style), Paragraph(f"{res.page.word_count} words", body_style)],
                [Paragraph("Title Tag:", bold_style), Paragraph(f"{res.page.title or '—'} ({len(res.page.title or '')} chars)", body_style)],
                [Paragraph("Meta Desc:", bold_style), Paragraph(f"{res.page.meta_description or '—'} ({len(res.page.meta_description or '')} chars)", body_style)],
            ]
            p_table = Table(p_data, colWidths=[100, 400])
            p_table.setStyle(
                TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, border_color),
                ])
            )
            page_block.append(p_table)
            page_block.append(Spacer(1, 8))
            
            # Page issues specific to this page
            from openseo.models.issue import Severity
            non_pass_issues = [iss for iss in res.issues if iss.severity != Severity.PASS]
            if non_pass_issues:
                page_block.append(Paragraph("Detected Issues & Fixes:", bold_style))
                issue_rows = [
                    [
                        Paragraph("Severity", table_header_style),
                        Paragraph("Issue / Category", table_header_style),
                        Paragraph("Problem Description", table_header_style),
                        Paragraph("Fix / Solution", table_header_style)
                    ]
                ]
                for iss in non_pass_issues:
                    sev_str = iss.severity.value.upper()
                    sev_color = colors.HexColor("#9B2C2C") if sev_str == "CRITICAL" else colors.HexColor("#C05621") if sev_str == "WARNING" else text_color
                    issue_rows.append([
                        Paragraph(sev_str, ParagraphStyle("PageSev", parent=table_cell_style, fontName="Helvetica-Bold", textColor=sev_color)),
                        Paragraph(html.escape(iss.title), table_cell_style),
                        Paragraph(html.escape(iss.description or ""), table_cell_style),
                        Paragraph(html.escape(iss.recommendation or "Verify page configuration."), table_cell_style),
                    ])
                issue_table = Table(issue_rows, colWidths=[60, 110, 190, 140])
                issue_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), secondary_color),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
                        ("GRID", (0, 0), (-1, -1), 0.5, border_color),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ])
                )
                page_block.append(issue_table)
            else:
                page_block.append(Paragraph("✓ This page passed all SEO rules checks.", body_style))
                
            page_block.append(Spacer(1, 20))
            story.append(KeepTogether(page_block))

        # ── SITE-WIDE AI RECOMMENDATIONS ──────────────────────────────────────
        if result.site_recommendations:
            story.append(Spacer(1, 25))
            story.append(Paragraph("Strategic AI Recommendations", h1_style))
            for i, rec in enumerate(result.site_recommendations, 1):
                rec_block = []
                rec_block.append(Paragraph(f"<b>{i}. {rec.title}</b> (Priority {rec.priority} • Effort: {rec.effort} • Impact: {rec.impact})", h2_style))
                rec_block.append(Paragraph(rec.body, body_style))
                story.append(KeepTogether(rec_block))
                story.append(Spacer(1, 10))

        # Build document
        doc.build(story)

        return str(pdf_path.resolve())
