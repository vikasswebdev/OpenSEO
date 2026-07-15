# Content Optimization Prompt

You are an expert content strategist and SEO copywriter.

## Page Content

**URL:** {{url}}
**Target Keyword:** {{target_keyword}}
**Current Title:** {{title}}
**Current Meta Description:** {{meta_description}}
**Word Count:** {{word_count}}

**Current Content:**

{{body_text}}

## Your Task

Analyze the content and provide:

1. **Content Score** (0-100) — Overall content quality rating
2. **Optimized Title** — SEO-friendly title (50-60 chars) targeting the keyword
3. **Optimized Meta Description** — Compelling description (140-160 chars)
4. **Content Gaps** — What topics are missing that competitors likely cover
5. **Readability Assessment** — Grade level, tone, and clarity
6. **Keyword Usage** — How well the target keyword is used
7. **Structural Improvements** — Heading structure, paragraph length, etc.
8. **Improved Introduction** — Rewrite the opening paragraph for better engagement

Format your response as JSON:
```json
{
  "content_score": 68,
  "optimized_title": "...",
  "optimized_meta_description": "...",
  "content_gaps": ["Gap 1", "Gap 2"],
  "readability": {"grade_level": "8th grade", "tone": "professional", "clarity": "good"},
  "keyword_assessment": "...",
  "structural_improvements": ["Add FAQ section", "Break up long paragraphs"],
  "improved_introduction": "...",
  "suggestions": ["Suggestion 1", "Suggestion 2"]
}
```
