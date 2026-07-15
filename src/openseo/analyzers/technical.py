"""
Deterministic technical SEO analyzers.

Analyzes security headers, HTTPS consistency, mobile viewports, favicons,
robots.txt/sitemap presence, redirects, and site-wide metadata duplication.
"""

from __future__ import annotations

from urllib.parse import urlparse
from openseo.models.page import Page
from openseo.models.issue import Issue, Severity, Category


def analyze_page_technical(page: Page) -> tuple[list[Issue], float]:
    """
    Run deterministic page-level technical checks.

    Returns list of Issues and a score from 0 to 100.
    """
    issues: list[Issue] = []
    score = 100.0

    # ── HTTPS & Mixed Content Check ──────────────────────────────────────────
    is_https = page.url.lower().startswith("https://")
    if not is_https:
        issues.append(
            Issue(
                id="insecure_connection",
                title="Page Not Using HTTPS",
                description="The page is served over insecure HTTP connection.",
                severity=Severity.CRITICAL,
                category=Category.TECHNICAL,
                recommendation="Install an SSL certificate and redirect all HTTP traffic to HTTPS.",
            )
        )
        score -= 20
    else:
        # Check mixed content (http assets on https page)
        http_assets = []
        for img in page.images:
            if img.src.lower().startswith("http://"):
                http_assets.append(img.src)
        for link in page.links:
            if link.href.lower().startswith("http://") and not link.is_external:
                http_assets.append(link.href)

        if http_assets:
            issues.append(
                Issue(
                    id="mixed_content",
                    title="Mixed Content Detected",
                    description=f"Page is loaded over HTTPS, but references {len(http_assets)} insecure HTTP resources.",
                    severity=Severity.WARNING,
                    category=Category.TECHNICAL,
                    element=", ".join(http_assets[:3]),
                    recommendation="Ensure all referenced images, styles, and scripts use HTTPS URLs.",
                )
            )
            score -= 10

    # ── Redirects / Status Codes ─────────────────────────────────────────────
    status = page.status_code
    if status and status >= 400:
        issues.append(
            Issue(
                id="broken_page",
                title="Broken Page Status Code",
                description=f"The page returned an error status code: {status}",
                severity=Severity.CRITICAL,
                category=Category.TECHNICAL,
                recommendation="Investigate server logs or routing issues causing this HTTP error code.",
            )
        )
        score -= 40
    elif page.final_url and page.final_url != page.url:
        issues.append(
            Issue(
                id="page_redirected",
                title="Page Redirected",
                description=f"URL redirected to: {page.final_url}",
                severity=Severity.INFO,
                category=Category.TECHNICAL,
            )
        )

    # ── Viewport Check ───────────────────────────────────────────────────────
    if not page.viewport:
        issues.append(
            Issue(
                id="viewport_missing",
                title="Missing Viewport Tag",
                description="No mobile viewport tag was found. Mobile users might see scaled down desktop layout.",
                severity=Severity.WARNING,
                category=Category.MOBILE,
                recommendation="Add <meta name='viewport' content='width=device-width, initial-scale=1.0'> to the HTML head.",
            )
        )
        score -= 15

    # ── Charset & Lang Checks ────────────────────────────────────────────────
    if not page.charset:
        issues.append(
            Issue(
                id="charset_missing",
                title="Missing Charset Declaration",
                description="The page HTML does not specify a character encoding charset.",
                severity=Severity.INFO,
                category=Category.TECHNICAL,
                recommendation="Add <meta charset='UTF-8'> at the top of the HTML <head>.",
            )
        )
        score -= 5

    if not page.lang:
        issues.append(
            Issue(
                id="lang_missing",
                title="Missing HTML Lang Attribute",
                description="The <html> element is missing a lang attribute, affecting screen readers.",
                severity=Severity.WARNING,
                category=Category.ACCESSIBILITY,
                recommendation="Add a descriptive lang attribute to the <html> tag, e.g. <html lang='en'>.",
            )
        )
        score -= 10

    # ── Robots Meta check ────────────────────────────────────────────────────
    if page.robots_meta:
        robots_lower = page.robots_meta.lower()
        if "noindex" in robots_lower:
            issues.append(
                Issue(
                    id="noindex_active",
                    title="Page Has noindex Tag Active",
                    description="This page is explicitly configured not to be indexed by search engines.",
                    severity=Severity.WARNING,
                    category=Category.TECHNICAL,
                    element=page.robots_meta,
                    recommendation="Remove 'noindex' from the robots meta tag if you want this page to rank.",
                )
            )
            score -= 15
        if "nofollow" in robots_lower:
            issues.append(
                Issue(
                    id="nofollow_active",
                    title="Page Has nofollow Tag Active",
                    description="Search engines are instructed not to follow links on this page.",
                    severity=Severity.INFO,
                    category=Category.TECHNICAL,
                    element=page.robots_meta,
                    recommendation="Remove 'nofollow' from robots meta tag to allow PageRank flow.",
                )
            )

    return issues, max(0.0, score)


def analyze_site_technical(
    pages: dict[str, Page],
    sitemap_discovered_urls: set[str] | list[str] | None = None
) -> tuple[list[Issue], float]:
    """
    Run site-level deterministic checks on a collection of crawled pages.

    Analyzes trailing slash consistency, metadata duplicates across all pages,
    WWW consistency, sitemap, and robots.txt.
    """
    issues: list[Issue] = []
    score = 100.0

    if not pages:
        return issues, 100.0

    # ── Sitemap Coverage Check ───────────────────────────────────────────────
    if sitemap_discovered_urls:
        sitemap_set = {u.lower() for u in sitemap_discovered_urls}
        missing_pages = []
        for url in pages:
            if url.lower() not in sitemap_set:
                missing_pages.append(url)
        if missing_pages:
            element_str = ", ".join(missing_pages[:3])
            issues.append(
                Issue(
                    id="missing_from_sitemap",
                    title=f"Pages Missing From sitemap.xml ({len(missing_pages)} pages)",
                    description="These pages are crawled but were not found in the XML sitemap.",
                    severity=Severity.WARNING,
                    category=Category.TECHNICAL,
                    element=element_str,
                    recommendation="Add these URLs to your sitemap.xml file so search engines discover them easily.",
                )
            )
            score -= 10

    # ── Robots.txt & Sitemap Presence Checks ─────────────────────────────────
    first_page = list(pages.values())[0]
    if not first_page.robots_txt:
        issues.append(
            Issue(
                id="site_missing_robots",
                title="Missing robots.txt",
                description="No robots.txt was detected on the site root.",
                severity=Severity.WARNING,
                category=Category.TECHNICAL,
                recommendation="Create a robots.txt file at the root directory of your site.",
            )
        )
        score -= 15

    if not first_page.sitemap_urls:
        issues.append(
            Issue(
                id="site_missing_sitemap",
                title="Missing XML Sitemap",
                description="No XML sitemap was declared or discovered in robots.txt or site root.",
                severity=Severity.WARNING,
                category=Category.TECHNICAL,
                recommendation="Create an XML sitemap and reference it inside robots.txt.",
            )
        )
        score -= 15

    # ── Trailing Slash Consistency ───────────────────────────────────────────
    has_slash = 0
    no_slash = 0
    for url in pages:
        parsed = urlparse(url)
        path = parsed.path
        if path and path != "/":
            if path.endswith("/"):
                has_slash += 1
            else:
                no_slash += 1

    if has_slash > 0 and no_slash > 0:
        issues.append(
            Issue(
                id="inconsistent_trailing_slash",
                title="Inconsistent Trailing Slashes",
                description=f"Urls are inconsistent. Found {has_slash} with slash and {no_slash} without.",
                severity=Severity.WARNING,
                category=Category.TECHNICAL,
                recommendation="Enforce trailing slash consistency site-wide via server redirects (e.g. always use or omit them).",
            )
        )
        score -= 10

    # ── WWW vs non-WWW Consistency ───────────────────────────────────────────
    www_hosts = 0
    non_www_hosts = 0
    for url in pages:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            www_hosts += 1
        else:
            non_www_hosts += 1

    if www_hosts > 0 and non_www_hosts > 0:
        issues.append(
            Issue(
                id="inconsistent_www_host",
                title="Inconsistent Host Prefixes (WWW vs non-WWW)",
                description=f"Found {www_hosts} pages with www. prefix and {non_www_hosts} pages without.",
                severity=Severity.WARNING,
                category=Category.TECHNICAL,
                recommendation="Redirect all traffic to a single preferred domain format (either with or without WWW).",
            )
        )
        score -= 10

    # ── Duplicate Title / Meta Description Site-wide ────────────────────────
    titles_map: dict[str, list[str]] = {}
    metas_map: dict[str, list[str]] = {}

    for url, page in pages.items():
        if page.title:
            titles_map.setdefault(page.title, []).append(url)
        if page.meta_description:
            metas_map.setdefault(page.meta_description, []).append(url)

    dup_titles = {t: urls for t, urls in titles_map.items() if len(urls) > 1}
    dup_metas = {m: urls for m, urls in metas_map.items() if len(urls) > 1}

    if dup_titles:
        element_str = "; ".join(f"'{title}' on {len(urls)} pages" for title, urls in list(dup_titles.items())[:3])
        issues.append(
            Issue(
                id="site_duplicate_titles",
                title=f"Duplicate Title Tags Found ({len(dup_titles)} clusters)",
                description="Multiple pages share the exact same title tag, which confuses search engines.",
                severity=Severity.CRITICAL,
                category=Category.TITLE,
                element=element_str,
                recommendation="Ensure every indexable page has a unique, descriptive <title> tag.",
            )
        )
        score -= 15

    if dup_metas:
        element_str = "; ".join(f"'{desc[:30]}...' on {len(urls)} pages" for desc, urls in list(dup_metas.items())[:3])
        issues.append(
            Issue(
                id="site_duplicate_meta_descriptions",
                title=f"Duplicate Meta Descriptions ({len(dup_metas)} clusters)",
                description="Multiple pages share the exact same meta description tag.",
                severity=Severity.WARNING,
                category=Category.META,
                element=element_str,
                recommendation="Write unique, descriptive meta descriptions for each page.",
            )
        )
        score -= 10

    return issues, max(0.0, score)
