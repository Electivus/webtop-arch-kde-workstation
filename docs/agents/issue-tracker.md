# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues in `Electivus/webtop-arch-kde-workstation`. Use the `gh` CLI with this configured target explicitly on every operation.

## Conventions

- **Create an issue**: `gh issue create --repo Electivus/webtop-arch-kde-workstation --title "..." --body-file <body-file>`.
- **Read an issue**: `gh issue view <number> --repo Electivus/webtop-arch-kde-workstation --json number,title,body,labels,comments,url,state`. Filter the returned JSON as needed; `--comments` is available for a plain-text view.
- **List issues**: `gh issue list --repo Electivus/webtop-arch-kde-workstation --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`. Add the appropriate `--label`, `--state`, and `--limit` filters.
- **Comment on an issue**: `gh issue comment <number> --repo Electivus/webtop-arch-kde-workstation --body-file <body-file>`.
- **Apply a label**: `gh issue edit <number> --repo Electivus/webtop-arch-kde-workstation --add-label "..."`.
- **Remove a label**: `gh issue edit <number> --repo Electivus/webtop-arch-kde-workstation --remove-label "..."`.
- **Close**: `gh issue close <number> --repo Electivus/webtop-arch-kde-workstation`. Publish any required explanation with the comment operation first.

For multiline bodies, write the exact Markdown to a UTF-8 file and pass `--body-file`; preserve real newlines and literal characters. Replace example arguments such as `<number>` and `<body-file>` with actual values before execution.

This file is the source of the configured repository target. Keep `--repo Electivus/webtop-arch-kde-workstation` on every issue or PR command and `repos/Electivus/webtop-arch-kde-workstation/` at the start of every REST API path. Never infer the target from Git remotes, the checkout, or the current `gh` context.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When enabled, PRs use the same labels and states as issues:

- **Read a PR**: `gh pr view <number> --repo Electivus/webtop-arch-kde-workstation --comments` and `gh pr diff <number> --repo Electivus/webtop-arch-kde-workstation`.
- **List external PRs for triage**: `gh api --method GET repos/Electivus/webtop-arch-kde-workstation/pulls --paginate -f state=open -f per_page=100 --jq '.[] | select(.author_association == "CONTRIBUTOR" or .author_association == "FIRST_TIME_CONTRIBUTOR" or .author_association == "NONE") | {number, title, body, labels, author: .user.login, author_association}'`. Fetch comments for selected PRs with the read operation above. The REST field is `author_association`; the CLI's PR JSON output does not expose `authorAssociation`.
- **Comment**: `gh pr comment <number> --repo Electivus/webtop-arch-kde-workstation --body-file <body-file>`.
- **Apply a label**: `gh pr edit <number> --repo Electivus/webtop-arch-kde-workstation --add-label "..."`.
- **Remove a label**: `gh pr edit <number> --repo Electivus/webtop-arch-kde-workstation --remove-label "..."`.
- **Close**: `gh pr close <number> --repo Electivus/webtop-arch-kde-workstation`.

GitHub shares a number space across issues and PRs. Resolve an ambiguous `#42` with `gh pr view 42 --repo Electivus/webtop-arch-kde-workstation`, falling back to `gh issue view 42 --repo Electivus/webtop-arch-kde-workstation` when it is an issue.

## When a skill says "publish to the issue tracker"

Create a GitHub issue using the configured target and the create operation above.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --repo Electivus/webtop-arch-kde-workstation --comments` and retrieve labels with the structured read operation when needed.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. Create it with `gh issue create --repo Electivus/webtop-arch-kde-workstation --label wayfinder:map --title "..." --body-file <body-file>`.
- **Child ticket**: create an issue and link it as a GitHub sub-issue with `gh api --method POST repos/Electivus/webtop-arch-kde-workstation/issues/<map>/sub_issues -F sub_issue_id=<child-db-id>`. Where sub-issues are unavailable, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. Use `wayfinder:<type>` labels (`research`, `prototype`, `grilling`, or `task`).
- **Blocking**: use GitHub's native issue dependencies. Add an edge with `gh api --method POST repos/Electivus/webtop-arch-kde-workstation/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`. Resolve the blocker's numeric database ID with `gh api repos/Electivus/webtop-arch-kde-workstation/issues/<number> --jq .id`; it is distinct from the issue number or `node_id`. Where dependencies are unavailable, put a `Blocked by: #<number>, #<number>` line at the top of the child body.
- **Frontier query**: list the map's open children with `gh issue list --repo Electivus/webtop-arch-kde-workstation --state open`, scoped to the map's sub-issues or task list. Exclude assigned tickets and tickets with open blockers (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the fallback `Blocked by` line). First in map order wins.
- **Claim**: `gh issue edit <number> --repo Electivus/webtop-arch-kde-workstation --add-assignee @me`, the session's first write.
- **Resolve**: `gh issue comment <number> --repo Electivus/webtop-arch-kde-workstation --body-file <body-file>`, then `gh issue close <number> --repo Electivus/webtop-arch-kde-workstation`. Append a context pointer (gist and link) to the map's Decisions-so-far.
