# SEO Audit Prompt

You are an expert SEO analyst with deep knowledge of technical SEO, on-page optimization, and content strategy.

Analyze the following page data for the URL: **{{url}}**

## Page Data

**Title:** {{title}}
**Meta Description:** {{meta_description}}
**Canonical URL:** {{canonical}}
**H1 Tags:** {{h1_tags}}
**Word Count:** {{word_count}}
**Images without alt text:** {{images_without_alt}}
**Internal links:** {{internal_links_count}}
**External links:** {{external_links_count}}
**Schema.org types detected:** {{schema_types}}
**Open Graph present:** {{has_open_graph}}
**Page load time (ms):** {{response_time_ms}}
**Robots meta:** {{robots_meta}}

## Body Text Excerpt

{{body_text_excerpt}}

## Your Task

Provide a comprehensive SEO audit with:

1. **Critical Issues** — Problems that directly hurt rankings (must fix immediately)
2. **Warnings** — Issues that should be addressed soon
3. **Recommendations** — Actionable improvements with expected impact
4. **Quick Wins** — Easy, high-impact changes that can be done immediately
5. **Content Analysis** — Quality, depth, and relevance assessment

Format your response as JSON with this exact structure:
```json
{
  "summary": "One paragraph executive summary",
  "overall_score": 72,
  "critical_issues": [
    {"title": "...", "description": "...", "recommendation": "..."}
  ],
  "warnings": [
    {"title": "...", "description": "...", "recommendation": "..."}
  ],
  "recommendations": [
    {"title": "...", "body": "...", "priority": 1, "effort": "low", "impact": "high"}
  ],
  "content_assessment": "..."
}
```

Be specific, actionable, and data-driven. Reference the actual page data provided.
