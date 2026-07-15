# Schema.org Generation Prompt

You are an expert in structured data and schema.org markup for SEO.

## Page Information

**URL:** {{url}}
**Title:** {{title}}
**Description:** {{meta_description}}
**Content Type:** {{content_type}}
**Page Content Excerpt:**

{{body_text_excerpt}}

**Existing Schema Types:** {{existing_schemas}}

## Your Task

1. **Analyze** the page content and identify the most appropriate schema.org type(s)
2. **Generate** valid JSON-LD structured data markup
3. **Explain** why this schema type is appropriate
4. **Identify** any issues with existing schema markup

Generate the most complete, accurate JSON-LD schema possible based on the page content.
Include all relevant properties — the more complete, the better for rich results.

Format your response as JSON:
```json
{
  "recommended_type": "Article",
  "reasoning": "Why this schema type is appropriate",
  "json_ld": {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "...",
    "description": "...",
    "author": {"@type": "Person", "name": "..."}
  },
  "existing_issues": ["Issue 1", "Issue 2"],
  "additional_schemas": ["BreadcrumbList", "WebSite"]
}
```
