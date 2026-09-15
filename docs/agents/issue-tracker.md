# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`
- **Read an issue**: `gh issue view <number> --comments`, including its labels.
- **List issues**: use `gh issue list` with appropriate state and label filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply or remove labels**: use `gh issue edit`.
- **Close an issue**: `gh issue close <number> --comment "..."`

Infer the repository from `git remote -v`; `gh` does this automatically when run inside this clone.

## Pull requests as a triage surface

**PRs as a request surface: no.**

If this is changed to `yes` later, external pull requests may be treated as requests and processed using the corresponding `gh pr` commands.

GitHub shares one number space across issues and pull requests. A reference such as `#42` may represent either one; try `gh pr view 42` and then fall back to `gh issue view 42`.

## When a skill says “publish to the issue tracker”

Create a GitHub issue in `BelieveTZ/finsight-rag`.

## When a skill says “fetch the relevant ticket”

Run `gh issue view <number> --comments`.

## Wayfinding operations

If the Wayfinder workflow is installed in the future:

- Use one issue labelled `wayfinder:map` as the map.
- Represent work items as child issues where GitHub sub-issues are available.
- Otherwise, link child issues through a task list and a `Part of #<map>` reference.
- Use native GitHub issue dependencies for blocking relationships where available.
- Claim work by assigning the selected issue to the current user.
- Resolve work by adding the result as a comment and closing the issue.
