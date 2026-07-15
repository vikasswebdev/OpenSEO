"""
`seo audit` command — comprehensive multi-page site SEO audit.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

logger = logging.getLogger(__name__)

from openseo.analyzers import (
    analyze_content,
    analyze_headings,
    analyze_images,
    analyze_links,
    analyze_meta,
    analyze_schema,
    analyze_title,
    analyze_page_technical,
    analyze_site_technical,
    detect_duplicate_clusters,
    build_link_graph,
)
from openseo.config.manager import get_config_manager
from openseo.crawler.site_crawler import SiteCrawler
from openseo.models.issue import Recommendation, Severity
from openseo.models.result import AuditResult, ScoreBreakdown
from openseo.models.site import SiteAuditResult, DuplicateCluster
from openseo.outputs import get_renderer
from openseo.prompts.manager import PromptManager
from openseo.services.llm import LLMService

console = Console()


def _compute_page_score(breakdown: ScoreBreakdown) -> float:
    """Compute overall weighted score for a single page from category scores."""
    weights = {
        "title": 0.15,
        "meta": 0.15,
        "headings": 0.15,
        "images": 0.10,
        "links": 0.10,
        "content": 0.20,
        "schema_org": 0.15,
    }
    total = sum(getattr(breakdown, k, 0) * w for k, w in weights.items())
    return round(total, 1)


async def _run_site_audit(
    url: str,
    provider: str | None,
    model: str | None,
    output: str,
    no_llm: bool,
    use_playwright: bool,
    max_pages: int,
    max_depth: int,
    ignore_robots: bool,
    verbose: bool,
    no_color: bool,
    sitemap_only: bool = False,
    report: bool = False,
) -> None:
    """Core async site audit logic."""
    config_manager = get_config_manager()
    renderer = get_renderer(output, verbose=verbose, no_color=no_color)

    # ── Crawl ─────────────────────────────────────────────────────────────────
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task_desc = f"Crawling website starting at {url}"
        if sitemap_only:
            task_desc += " (sitemap urls only)"
        elif max_pages > 0:
            task_desc += f" (max {max_pages} pages)"
        else:
            task_desc += " (all pages)"

        task = progress.add_task(f"[cyan]{task_desc}...", total=None)

        start_time = time.monotonic()
        try:
            site_crawler = SiteCrawler(
                url,
                max_pages=max_pages,
                max_depth=max_depth,
                use_playwright=use_playwright,
                ignore_robots=ignore_robots,
                sitemap_only=sitemap_only,
            )
            crawled_pages = await site_crawler.crawl()
        except Exception as e:
            renderer.render_error(f"Crawling failed: {e}")
            raise typer.Exit(1) from e

        if not crawled_pages:
            renderer.render_error("No pages crawled. Check your URL or robots.txt settings.")
            raise typer.Exit(1)

        progress.update(task, description="[cyan]Running deterministic page-level analyzers...")

        # ── Analyze Individual Pages ──────────────────────────────────────────
        page_results: dict[str, AuditResult] = {}
        for page_url, page in crawled_pages.items():
            all_issues = []
            
            # Local deterministic analyzers
            title_issues, title_score = analyze_title(page)
            meta_issues, meta_score = analyze_meta(page)
            heading_issues, heading_score = analyze_headings(page)
            image_issues, image_score = analyze_images(page)
            link_issues, link_score = analyze_links(page)
            schema_issues, schema_score = analyze_schema(page)
            content_issues, content_score = analyze_content(page)
            tech_issues, tech_score = analyze_page_technical(page)

            all_issues.extend(title_issues)
            all_issues.extend(meta_issues)
            all_issues.extend(heading_issues)
            all_issues.extend(image_issues)
            all_issues.extend(link_issues)
            all_issues.extend(schema_issues)
            all_issues.extend(content_issues)
            all_issues.extend(tech_issues)

            # Recalculate content/technical category score incorporating deterministic technical checks
            breakdown = ScoreBreakdown(
                title=title_score,
                meta=meta_score,
                headings=heading_score,
                images=image_score,
                links=link_score,
                schema_org=schema_score,
                content=content_score,
                technical=tech_score,
            )
            overall_score = _compute_page_score(breakdown)

            # LLM Recommendations for single pages (only run for the homepage to save tokens/time)
            page_recommendations = []
            provider_used = None
            model_used = None

            if not no_llm and page_url == site_crawler.base_url:
                progress.update(task, description=f"[cyan]Analyzing homepage with AI: {page_url}...")
                try:
                    llm = LLMService(
                        config_manager,
                        provider_override=provider,
                        model_override=model,
                    )
                    prompt_manager = PromptManager()
                    prompt = prompt_manager.render(
                        "audit",
                        url=page_url,
                        title=page.title or "",
                        meta_description=page.meta_description or "",
                        canonical=page.canonical or "",
                        h1_tags=", ".join(page.h1_tags),
                        word_count=str(page.word_count),
                        images_without_alt=str(len(page.images_without_alt)),
                        internal_links_count=str(len(page.internal_links)),
                        external_links_count=str(len(page.external_links)),
                        schema_types=", ".join(s.type or "?" for s in page.schema_org),
                        has_open_graph="Yes" if page.open_graph.title else "No",
                        response_time_ms=str(page.response_time_ms or "?"),
                        robots_meta=page.robots_meta or "not set",
                        body_text_excerpt=page.body_text[:1500],
                    )
                    response = await llm.generate(prompt)
                    provider_used = llm.provider_name
                    model_used = llm.model_name

                    try:
                        raw = response.content
                        if "```json" in raw:
                            raw = raw.split("```json")[1].split("```")[0]
                        elif "```" in raw:
                            raw = raw.split("```")[1].split("```")[0]
                        llm_data = json.loads(raw.strip())

                        from openseo.models.issue import Category
                        for rec in llm_data.get("recommendations", []):
                            try:
                                cat = Category(rec.get("category", "technical").lower())
                            except ValueError:
                                cat = Category.TECHNICAL
                            page_recommendations.append(
                                Recommendation(
                                    title=rec.get("title", "Recommendation"),
                                    body=rec.get("body", ""),
                                    priority=int(rec.get("priority", 3)),
                                    category=cat,
                                    effort=rec.get("effort", "medium"),
                                    impact=rec.get("impact", "medium"),
                                )
                            )
                    except Exception:
                        pass
                except Exception as e:
                    logger.debug("Failed running page-level LLM analysis: %s", e)

            page_results[page_url] = AuditResult(
                url=page_url,
                page=page,
                issues=all_issues,
                recommendations=page_recommendations,
                score=overall_score,
                score_breakdown=breakdown,
                provider_used=provider_used,
                model_used=model_used,
            )

        # ── Site-Wide Analysis ────────────────────────────────────────────────
        progress.update(task, description="[cyan]Analyzing internal link graph and duplicates...")
        link_graph = build_link_graph(crawled_pages)
        duplicate_clusters = detect_duplicate_clusters(crawled_pages)
        site_issues, site_tech_score = analyze_site_technical(
            crawled_pages,
            sitemap_discovered_urls=site_crawler.sitemap_discovered_urls
        )

        # Calculate average breakdown scores
        avg_title = sum(r.score_breakdown.title for r in page_results.values()) / len(page_results)
        avg_meta = sum(r.score_breakdown.meta for r in page_results.values()) / len(page_results)
        avg_headings = sum(r.score_breakdown.headings for r in page_results.values()) / len(page_results)
        avg_images = sum(r.score_breakdown.images for r in page_results.values()) / len(page_results)
        avg_links = sum(r.score_breakdown.links for r in page_results.values()) / len(page_results)
        avg_content = sum(r.score_breakdown.content for r in page_results.values()) / len(page_results)
        avg_schema = sum(r.score_breakdown.schema_org for r in page_results.values()) / len(page_results)
        avg_tech = sum(r.score_breakdown.technical for r in page_results.values()) / len(page_results)

        site_breakdown = ScoreBreakdown(
            title=avg_title,
            meta=avg_meta,
            headings=avg_headings,
            images=avg_images,
            links=avg_links,
            content=avg_content,
            schema_org=avg_schema,
            technical=avg_tech,
        )

        # Overall site score combines page averages and site-level technical deductions
        site_overall_score = min(avg_tech, site_tech_score) * 0.3 + avg_content * 0.2 + avg_title * 0.15 + avg_meta * 0.15 + avg_headings * 0.10 + avg_links * 0.10
        site_overall_score = round(site_overall_score, 1)

        # LLM Site Summary and recommendations
        site_recommendations = []
        global_provider = None
        global_model = None

        if not no_llm:
            progress.update(task, description="[cyan]Generating site-wide AI strategy...")
            try:
                llm = LLMService(
                    config_manager,
                    provider_override=provider,
                    model_override=model,
                )
                prompt_manager = PromptManager()
                
                # Format issues for LLM summary
                issues_summary_list = []
                for issue in site_issues:
                    issues_summary_list.append(f"- Site Issue: {issue.title} (Severity: {issue.severity.value})")
                for page_url, res in page_results.items():
                    for issue in res.critical_issues:
                        issues_summary_list.append(f"- Page {page_url}: {issue.title} (Critical)")

                first_page = list(crawled_pages.values())[0]
                prompt = prompt_manager.render(
                    "site_summary",
                    url=url,
                    total_pages=str(len(crawled_pages)),
                    orphan_pages=", ".join([u for u, n in link_graph.items() if n.is_orphan]) or "None",
                    duplicate_clusters_count=str(len(duplicate_clusters)),
                    sitemaps=", ".join(first_page.sitemap_urls) or "None",
                    robots_txt=first_page.robots_txt or "None",
                    site_issues="\n".join(issues_summary_list[:20]) or "None",
                )
                response = await llm.generate(prompt)
                global_provider = llm.provider_name
                global_model = llm.model_name

                try:
                    raw = response.content
                    if "```json" in raw:
                        raw = raw.split("```json")[1].split("```")[0]
                    elif "```" in raw:
                        raw = raw.split("```")[1].split("```")[0]
                    llm_data = json.loads(raw.strip())

                    from openseo.models.issue import Category
                    for rec in llm_data.get("recommendations", []):
                        try:
                            cat = Category(rec.get("category", "technical").lower())
                        except ValueError:
                            cat = Category.TECHNICAL
                        site_recommendations.append(
                            Recommendation(
                                title=rec.get("title", "Recommendation"),
                                body=rec.get("body", ""),
                                priority=int(rec.get("priority", 3)),
                                category=cat,
                                effort=rec.get("effort", "medium"),
                                impact=rec.get("impact", "medium"),
                            )
                        )
                except Exception:
                    pass
            except Exception as e:
                logger.debug("Failed running site-level LLM strategy: %s", e)

    duration_ms = (time.monotonic() - start_time) * 1000

    site_result = SiteAuditResult(
        url=url,
        duration_ms=round(duration_ms, 1),
        pages=page_results,
        link_graph=link_graph,
        duplicate_clusters=duplicate_clusters,
        score=site_overall_score,
        score_breakdown=site_breakdown,
        site_issues=site_issues,
        site_recommendations=site_recommendations,
        sitemap_discovered_urls=list(site_crawler.sitemap_discovered_urls),
        provider_used=global_provider,
        model_used=global_model,
    )

    # ── Render Report ─────────────────────────────────────────────────────────
    # If the output format is JSON or Markdown, output the site-wide JSON representation
    if output == "json":
        print(site_result.model_dump_json(indent=2))
    elif output == "markdown":
        # Simply format it as Markdown representation and print it
        lines = [
            f"# Site SEO Audit Report: {site_result.url}",
            f"",
            f"**Site SEO Score:** {site_result.score:.0f}/100",
            f"**Total Pages Crawled:** {site_result.total_pages}",
            f"**Orphan Pages Detected:** {len(site_result.orphan_pages)}",
            f"**Duplicate Content Clusters:** {len(site_result.duplicate_clusters)}",
            f"",
            f"---",
            f"",
            f"## Site-Wide Issues",
            f"",
        ]
        for issue in site_result.site_issues:
            lines.append(f"- **{issue.title}** ({issue.severity.value}): {issue.description}")
        lines.append("")
        if site_result.site_recommendations:
            lines.append("## AI Strategic Recommendations")
            for i, rec in enumerate(site_result.site_recommendations, 1):
                lines.append(f"### {i}. {rec.title} (Priority: {rec.priority}, Impact: {rec.impact})")
                lines.append(f"{rec.body}")
                lines.append("")
        print("\n".join(lines))
    else:
        # Terminal format
        # If terminal renderer doesn't support site audit natively, we pass it down and update it
        if hasattr(renderer, "render_site_audit"):
            # Call site-level renderer
            renderer.render_site_audit(site_result)  # type: ignore[attr-defined]
        else:
            # Fallback to rendering the homepage result
            homepage_result = page_results.get(site_crawler.base_url)
            if homepage_result:
                renderer.render_audit(homepage_result)
            else:
                renderer.render_error("No homepage results available.")

    # Generate PDF report if requested
    if report:
        from openseo.outputs.pdf import PdfRenderer
        try:
            pdf_path = PdfRenderer().generate_report(site_result)
            renderer.render_success(f"PDF report generated successfully: {pdf_path}")
        except Exception as e:
            renderer.render_error(f"Failed to generate PDF report: {e}")


def register(app: typer.Typer) -> None:
    """Register the audit command with the Typer app."""

    @app.command("audit")
    def audit(
        url: Annotated[Optional[str], typer.Argument(help="URL to audit")] = None,
        provider: Annotated[Optional[str], typer.Option("--provider", "-p", help="LLM provider")] = None,
        model: Annotated[Optional[str], typer.Option("--model", "-m", help="LLM model")] = None,
        output: Annotated[str, typer.Option("--output", "-o", help="Output format: terminal|json|markdown")] = "terminal",
        no_llm: Annotated[bool, typer.Option("--no-llm", help="Skip LLM analysis")] = False,
        playwright: Annotated[bool, typer.Option("--playwright", help="Use Playwright (JS rendering)")] = False,
        max_pages: Annotated[int, typer.Option("--max-pages", help="Max pages to crawl for site audits (0 for unlimited)")] = 10,
        max_depth: Annotated[int, typer.Option("--depth", help="Maximum directory depth to crawl")] = 3,
        ignore_robots: Annotated[bool, typer.Option("--ignore-robots", help="Ignore robots.txt instructions")] = False,
        report: Annotated[bool, typer.Option("--report", help="Generate a PDF report in results/ folder")] = False,
        sitemap_only: Annotated[bool, typer.Option("--sitemap-only", help="Only crawl URLs listed in sitemap.xml")] = False,
        interactive: Annotated[bool, typer.Option("--interactive", "-i", help="Run audit in interactive mode")] = False,
        verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
        no_color: Annotated[bool, typer.Option("--no-color", help="Disable color output")] = False,
    ) -> None:
        """
        Run a comprehensive site-wide SEO audit starting at a URL.

        If no URL is supplied, OpenSEO enters interactive wizard mode.

        Examples:

          seo audit

          seo audit https://example.com

          seo audit https://example.com --max-pages 5 --depth 2
        """
        if interactive or not url:
            typer.secho("\n🌐 Welcome to the OpenSEO Audit Wizard!\n", fg=typer.colors.CYAN, bold=True)
            if not url:
                url = typer.prompt("Enter the website URL to audit (e.g. https://example.com)")
            
            # Interactive prompts
            max_pages = typer.prompt("Maximum pages to crawl (0 for unlimited)", default=10, type=int)
            max_depth = typer.prompt("Crawl depth", default=3, type=int)
            sitemap_only = typer.confirm("Crawl sitemap URLs only?", default=False)
            playwright = typer.confirm("Use Playwright (JS rendering)?", default=False)
            
            # Ask about LLM
            disable_llm = typer.confirm("Skip AI strategic recommendations?", default=False)
            no_llm = disable_llm
            
            # Ask about PDF report
            report = typer.confirm("Generate a PDF report in results/ folder?", default=True)
            typer.secho("\n🚀 Configuration locked! Starting audit...\n", fg=typer.colors.GREEN)

        asyncio.run(
            _run_site_audit(
                url,
                provider,
                model,
                output,
                no_llm,
                playwright,
                max_pages,
                max_depth,
                ignore_robots,
                verbose,
                no_color,
                sitemap_only=sitemap_only,
                report=report,
            )
        )
