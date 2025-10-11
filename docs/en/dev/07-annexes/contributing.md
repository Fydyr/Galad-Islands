---
i18n:
  en: "Contribution Guide"
  fr: "Guide de contribution"
---

# Contribution Guide

## Commit Conventions

The project uses the Conventional Commits 1.0.0 specification to ensure a readable and machine-exploitable commit history.

### Commit Message Structure

```text
<type>(<scope>): <subject>

<body>

<footer>
```

**Mandatory Components:**

- `type`: type of change
- `subject`: Short description (max 72 characters)

**Optional Components:**

- `scope`: Scope of the change (component, module, file)
- `body`: Detailed description of the change
- `footer`: Metadata (issue references, breaking changes)

### Commit Types

| Type | Description | Versioning Impact |
|------|-------------|----------------------|
| `feat` | Adds a new feature | MINOR |
| `fix` | Fixes a bug | PATCH |
| `docs` | Documentation changes only | - |
| `style` | Changes not affecting logic (formatting, spaces, indentation) | - |
| `refactor` | Refactoring without changing functionality | - |
| `perf` | Performance improvements | PATCH |
| `test` | Adding or modifying tests | - |
| `build` | Changes to the build system or dependencies | - |
| `ci` | CI/CD configuration changes | - |
| `chore` | Maintenance tasks (does not modify src or test) | - |
| `revert` | Reverts a previous commit | Depends on the reverted commit |

### Writing Rules

!!! info Subject
    - Use the imperative present tense ("add" not "added" or "adds")
    - Do not start with a capital letter
    - Do not end with a period
    - Maximum 72 characters

!!! info Body
    - Separate from the subject with a blank line
    - Explain the "what" and "why", not the "how"
    - Maximum 100 characters per line

!!! info Footer
    - Issue references: `Refs: #123, #456`
    - Closing issues: `Closes: #123`
    - Breaking changes: `BREAKING CHANGE: Description`

### Examples

=== "New Unit"

    ```bash
    feat(units): add Leviathan unit with siege capabilities
    
    Add the Leviathan unit with high health and powerful attacks.
    Includes new sprite assets and unit factory integration.
    
    Closes: #156
    ```

=== "Combat Bug Fix"

    ```bash
    fix(combat): prevent units from attacking through obstacles
    
    Fixed pathfinding issue where units could attack targets
    through solid terrain. Added line-of-sight validation.
    
    Refs: #203
    ```

=== "Shop Refactoring"

    ```bash
    refactor(shop): extract unit pricing logic to gameplay constants
    
    Moved hardcoded unit costs to centralized constants in gameplay.py.
    Improves maintainability and prevents pricing inconsistencies.
    ```

---

## Contribution Workflow

### Prerequisites

- Git 2.0+
- GitHub account with access to the repository
- Development environment configured according to the README

### Standard Process

#### 1. Preparation

```bash
# Fork the repository via the GitHub interface

# Clone the fork
git clone https://github.com/Fydyr/Galad-Islands.git
cd <repository>

# Configure the upstream repository
git remote add upstream https://github.com/Fydyr/Galad-Islands.git

# Synchronize with upstream
git fetch upstream
git checkout main
git merge upstream/main
```

#### 2. Branch Creation

!!! tip Naming Convention
    ```text
    <type>/<issue-number>-<short-description>
    ```

**Examples:**

```bash
git checkout -b feat/123-oauth-integration
git checkout -b fix/456-null-pointer-exception
git checkout -b docs/789-api-documentation
```

**Branch Types:**

- `feat/`: New feature
- `fix/`: Bug fix
- `docs/`: Documentation
- `refactor/`: Refactoring
- `test/`: Tests
- `chore/`: Maintenance

#### 3. Commit

```bash
# Add modified files
git add <files>

# Commit with conventional message
git commit -m "type(scope): description"

# Validation
git log --oneline
```

#### 4. Synchronization

```bash
# Fetch the latest changes
git fetch upstream
git rebase upstream/main

# Resolve conflicts if necessary
# Then continue the rebase
git rebase --continue
```

#### 5. Push and Pull Request

```bash
# Push to the fork
git push origin <branch-name>
```

!!! note In case of rebase
    Check if your changes might overwrite other contributors' changes.

!!! note Creating the Pull Request
    1. Open the GitHub interface
    2. Create a Pull Request from the fork's branch to upstream's `main`
    3. Fill out the PR template with:
        - **Title**: Clear summary of the change
        - **Description**: Context and technical details
        - **Type of change**: Feature, Bug fix, etc.
        - **Related issues**: References (#123)


---

## Code Standards

### General Principles

!!! abstract SOLID
    - Single Responsibility Principle
    - Open/Closed Principle
    - Liskov Substitution Principle
    - Interface Segregation Principle
    - Dependency Inversion Principle

!!! abstract Clean Code
    - Explicit and meaningful names
    - Short functions (< 20 lines)
    - Comments only when necessary
    - No duplicated code (DRY)
    - Proper error management

### Naming Conventions

=== "Variables and Functions"

    ```python
    # snake_case for variables and functions
    user_name = 'John'
    def get_user_data():
        pass
    ```

=== "Classes and Components"

    ```python
    # PascalCase for Classes and Components
    class UserService:
        pass
    class UserProfileComponent:
        pass
    ```

=== "Constants"

    ```python
    # UPPER_SNAKE_CASE for Constants
    MAX_RETRY_COUNT = 3
    API_BASE_URL = 'https://api.example.com'
    ```

=== "Files"

    - Utilities: `snake_case.py`

### Tests

!!! success Code Coverage
    - **Minimum Required**: 80%
    - **Goal**: 90%+

---

## Review Process

### Acceptance Criteria

!!! warning Mandatory
    - [ ] At least one approved review from a maintainer
    - [ ] No conflicts with the target branch
    - [ ] Up-to-date documentation
    - [ ] Satisfactory test coverage

!!! tip Recommended
    - [ ] Performance evaluated for critical changes
    - [ ] Accessibility checked for UI changes
    - [ ] Security analyzed for sensitive changes

### Handling Feedback

**Resolving comments:**

1. Read and understand all comments
2. Apply the requested changes
3. Reply to comments to explain choices
4. Mark comments as resolved
5. Request a new review

**Changes after review:**

```bash
# Modify the code
git add <files>

# Correction commit
git commit -m "fix(scope): address review comments"

# Push
git push origin <branch-name>
```

---

## Contact

!!! question For any questions
    Open an issue with the `question` label

### Maintainers

- Enzo Fournier
- Edouard Alluin
- Julien Behani
- Ethan Cailliau
- Alexandre Damman
- Romain Lambert

---

!!! info Document Version
    **Version**: 1.0.0