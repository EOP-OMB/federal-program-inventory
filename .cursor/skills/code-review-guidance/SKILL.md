---
name: code-review-guidance
description: Provides consistent, high-signal code review standards for PR and branch-based reviews, including severity prioritization, issue consolidation, prior-feedback handling, and ignore-path rules.
disable-model-invocation: true
---

# Code Review Guidance

## Use this skill when

- You are reviewing code changes for risk, defects, regressions, or maintainability issues.
- You need consistent review quality across PR-based and git-diff-based workflows.

## Review priorities

Focus findings in this order:

1. correctness, security, and data integrity
2. reliability and performance regressions
3. maintainability issues likely to cause defects

Avoid low-value nits and speculative comments unless they are likely to prevent defects.

## Consolidation rules

- Group related findings into one theme per issue.
- For each theme, include:
  - what is wrong,
  - why it matters (impact/risk),
  - concrete recommendation,
  - the relevant locations in the diff.
- Keep output concise and high-signal.

## Review procedure

1. Identify candidate issues with severity, confidence, and impacted locations.
2. When a prior thread is available, drop candidates that are already addressed or already raised so they do not consume the comment budget.
3. Group the remaining candidates by theme (for example: validation gap, unsafe null handling, missing authorization, N+1 query).
4. Merge each theme into one comment using the consolidation rules above.
5. Keep only the top 5 themes by importance (severity and confidence first, then breadth).
6. Write the summary:
   - If there are new issues, say so and list one bullet per issue, sorted by severity (highest first).
   - If there are no new issues, add no inline comments and state that no new issues were identified.
   - If guardrails blocked the review, do not produce a review.
   - If a previously mentioned issue still looks unaddressed and unacknowledged, mention it as a summary bullet only. Do not add an inline comment for it.

## Prior feedback

When a prior thread is available, use it as context. For a pull request, that thread is the existing issue comments, submitted reviews, and inline review comments. For a local diff, there is no thread unless the user supplies one. Use the thread to avoid duplicate comments, check whether earlier findings were addressed, and spend the comment budget on remaining risk.

## Ignore rules

Exclude these files from analysis and recommendations:

- `website/transformed_data.db`
- Jekyll markdown files under `website/**/*.md`
- Cypress visual regression screenshots under `cypress/cypress-image-diff-screenshots/**`
- Cypress failure screenshots under `cypress/reports/screenshots/**`

## Local diff command

The diff reviewer runs only this command when reviewing the working tree against `dev`. The pull request reviewer does not run it; it reads the pre-fetched diff. The command includes uncommitted edits. Do not substitute `git diff dev...HEAD` unless the user asks for the committed branch range.

```bash
git diff dev -- . ':(exclude)website/transformed_data.db' ':(exclude)website/**/*.md' ':(exclude)cypress/cypress-image-diff-screenshots' ':(exclude)cypress/reports/screenshots'
```

## No-issues behavior

If no actionable issues are found, say so clearly and avoid forcing suggestions.
