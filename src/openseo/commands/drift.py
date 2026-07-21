"""
`seo drift` command group — baseline capture, comparison, and change monitoring.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from openseo.crawler.http import HttpCrawler
from openseo.services.drift_store import DriftStore, url_hash, normalize_url, DRIFT_DB
from openseo.constants import (
    SEVERITY_COLORS,
    SEVERITY_ICONS,
    SEVERITY_CRITICAL,
    SEVERITY_WARNING,
    SEVERITY_INFO,
)

console = Console()
drift_app = typer.Typer(
    name="drift",
    help="Monitor content and technical SEO changes over time.",
    no_args_is_help=True,
)


def hash_content(content: str) -> str:
    """SHA-256 hash of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _make_finding(
    rule: str, severity: str, triggered: bool, old_value: any, new_value: any, message: str
) -> dict:
    return {
        "rule": rule,
        "severity": severity,
        "triggered": triggered,
        "old_value": old_value,
        "new_value": new_value,
        "message": message,
    }


def run_drift_rules(baseline: dict, current_page: any) -> list[dict]:
    """Run all comparison rules between a baseline dict and a crawled Page model."""
    findings = []

    # Prepare current state variables
    current_title = (current_page.title or "").strip()
    current_desc = (current_page.meta_description or "").strip()
    current_canonical = current_page.canonical or ""
    current_robots = (current_page.robots_meta or "").lower()
    current_status = current_page.status_code or 200

    h1_list = current_page.h1_tags
    current_h1 = h1_list[0] if h1_list else ""
    current_h2 = [h.text for h in current_page.headings if h.level == 2]
    current_h3 = [h.text for h in current_page.headings if h.level == 3]

    current_schema = [s.raw for s in current_page.schema_org]
    current_schema_str = json.dumps(current_schema, sort_keys=True)
    current_schema_hash = hash_content(current_schema_str) if current_schema else ""

    # Open Graph serialization matching what's saved
    current_og = current_page.open_graph.model_dump()
    current_og_filtered = {k: v for k, v in current_og.items() if v is not None}
    current_html_hash = hash_content(current_page.body_text or "")

    # Load baseline state variables
    old_title = (baseline.get("title") or "").strip()
    old_desc = (baseline.get("meta_description") or "").strip()
    old_canonical = baseline.get("canonical") or ""
    old_robots = (baseline.get("robots") or "").lower()
    old_status = baseline.get("status_code") or 200
    old_h1 = (baseline.get("h1") or "").strip()

    old_h2 = json.loads(baseline.get("h2_json") or "[]")
    old_h3 = json.loads(baseline.get("h3_json") or "[]")
    old_schema = json.loads(baseline.get("schema_json") or "[]")
    old_og = json.loads(baseline.get("og_json") or "{}")
    old_og_filtered = {k: v for k, v in old_og.items() if v is not None}

    # CRITICAL RULES (Rules 1-8)
    # Rule 1: Schema removed
    schema_rem = len(old_schema) > 0 and len(current_schema) == 0
    findings.append(
        _make_finding(
            "schema_removed",
            SEVERITY_CRITICAL,
            schema_rem,
            f"{len(old_schema)} schema block(s)",
            "0 schema blocks",
            "Structured data (JSON-LD) has been removed completely. Rich results eligibility will be lost.",
        )
    )

    # Rule 2: Canonical changed
    canonical_chg = bool(old_canonical) and bool(current_canonical) and old_canonical != current_canonical
    findings.append(
        _make_finding(
            "canonical_changed",
            SEVERITY_CRITICAL,
            canonical_chg,
            old_canonical,
            current_canonical,
            f"Canonical URL changed from '{old_canonical}' to '{current_canonical}'.",
        )
    )

    # Rule 3: Canonical removed
    canonical_rem = bool(old_canonical) and not current_canonical
    findings.append(
        _make_finding(
            "canonical_removed",
            SEVERITY_CRITICAL,
            canonical_rem,
            old_canonical,
            None,
            "Canonical tag has been removed. Google will identify canonicals dynamically, risking duplicates.",
        )
    )

    # Rule 4: Noindex added
    noindex_add = "noindex" not in old_robots and "noindex" in current_robots
    findings.append(
        _make_finding(
            "noindex_added",
            SEVERITY_CRITICAL,
            noindex_add,
            baseline.get("robots"),
            current_page.robots_meta,
            "A 'noindex' directive has been added. The page will be dropped from search rankings.",
        )
    )

    # Rule 5: H1 removed
    h1_rem = bool(old_h1) and not current_h1
    findings.append(
        _make_finding(
            "h1_removed",
            SEVERITY_CRITICAL,
            h1_rem,
            old_h1,
            None,
            "H1 heading has been removed. Primary topic signal is missing.",
        )
    )

    # Rule 6: H1 changed significantly
    if old_h1 and current_h1:
        ratio = SequenceMatcher(None, old_h1, current_h1).ratio()
        h1_chg = ratio < 0.5
        findings.append(
            _make_finding(
                "h1_changed_significantly",
                SEVERITY_CRITICAL,
                h1_chg,
                old_h1,
                current_h1,
                f"H1 changed significantly (similarity: {ratio:.0%}). Keyword targeting might be disrupted.",
            )
        )
    else:
        findings.append(
            _make_finding(
                "h1_changed_significantly",
                SEVERITY_CRITICAL,
                False,
                old_h1,
                current_h1,
                "H1 comparison skipped.",
            )
        )

    # Rule 7: Title removed
    title_rem = bool(old_title) and not current_title
    findings.append(
        _make_finding(
            "title_removed",
            SEVERITY_CRITICAL,
            title_rem,
            old_title,
            None,
            "Title tag has been removed completely.",
        )
    )

    # Rule 8: Status code error
    status_err = (200 <= old_status < 400) and (current_status >= 400)
    findings.append(
        _make_finding(
            "status_code_error",
            SEVERITY_CRITICAL,
            status_err,
            old_status,
            current_status,
            f"Page returns HTTP error status {current_status} (was {old_status}).",
        )
    )

    # WARNING RULES (Rules 9-14)
    # Rule 9: Title changed
    title_chg = bool(old_title) and bool(current_title) and old_title != current_title
    findings.append(
        _make_finding(
            "title_changed",
            SEVERITY_WARNING,
            title_chg,
            old_title,
            current_title,
            "Title tag text has changed. Monitor CTR over the next two weeks.",
        )
    )

    # Rule 10: Meta description changed
    desc_chg = bool(old_desc) and bool(current_desc) and old_desc != current_desc
    findings.append(
        _make_finding(
            "meta_description_changed",
            SEVERITY_WARNING,
            desc_chg,
            old_desc,
            current_desc,
            "Meta description changed.",
        )
    )

    # Rule 13: OG tags removed
    og_rem = len(old_og_filtered) > 0 and len(current_og_filtered) == 0
    findings.append(
        _make_finding(
            "og_tags_removed",
            SEVERITY_WARNING,
            og_rem,
            list(old_og_filtered.keys()),
            [],
            "All Open Graph tags have been removed. Social previews will be broken.",
        )
    )

    # Rule 14: Schema modified
    schema_mod = (
        bool(baseline.get("schema_hash"))
        and bool(current_schema_hash)
        and baseline.get("schema_hash") != current_schema_hash
    )
    findings.append(
        _make_finding(
            "schema_modified",
            SEVERITY_WARNING,
            schema_mod,
            baseline.get("schema_hash")[:12] if baseline.get("schema_hash") else None,
            current_schema_hash[:12] if current_schema_hash else None,
            "Schema content has been modified. Validate structure.",
        )
    )

    # INFO RULES (Rules 15-17)
    # Rule 15: Schema added
    schema_add = len(old_schema) == 0 and len(current_schema) > 0
    findings.append(
        _make_finding(
            "schema_added",
            SEVERITY_INFO,
            schema_add,
            "0 blocks",
            f"{len(current_schema)} blocks",
            "New structured data added.",
        )
    )

    # Rule 16: H2 structure changed
    h2_chg = old_h2 != current_h2
    findings.append(
        _make_finding(
            "h2_structure_changed",
            SEVERITY_INFO,
            h2_chg,
            f"{len(old_h2)} H2s",
            f"{len(current_h2)} H2s",
            "H2 heading structure changed.",
        )
    )

    # Rule 17: Content hash changed
    content_chg = bool(baseline.get("html_hash")) and baseline.get("html_hash") != current_html_hash
    findings.append(
        _make_finding(
            "content_hash_changed",
            SEVERITY_INFO,
            content_chg,
            baseline.get("html_hash")[:12] if baseline.get("html_hash") else None,
            current_html_hash[:12] if current_html_hash else None,
            "Page content has changed (HTML body hash differs from baseline).",
        )
    )

    return findings


async def _crawl_and_extract(url: str) -> any:
    async with HttpCrawler() as crawler:
        return await crawler.fetch(url)


@drift_app.command("baseline")
def drift_baseline(
    url: Annotated[str, typer.Argument(help="URL to baseline")],
) -> None:
    """Capture a new SEO baseline snapshot of a page's elements."""
    typer.echo(f"🕸  Crawling {url}...", err=True)
    try:
        page = asyncio.run(_crawl_and_extract(url))
    except Exception as e:
        console.print(f"[bold red]Error:[/] Could not crawl URL: {e}")
        raise typer.Exit(1)

    norm_url = normalize_url(url)
    uhash = url_hash(url)
    now = datetime.now(timezone.utc).isoformat()

    h1_list = page.h1_tags
    h1_text = h1_list[0] if h1_list else None
    h2_list = [h.text for h in page.headings if h.level == 2]
    h3_list = [h.text for h in page.headings if h.level == 3]

    schema_list = [s.raw for s in page.schema_org]
    schema_str = json.dumps(schema_list, sort_keys=True)
    schema_content_hash = hash_content(schema_str) if schema_list else None
    html_content_hash = hash_content(page.body_text or "")

    og_data = page.open_graph.model_dump()

    baseline_record = {
        "url": norm_url,
        "url_hash": uhash,
        "timestamp": now,
        "title": page.title,
        "meta_description": page.meta_description,
        "canonical": page.canonical,
        "robots": page.robots_meta,
        "h1": h1_text,
        "h2_json": json.dumps(h2_list),
        "h3_json": json.dumps(h3_list),
        "schema_json": json.dumps(schema_list),
        "og_json": json.dumps(og_data),
        "cwv_json": None,  # PageSpeed/CWV integration implemented in Phase 2
        "html_hash": html_content_hash,
        "schema_hash": schema_content_hash,
        "status_code": page.status_code or 200,
    }

    store = DriftStore()
    try:
        baseline_id = store.save_baseline(baseline_record)
        console.print(Panel(
            f"[bold]Baseline Captured Successfully![/]\n\n"
            f"• [bold]ID:[/] {baseline_id}\n"
            f"• [bold]URL:[/] {norm_url}\n"
            f"• [bold]Title:[/] {page.title or 'N/A'}\n"
            f"• [bold]H1 heading:[/] {h1_text or 'N/A'}\n"
            f"• [bold]H2 Headings:[/] {len(h2_list)}\n"
            f"• [bold]Schema Blocks:[/] {len(schema_list)}\n"
            f"• [bold]Status Code:[/] {page.status_code or 200}",
            title="[bold]SEO Drift Baseline",
            border_style="green",
        ))
    except Exception as e:
        console.print(f"[bold red]Database Error:[/] {e}")
        raise typer.Exit(1)


@drift_app.command("compare")
def drift_compare(
    url: Annotated[str, typer.Argument(help="URL to compare")],
    baseline_id: Annotated[Optional[int], typer.Option("--baseline-id", help="Compare to specific baseline ID instead of latest")] = None,
    output: Annotated[str, typer.Option("--output", "-o")] = "terminal",
) -> None:
    """Compare current page state to stored baseline and detect SEO drift."""
    store = DriftStore()
    baseline = store.load_baseline(url, baseline_id)
    if not baseline:
        console.print(f"[bold red]Error:[/] No baseline found for {url}. Run 'seo drift baseline <url>' first.")
        raise typer.Exit(1)

    typer.echo(f"🕸  Crawling current state of {url}...", err=True)
    try:
        page = asyncio.run(_crawl_and_extract(url))
    except Exception as e:
        console.print(f"[bold red]Error:[/] Could not crawl URL: {e}")
        raise typer.Exit(1)

    findings = run_drift_rules(baseline, page)
    triggered = [f for f in findings if f["triggered"]]

    critical_count = sum(1 for f in triggered if f["severity"] == SEVERITY_CRITICAL)
    warning_count = sum(1 for f in triggered if f["severity"] == SEVERITY_WARNING)
    info_count = sum(1 for f in triggered if f["severity"] == SEVERITY_INFO)

    comparison_result = {
        "status": "ok",
        "url": normalize_url(url),
        "baseline_id": baseline["id"],
        "baseline_timestamp": baseline["timestamp"],
        "comparison_timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_rules": len(findings),
            "triggered": len(triggered),
            "critical": critical_count,
            "warning": warning_count,
            "info": info_count,
        },
        "triggered_findings": triggered,
        "current_status_code": page.status_code or 200,
    }

    # Save comparison to database
    try:
        store.save_comparison(comparison_result, baseline["id"])
    except Exception as e:
        typer.echo(f"Warning: Could not save comparison results to database: {e}", err=True)

    if output == "json":
        print(json.dumps(comparison_result, indent=2))
        return

    # Print summary & findings beautifully in terminal
    console.print(f"[bold]SEO Drift Comparison for:[/] {normalize_url(url)}")
    console.print(f"Comparing against baseline ID [cyan]{baseline['id']}[/] captured at {baseline['timestamp']}")
    console.print()

    table = Table(title="Drift Rules Triggered", expand=True)
    table.add_column("Severity", width=12)
    table.add_column("Rule", width=25)
    table.add_column("Description", ratio=3)
    table.add_column("Before", ratio=2)
    table.add_column("After", ratio=2)

    for f in triggered:
        color = SEVERITY_COLORS.get(f["severity"].lower(), "white")
        icon = SEVERITY_ICONS.get(f["severity"].lower(), "")
        table.add_row(
            f"[{color}]{icon} {f['severity']}[/]",
            f["rule"],
            f["message"],
            str(f["old_value"])[:50],
            str(f["new_value"])[:50],
        )

    if triggered:
        console.print(table)
    else:
        console.print("[bold green]✓ No SEO drift detected. Page matches baseline perfectly![/]")

    console.print()
    console.print(Panel(
        f"[bold]Drift Summary:[/]\n"
        f"  • [red]Critical Issues:[/] {critical_count}\n"
        f"  • [yellow]Warnings:[/] {warning_count}\n"
        f"  • [blue]Info Alerts:[/] {info_count}",
        title="[bold]Status",
        border_style="red" if critical_count > 0 else "yellow" if warning_count > 0 else "green",
    ))


@drift_app.command("history")
def drift_history(
    url: Annotated[str, typer.Argument(help="URL to query history for")],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max history entries to list")] = 20,
) -> None:
    """Show historic baselines and comparisons for a URL."""
    store = DriftStore()
    history = store.get_history(url, limit)

    if not history["baselines"]:
        console.print(f"[bold red]Error:[/] No baselines found for {url}. Run 'seo drift baseline <url>' first.")
        raise typer.Exit(1)

    console.print(f"[bold]SEO Drift History for:[/] {history['url']}\n")

    baseline_table = Table(title="Baselines Captured", expand=True)
    baseline_table.add_column("ID", width=6)
    baseline_table.add_column("Timestamp", width=25)
    baseline_table.add_column("Title", ratio=3)
    baseline_table.add_column("H1", ratio=2)
    baseline_table.add_column("Status", width=8)

    for b in history["baselines"]:
        baseline_table.add_row(
            str(b["id"]),
            b["timestamp"],
            b["title"] or "N/A",
            b["h1"] or "N/A",
            str(b["status_code"]),
        )

    console.print(baseline_table)
    console.print()

    comp_table = Table(title="Drift Checks Run", expand=True)
    comp_table.add_column("ID", width=6)
    comp_table.add_column("Baseline ID", width=12)
    comp_table.add_column("Timestamp", width=25)
    comp_table.add_column("Criticals", width=10)
    comp_table.add_column("Warnings", width=10)
    comp_table.add_column("Infos", width=8)

    for c in history["comparisons"]:
        comp_table.add_row(
            str(c["id"]),
            str(c["baseline_id"]),
            c["timestamp"],
            f"[red]{c['critical']}[/]" if c["critical"] > 0 else "0",
            f"[yellow]{c['warning']}[/]" if c["warning"] > 0 else "0",
            f"[blue]{c['info']}[/]" if c["info"] > 0 else "0",
        )

    console.print(comp_table)


@drift_app.command("report")
def drift_report(
    url: Annotated[str, typer.Argument(help="URL to generate report for")],
    output_file: Annotated[Optional[Path], typer.Option("--output", "-o", help="Custom output HTML filepath")] = None,
) -> None:
    """Generate a self-contained HTML report of the latest drift comparison."""
    store = DriftStore()
    baseline = store.load_baseline(url)
    if not baseline:
        console.print(f"[bold red]Error:[/] No baseline found for {url}. Run 'seo drift baseline <url>' first.")
        raise typer.Exit(1)

    typer.echo(f"🕸  Crawling current state of {url}...", err=True)
    try:
        page = asyncio.run(_crawl_and_extract(url))
    except Exception as e:
        console.print(f"[bold red]Error:[/] Could not crawl URL: {e}")
        raise typer.Exit(1)

    findings = run_drift_rules(baseline, page)
    triggered = [f for f in findings if f["triggered"]]

    critical_count = sum(1 for f in triggered if f["severity"] == SEVERITY_CRITICAL)
    warning_count = sum(1 for f in triggered if f["severity"] == SEVERITY_WARNING)
    info_count = sum(1 for f in triggered if f["severity"] == SEVERITY_INFO)

    comparison_result = {
        "status": "ok",
        "url": normalize_url(url),
        "baseline_id": baseline["id"],
        "baseline_timestamp": baseline["timestamp"],
        "comparison_timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_rules": len(findings),
            "triggered": len(triggered),
            "critical": critical_count,
            "warning": warning_count,
            "info": info_count,
        },
        "triggered_findings": triggered,
        "untriggered_findings": [f for f in findings if not f["triggered"]],
        "current_status_code": page.status_code or 200,
    }

    # Generate HTML content using the reference template logic
    from openseo.commands.drift import _generate_html_report_content
    html_content = _generate_html_report_content(comparison_result)

    target_path = output_file or Path("seo-drift-report.html")
    try:
        target_path.write_text(html_content, encoding="utf-8")
        console.print(f"[bold green]✓ Report generated successfully:[/] [cyan]{target_path.resolve()}[/]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] Could not write HTML file: {e}")
        raise typer.Exit(1)


def _generate_html_report_content(comparison: dict) -> str:
    """Generate self-contained HTML using visual palette rules."""
    url = comparison["url"]
    baseline_ts = comparison["baseline_timestamp"]
    compare_ts = comparison["comparison_timestamp"]
    summary = comparison["summary"]
    triggered = comparison["triggered_findings"]
    untriggered = comparison.get("untriggered_findings", [])

    critical = summary["critical"]
    warning = summary["warning"]
    info = summary["info"]

    if critical > 0:
        status_text = "DRIFT DETECTED"
        status_color = "#c53030"
    elif warning > 0:
        status_text = "CHANGES DETECTED"
        status_color = "#d4740e"
    elif info > 0:
        status_text = "MINOR CHANGES"
        status_color = "#1e3a5f"
    else:
        status_text = "NO DRIFT"
        status_color = "#2d6a4f"

    finding_cards = ""
    for finding in triggered:
        sev = finding["severity"]
        color = "#c53030" if sev == SEVERITY_CRITICAL else "#d4740e" if sev == SEVERITY_WARNING else "#1e3a5f"
        bg = "#fef2f2" if sev == SEVERITY_CRITICAL else "#fffbeb" if sev == SEVERITY_WARNING else "#eff6ff"
        
        finding_cards += f"""
        <div class="finding-card" style="border-left: 4px solid {color}; background: {bg};">
            <div class="finding-header">
                <span class="severity-badge" style="background: {color}; color: #ffffff;">{sev}</span>
                <span class="rule-name">{finding['rule']}</span>
            </div>
            <p class="finding-message">{finding['message']}</p>
            <div class="finding-diff">
                <div class="diff-old"><strong>Before:</strong> {finding['old_value']}</div>
                <div class="diff-new"><strong>After:</strong> {finding['new_value']}</div>
            </div>
        </div>
        """

    passed_list = ""
    for finding in untriggered:
        passed_list += f"<li>{finding['rule']}: {finding['message']}</li>\n"

    report_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SEO Drift Report - {url}</title>
    <style>
        body {{ font-family: sans-serif; background: #faf9f7; color: #374151; padding: 2rem; max-width: 900px; margin: 0 auto; }}
        .header {{ text-align: center; padding: 2rem; background: #1e3a5f; color: #ffffff; border-radius: 8px; margin-bottom: 2rem; }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .header .url {{ font-family: monospace; word-break: break-all; opacity: 0.9; }}
        .header .timestamps {{ font-size: 0.85rem; opacity: 0.7; margin-top: 0.5rem; }}
        .status-banner {{ text-align: center; padding: 1rem; border-radius: 8px; font-size: 1.4rem; font-weight: bold; margin-bottom: 2rem; color: #ffffff; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem; }}
        .summary-card {{ text-align: center; padding: 1rem; border-radius: 8px; background: #ffffff; border: 1px solid #e5e7eb; }}
        .summary-card .count {{ font-size: 2rem; font-weight: bold; }}
        .summary-card .label {{ font-size: 0.85rem; color: #6b7280; }}
        .section-title {{ font-size: 1.3rem; color: #1e3a5f; border-bottom: 2px solid #b8860b; padding-bottom: 0.5rem; margin: 2rem 0 1rem; }}
        .finding-card {{ padding: 1rem; border-radius: 6px; margin-bottom: 1rem; }}
        .finding-header {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; }}
        .severity-badge {{ display: inline-block; padding: 0.15rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold; letter-spacing: 0.05em; }}
        .rule-name {{ font-family: monospace; font-size: 0.9rem; color: #6b7280; }}
        .finding-message {{ margin-bottom: 0.75rem; }}
        .finding-diff {{ font-family: monospace; font-size: 0.85rem; background: #ffffff; padding: 0.75rem; border-radius: 4px; border: 1px solid #e5e7eb; }}
        .diff-old {{ color: #c53030; margin-bottom: 0.3rem; }}
        .diff-new {{ color: #2d6a4f; }}
        .passed-section {{ background: #ffffff; padding: 1rem; border-radius: 8px; border: 1px solid #e5e7eb; }}
        .passed-section ul {{ list-style: none; padding: 0; }}
        .passed-section li {{ padding: 0.3rem 0; font-size: 0.9rem; color: #6b7280; }}
        .passed-section li::before {{ content: "\\2713 "; color: #2d6a4f; font-weight: bold; }}
        .footer {{ text-align: center; margin-top: 2rem; padding: 1rem; font-size: 0.8rem; color: #6b7280; border-top: 1px solid #e5e7eb; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SEO Drift Report</h1>
        <div class="url">{url}</div>
        <div class="timestamps">
            Baseline: {baseline_ts} | Compared: {compare_ts}
        </div>
    </div>
    <div class="status-banner" style="background: {status_color};">
        {status_text}
    </div>
    <div class="summary-grid">
        <div class="summary-card">
            <div class="count" style="color: #c53030;">{critical}</div>
            <div class="label">Critical</div>
        </div>
        <div class="summary-card">
            <div class="count" style="color: #d4740e;">{warning}</div>
            <div class="label">Warning</div>
        </div>
        <div class="summary-card">
            <div class="count" style="color: #1e3a5f;">{info}</div>
            <div class="label">Info</div>
        </div>
    </div>
    {f"<h2 class='section-title'>Findings ({len(triggered)} triggered)</h2>" + finding_cards if triggered else ""}
    <h2 class="section-title">Passed Checks ({len(untriggered)})</h2>
    <div class="passed-section">
        <ul>{passed_list}</ul>
    </div>
    <div class="footer">
        Generated by OpenSEO Drift Monitor | {report_time}
    </div>
</body>
</html>
"""


def register(app: typer.Typer) -> None:
    """Register the drift command group."""
    app.add_typer(drift_app)
