# Federal Program Inventory

## About the inventory
The [Federal Program Inventory (FPI)](https://fpi.omb.gov/) is a comprehensive, searchable tool with critical information about all Federal programs that provide grants, loans, or direct payments to individuals, governments, firms or other organizations. The FPI increases government transparency and accessibility and fulfills Congressional mandates to the Office of Management and Budget (OMB) to create and publicly post an inventory.

## About the repository
This repository contains four main sub-directories: (1) [api](api), which contains code for the API that exposes the FPI's elasticsearch instance; (2) [data_processing](data_processing), which contains code for the extract, transform, and load process that gathers and processes the underlying data for the FPI; (3) [indexer](indexer), which contains code to add programs to the FPI's elasticsearch index upon launch; and (4) [website](website), which contains code to build the public-facing FPI website. See the README.md files in each of these directories for more information.

## The build process
The various images that are deployed to run the FPI are generated using Github Actions. The scripts to do so are found in the [.github/workflows](.github/workflows) sub-directory. Github Actions will build three images (website, api, and indexer) upon commit to any of the `[stage]-release` branches. Deployment of these images must then be manually triggered / confirmed on internal systems to deploy the images to the respective environments.

## Subagents
This repository includes two Cursor subagents:

- `.cursor/agents/documentation-updater.md`, which is used to maintain README documentation with minimal, accurate edits.
- `.cursor/agents/pr-reviewer.md`, which is used to review pull request diffs through GitHub CLI and prepare focused review feedback.

### `documentation-updater`

The `documentation-updater` subagent supports two request types:
- `add`: requires `title` and `file` (the target `README.md` file path), adds a new section in a location consistent with existing structure, writes up to roughly 1000 words, and leaves unrelated sections unchanged.
- `update`: accepts optional `id` and `branch` parameters. It inspects `id` with `git show --format=fuller -m <id> -- . ':(exclude)website/**/*.md'`, inspects `branch` with `git diff dev...<branch> -- . ':(exclude)website/**/*.md'`, and otherwise defaults to `git diff dev...HEAD -- . ':(exclude)website/**/*.md'`, then updates only existing README content that is no longer true. It should not add new sections, should usually skip small bug fixes/minor features, and should keep documentation diffs under 1000 words.

For both request types, it should keep edits minimal, match surrounding README tone, ignore Jekyll markdown (`website/**/*.md`) when deciding what to document, and never stage or commit changes.

### `pr-reviewer`

The `pr-reviewer` subagent accepts a required pull request number (`pr`) and reviews the PR diff using GitHub CLI (`gh`) as the authenticated user.

Its review behavior is intentionally constrained:
- consolidate related findings into one comment per theme;
- comment on the five most important pieces of feedback at most;
- prioritize correctness/security/data integrity and reliability concerns over minor style nits.

It also supports draft-first workflows:
- it creates one pending review draft without submitting it;
- if a pending draft already exists for the authenticated user, it asks for confirmation, then replaces that draft to keep a single current review.

To reduce sandbox-related prompting, you may want to allowlist the gh command by doing the following:
- Go to Cursor Settings > Agents > Auto-Run > Command Allowlist.Add gh to the allowed command array so Cursor doesn't aggressively block the binary invocation.

Subagents are expected to avoid staging or committing changes unless explicitly asked.
