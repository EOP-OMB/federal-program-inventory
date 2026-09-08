---
name: github-pr-review-api
description: Standardizes GitHub PR review API usage with gh CLI, including enterprise hostname handling, pending review replacement, JSON payload creation, and inline comment verification. Use when creating, replacing, or validating PR draft reviews and inline comments.
disable-model-invocation: true
---

# GitHub PR Review API

## Use this skill when

- You need to create or replace a pending PR review.
- You need to attach inline comments reliably in the first create call.
- You are working against GitHub Enterprise where default host selection can cause 404 errors.

## Required workflow

1. Run commands outside the sandbox.
2. Resolve target host and repo first.
3. Gather PR context and head SHA.
4. Remove existing authenticated-user pending reviews.
5. Build one JSON payload file containing `body`, `commit_id`, and `comments`.
6. Create one pending review via `gh api ... -X POST --input`.
7. Verify attached inline comments on the created review.
8. If verification count is wrong, delete and recreate once with corrected payload.

## Host and repo resolution

- Always run `gh auth status` and identify the correct host for the target repository.
- For enterprise repos, always pass `--hostname <host>` on `gh api` calls.
- Resolve owner/repo via `gh repo view --json owner,name`.

## Review creation payload

Build JSON payload with this shape:

```json
{
  "body": "review summary",
  "commit_id": "<pr_head_sha>",
  "comments": [
    {
      "path": "README.md",
      "position": 9,
      "body": "inline review comment"
    }
  ]
}
```

Rules:

- Include `commit_id` from PR head SHA.
- Prefer `comments[].position` from diff context over `line`/`side`.
- Keep comments consolidated and high-signal.
- Exclude markdown files under `website/` from review comments (for example: `website/**/*.md`).

## Position sourcing

- Retrieve diff anchors with `GET /repos/<owner>/<repo>/pulls/<pr>/files`.
- Use the `patch` hunks to compute or confirm valid `position`.
- If unsure about line-based anchors, use `position`.

## Canonical commands

Resolve PR context:

```bash
gh pr view <pr> --json number,url,headRefName,baseRefName,headRefOid
```

Fetch diff context:

```bash
gh pr diff <pr> --patch
```

Fetch diff context while excluding website markdown files:

```bash
gh pr diff <pr> --patch | awk '
  /^diff --git / {
    path = $4
    sub("^b/", "", path)
    skip = (path ~ /^website\/.*\.md$/)
  }
  !skip { print }
'
```

List pending reviews:

```bash
gh api --hostname <host> repos/<owner>/<repo>/pulls/<pr>/reviews
```

Delete pending review:

```bash
gh api --hostname <host> repos/<owner>/<repo>/pulls/<pr>/reviews/<review_id> -X DELETE
```

Create pending review from JSON payload:

```bash
gh api --hostname <host> repos/<owner>/<repo>/pulls/<pr>/reviews -X POST --input /tmp/review.json
```

Verify created inline comments:

```bash
gh api --hostname <host> repos/<owner>/<repo>/pulls/<pr>/reviews/<review_id>/comments
```

## Verification requirements

- Verify review state is `PENDING`.
- Verify inline comment count equals intended consolidated comment count.
- If mismatch: recreate once, then report the final count and review ID.

## Output checklist

- PR URL and number.
- Hostname used.
- Pending review ID.
- Consolidated comment count requested vs attached.
- Confirmation the review remains `PENDING`.
