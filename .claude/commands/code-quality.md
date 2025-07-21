# Code Quality Verification Command

You are tasked with performing a comprehensive code quality analysis and fixing any issues found. Follow these steps meticulously:

## Step 1: Read the Target File

$ARGUMENTS

If a file path is provided above, read and analyze it first. If no file is provided, proceed directly to running the linters on the entire project.

## Step 2: Run Initial Quality Checks

Execute the following commands and capture their output:

```bash
ruff check . --fix
mypy .
```

## Step 3: Deep Analysis

After running the linters, perform a thorough analysis:

- Examine each error message carefully
- Understand the root cause of each issue, not just the symptoms
- Consider the broader context and implications of each error
- Identify patterns in the errors that might indicate systemic issues

## Step 4: Solution Planning

Before fixing, think deeply about:

- The most elegant and maintainable solution for each issue
- How fixes might interact with each other
- Whether refactoring would be more appropriate than quick fixes
- Ensuring solutions follow Python best practices and modern conventions

## Step 5: Implementation Requirements

When fixing the code, strictly adhere to these principles:

### Python 3.12+ Type System

- Use `str | None` instead of `Optional[str]`
- Use `list[User]` instead of `List[User]`
- Use `dict[str, int]` instead of `Dict[str, int]`
- Import from `typing` only for advanced types (`Protocol`, `TypeVar`, `Generic`, `Literal`, etc.)
- Use `from __future__ import annotations` when forward references are needed
- Prefer concrete types over `Any` - if you must use `Any`, document why
- Never use `# type: ignore` without exhausting all other options

### Type Hints Best Practices

- Use generics properly: `list[T]`, `dict[K, V]`, not bare `list` or `dict`
- Define custom types for complex structures: `TypeAlias` or `TypedDict`
- Use `Protocol` for structural subtyping when appropriate
- Leverage `Literal` types for known string values
- Apply `@overload` for functions with multiple signatures

### Code Quality Standards

- Follow PEP 8 formatting without exceptions
- Use descriptive names that clearly indicate purpose and scope
- Prefer composition over inheritance
- Keep functions small and focused on a single responsibility
- Document complex logic with clear comments
- Use docstrings for all public functions and classes

## Step 6: Fix Implementation

Apply the fixes systematically:

1. Start with type-related errors
2. Address linting issues
3. Refactor if necessary to eliminate root causes
4. Ensure each fix maintains or improves code clarity

## Step 7: Verification

After implementing all fixes, run the verification commands again:

```bash
ruff check .
mypy .
```

Both commands must pass with zero errors or warnings.

## Step 8: Final Review

Review the changes to ensure:

- All fixes follow best practices
- No quick fixes or workarounds were used
- The code is more maintainable than before
- Type safety has been improved
- The code remains readable and clear

Report the summary of:

1. Issues found initially
2. Root causes identified
3. Solutions implemented
4. Verification results

Remember: Quality over speed. Take time to understand and fix issues properly.
