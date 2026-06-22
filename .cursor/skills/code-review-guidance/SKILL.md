---
name: code-review-guidance
description: Provides consistent, high-signal code review standards for PR and branch-based reviews, including severity prioritization, issue consolidation, and ignore-path rules.
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
  - concrete recommendation.
- Keep output concise and high-signal.

## Ignore rules

Exclude these files from analysis and recommendations:

- `data_processing/transformed/transformed_data.db`
- Jekyll markdown files under `website/**/*.md`

## No-issues behavior

If no actionable issues are found, say so clearly and avoid forcing suggestions.
