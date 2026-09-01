# Issue tracker: GitHub

Issues and specs for this repository live in GitHub Issues. Use the `gh` CLI for issue operations.

## Conventions

- Create an issue with `gh issue create`.
- Read an issue and its comments with `gh issue view <number> --comments`.
- List issues with `gh issue list`, narrowing by state or label as needed.
- Add comments with `gh issue comment <number>`.
- Apply or remove labels with `gh issue edit <number> --add-label` or `--remove-label`.
- Close an issue with `gh issue close <number>`.

Infer the repository from this checkout's GitHub remote; `gh` does this automatically.

## Pull requests as a triage surface

PRs as a request surface: **no**.

## Skill conventions

When a skill says to publish to the issue tracker, create a GitHub issue. When it says to fetch a ticket, use `gh issue view <number> --comments`.
