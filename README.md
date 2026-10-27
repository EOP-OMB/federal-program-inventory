# Federal Program Inventory

## About the inventory
The [Federal Program Inventory (FPI)](https://fpi.omb.gov/) is a comprehensive, searchable tool with critical information about all Federal programs that provide grants, loans, or direct payments to individuals, governments, firms or other organizations. The FPI increases government transparency and accessibility and fulfills Congressional mandates to the Office of Management and Budget (OMB) to create and publicly post an inventory.

## About the repository
This repository contains four main sub-directories: (1) [api](api), which contains code for the API that exposes the FPI's elasticsearch instance; (2) [data_processing](data_processing), which contains code for the extract, transform, and load process that gathers and processes the underlying data for the FPI; (3) [indexer](indexer), which contains code to add programs to the FPI's elasticsearch index upon launch; and (4) [website](website), which contains code to build the public-facing FPI website. See the README.md files in each of these directories for more information.

## Subagents
This repository includes Cursor subagents:

- `.cursor/agents/documentation-updater.md`, which is used to maintain README documentation with minimal, accurate edits.
- `.cursor/agents/diff-reviewer.md`, which reviews the working tree against `dev` and prints findings in chat.
- `.cursor/agents/pr-reviewer.md`, which GitHub Actions uses to write a focused review payload from pre-fetched context. It is not a local chat reviewer.

### `documentation-updater`

The `documentation-updater` subagent supports two request types:
- `add`: requires `title` and `file` (the target `README.md` file path), adds a new section in a location consistent with existing structure, writes up to roughly 1000 words, and leaves unrelated sections unchanged.
- `update`: accepts optional `id` and `branch` parameters. It inspects `id` with `git show --format=fuller -m <id> -- . ':(exclude)website/**/*.md' website/TESTS.md website/README.md`, inspects `branch` with `git diff dev...<branch> -- . ':(exclude)website/**/*.md' website/TESTS.md website/README.md`, and otherwise defaults to `git diff dev...HEAD -- . ':(exclude)website/**/*.md' website/TESTS.md website/README.md`, then updates only existing README content that is no longer true. It should not add new sections, should usually skip small bug fixes/minor features, and should keep documentation diffs under 1000 words.

For both request types, it should keep edits minimal, match surrounding README tone, ignore Jekyll markdown (`website/**/*.md`) when deciding what to document except `website/TESTS.md` and `website/README.md`, and never stage or commit changes.

### `diff-reviewer`

The `diff-reviewer` subagent reviews the working tree against `dev` and prints up to five consolidated findings in chat. It runs the local diff command in `.cursor/skills/code-review-guidance/SKILL.md`. It does not call GitHub, write a review payload, or edit files. Use it when a pull-request review needs to be done locally, including when Cursor policy blocks the automated review.

### `pr-reviewer`

The `pr-reviewer` subagent is Actions/payload-only. GitHub Actions passes a pull request number (`pr`) and `mode=json`. The agent reads pre-fetched context files, uses existing issue comments, submitted reviews, and inline review comments so new comments stay focused on remaining issues, and writes one review payload. It does not fetch the pull request, run shell commands, or post the review. A later workflow step submits that payload. For a local review, use `diff-reviewer`.

Its review behavior is intentionally constrained:
- consolidate related findings into one comment per theme;
- comment on the five most important pieces of feedback at most;
- prioritize correctness/security/data integrity and reliability concerns over minor style nits.

Subagents are expected to avoid staging or committing changes unless explicitly asked.
