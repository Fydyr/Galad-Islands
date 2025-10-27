# Contributing

Thank you for your interest in contributing to Galad-Islands. This document describes how to report issues, request features and submit code changes in a clear and efficient way. It is inspired by the project's developer documentation.

---

## Table of contents

- Code of Conduct
- Quick start
- Commit conventions
- Branch naming & workflow
- Pull requests
- Tests & CI
- Code style & standards
- Review process
- Security
- Reporting issues & feature requests
- Maintainers & contact

---

## Code of Conduct

Be respectful, inclusive and professional. Harassment, hate speech or abusive behaviour will not be tolerated. If you experience or witness unacceptable behaviour, open an issue or contact a maintainer.

---

## Quick start

1. Fork the repository on GitHub.
2. Clone your fork:
   ```
   git clone https://github.com/<your-user>/Galad-Islands.git
   cd Galad-Islands
   ```
3. Add upstream remote:
   ```
   git remote add upstream https://github.com/Fydyr/Galad-Islands.git
   git fetch upstream
   ```

---

## Commit conventions

We follow Conventional Commits 1.0.0 to keep history readable and machine-usable.

Format:
```
type(scope): short subject

optional body

optional footer
```

- type: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
- subject: imperative, lower-case start, max 72 chars, no trailing period
- body: explain why and what (wrap ~100 chars)
- footer: references (e.g. `Closes: #123`) or `BREAKING CHANGE: ...`

Example:
```
feat(menu): add gamemode selection modal

Adds a modal to choose player vs AI and AI vs AI modes.
Closes: #156
```

---

## Branch naming & workflow

Branch name pattern:
```
<type>/<issue-number>-short-description
```
Examples:
- feat/123-gamemode-modal
- fix/45-resize-crash
- docs/77-api

Typical workflow:
1. Sync main:
   ```
   git checkout main
   git fetch upstream
   git merge upstream/main
   ```
2. Create branch:
   ```
   git checkout -b feat/123-description
   ```
3. Work locally, add tests.
4. Rebase before pushing:
   ```
   git fetch upstream
   git rebase upstream/main
   ```
   Resolve conflicts and continue rebase.
5. Push:
   ```
   git push -u origin <branch-name>
   ```
   If you rebased:
   ```
   git push --force-with-lease
   ```

---

## Pull requests

- Target branch: `main` (unless PR template specifies otherwise).
- Fill the PR description: summary, motivation, type of change, linked issues, screenshots/logs if relevant.
- Keep PRs focused and small when possible.
- Link related issues using `Closes:` or `Refs:` in commit messages or PR description.
- Respond to review comments and update the branch.

PR checks (CI) must pass before merge. Maintainers may require squash or rebase merges.

---

## Tests & CI

- Add or update tests for functional changes.
- Run tests locally:
  ```
  pytest
  ```
- CI runs tests, linters and formatters. Do not merge failing checks.
- Target coverage: minimum 80%, goal 90%+.

---

## Code style & standards

General:
- Follow existing patterns in the codebase.
- Keep functions short and focused.
- Write clear, self-explanatory names.
- Avoid duplication (DRY).
- Handle errors explicitly; don't silently swallow exceptions.

Python conventions:
- snake_case for functions and variables
- PascalCase for classes
- UPPER_SNAKE_CASE for constants
- File names in snake_case

Recommended tooling:
- black
- flake8
- isort

Example formatting check:
```
black --check .
flake8
```

---

## Review process

Acceptance criteria (minimum):
- At least one maintainer approval
- CI checks passing
- No merge conflicts
- Tests added/updated when applicable
- Documentation updated if behavior or public API changed

Handling feedback:
- Apply requested changes, add a short explanation in PR comments, and request re-review.

---

## Security

- Do not commit secrets (API keys, passwords, tokens).
- Use environment variables or secret managers.
- For security vulnerabilities, prefer private communication with maintainers (create a private issue or contact a maintainer directly when possible).

---

## Reporting issues & feature requests

When opening an issue include:
- Clear title
- Steps to reproduce
- Expected vs actual behaviour
- Environment (OS, Python version, branch/commit)
- Logs or screenshots when relevant

Search existing issues before creating a new one.

---

## Maintainers & contact

Maintainers:
- Enzo Fournier
- Edouard Alluin
- Julien Behani
- Ethan Cailliau
- Alexandre Damman
- Romain Lambert

For general questions, open an issue labeled `question` or use Discussions if enabled.

---

## Thank you

Contributions are welcome and appreciated. If unsure where to start, look for issues labeled `good first issue` or open a short discussion describing what you'd like to do.
...existing code...
```// filepath: d:\IUT\2025-2026\SAE\sae1\Galad-Islands\CONTRIBUTING.md
...existing code...
# Contributing

Thank you for your interest in contributing to Galad-Islands. This document describes how to report issues, request features and submit code changes in a clear and efficient way. It is inspired by the project's developer documentation.

---

## Table of contents

- Code of Conduct
- Quick start
- Commit conventions
- Branch naming & workflow
- Pull requests
- Tests & CI
- Code style & standards
- Review process
- Security
- Reporting issues & feature requests
- Maintainers & contact

---

## Code of Conduct

Be respectful, inclusive and professional. Harassment, hate speech or abusive behaviour will not be tolerated. If you experience or witness unacceptable behaviour, open an issue or contact a maintainer.

---

## Quick start

1. Fork the repository on GitHub.
2. Clone your fork:
   ```
   git clone https://github.com/<your-user>/Galad-Islands.git
   cd Galad-Islands
   ```
3. Add upstream remote:
   ```
   git remote add upstream https://github.com/Fydyr/Galad-Islands.git
   git fetch upstream
   ```

---

## Commit conventions

We follow Conventional Commits 1.0.0 to keep history readable and machine-usable.

Format:
```
type(scope): short subject

optional body

optional footer
```

- type: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
- subject: imperative, lower-case start, max 72 chars, no trailing period
- body: explain why and what (wrap ~100 chars)
- footer: references (e.g. `Closes: #123`) or `BREAKING CHANGE: ...`

Example:
```
feat(menu): add gamemode selection modal

Adds a modal to choose player vs AI and AI vs AI modes.
Closes: #156
```

---

## Branch naming & workflow

Branch name pattern:
```
<type>/<issue-number>-short-description
```
Examples:
- feat/123-gamemode-modal
- fix/45-resize-crash
- docs/77-api

Typical workflow:
1. Sync main:
   ```
   git checkout main
   git fetch upstream
   git merge upstream/main
   ```
2. Create branch:
   ```
   git checkout -b feat/123-description
   ```
3. Work locally, add tests.
4. Rebase before pushing:
   ```
   git fetch upstream
   git rebase upstream/main
   ```
   Resolve conflicts and continue rebase.
5. Push:
   ```
   git push -u origin <branch-name>
   ```
   If you rebased:
   ```
   git push --force-with-lease
   ```

---

## Pull requests

- Target branch: `main` (unless PR template specifies otherwise).
- Fill the PR description: summary, motivation, type of change, linked issues, screenshots/logs if relevant.
- Keep PRs focused and small when possible.
- Link related issues using `Closes:` or `Refs:` in commit messages or PR description.
- Respond to review comments and update the branch.

PR checks (CI) must pass before merge. Maintainers may require squash or rebase merges.

---

## Tests & CI

- Add or update tests for functional changes.
- Run tests locally:
  ```
  pytest
  ```
- CI runs tests, linters and formatters. Do not merge failing checks.
- Target coverage: minimum 80%, goal 90%+.

---

## Code style & standards

General:
- Follow existing patterns in the codebase.
- Keep functions short and focused.
- Write clear, self-explanatory names.
- Avoid duplication (DRY).
- Handle errors explicitly; don't silently swallow exceptions.

Python conventions:
- snake_case for functions and variables
- PascalCase for classes
- UPPER_SNAKE_CASE for constants
- File names in snake_case

Recommended tooling:
- black
- flake8
- isort

Example formatting check:
```
black --check .
flake8
```

---

## Review process

Acceptance criteria (minimum):
- At least one maintainer approval
- CI checks passing
- No merge conflicts
- Tests added/updated when applicable
- Documentation updated if behavior or public API changed

Handling feedback:
- Apply requested changes, add a short explanation in PR comments, and request re-review.

---

## Security

- Do not commit secrets (API keys, passwords, tokens).
- Use environment variables or secret managers.
- For security vulnerabilities, prefer private communication with maintainers (create a private issue or contact a maintainer directly when possible).

---

## Reporting issues & feature requests

When opening an issue include:
- Clear title
- Steps to reproduce
- Expected vs actual behaviour
- Environment (OS, Python version, branch/commit)
- Logs or screenshots when relevant

Search existing issues before creating a new one.

---

## Maintainers & contact

Maintainers:
- Enzo Fournier
- Edouard Alluin
- Julien Behani
- Ethan Cailliau
- Alexandre Damman
- Romain Lambert

For general questions, open an issue labeled `question` or use Discussions if enabled.

---

## Thank you

Contributions are welcome and appreciated. If unsure where to start, look for issues labeled `good first issue` or open a short discussion describing what you'd like to do.