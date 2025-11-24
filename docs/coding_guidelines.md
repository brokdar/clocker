# Coding Guidelines & Instructions for Claude 4

## <critical_instructions>

**YOU MUST FOLLOW EVERY RULE IN THIS DOCUMENT WITHOUT EXCEPTION. These are not suggestions - they are mandatory requirements.**
</critical_instructions>

## <core_philosophy>

### Mandatory Principles

1. **DELETE DEPRECATED CODE IMMEDIATELY**: Never maintain backward compatibility. Remove legacy functions instantly.
2. **FUNCTIONALITY FIRST**: Build working features before production patterns. No over-engineering.
3. **DETAILED ERRORS MANDATORY**: Every error must include: what failed, where, why, and actual values.
4. **BREAK TO IMPROVE**: Restructure code when it improves architecture. Never preserve poor patterns.

</core_philosophy>

## <python_requirements>

### Type Hints Are MANDATORY

**YOU MUST:**

- Use Python 3.12+ exclusively
- Add type hints to EVERY function, method, and variable
- Use generics: `List[str]`, `Dict[str, int]`, `Repository[User]`
- Use `User | None` instead of `Optional[None]`
- NEVER use `Any` unless interfacing with dynamic third-party code

**CORRECT:**

```python
def process_users(users: List[User], active: bool = True) -> Dict[int, User]:
    result: Dict[int, User] = {}
    for user in users:
        result[user.id] = user
    return result
```

**FORBIDDEN:**

```python
def process_users(users, active=True):  # NO TYPE HINTS - FORBIDDEN
    result = {}  # NO TYPE ANNOTATION - FORBIDDEN
    return result
```

</python_requirements>

## <import_rules>

**YOU MUST:**: Place ALL imports at file top
**YOU MUST NOT:**: Use inline imports (EXCEPT for circular dependencies)

**CORRECT:**

```python
import json
from datetime import datetime
from typing import List, Optional

import structlog
from fastapi import HTTPException

from app.models.user import User
from app.services.auth import AuthService
```

</import_rules>

## <documentation_standards>

### Google Style Docstrings ONLY

**YOU MUST document every public interface:**

```python
class UserService:
    """Service layer for user management operations.

    Handles CRUD operations and enforces business rules.
    """

    def create_user(self, data: UserCreate) -> User:
        """Creates a new user with validation.

        Args:
            data (UserCreate): User creation data.

        Returns:
            User: The newly created user.

        Raises:
            UserAlreadyExistsError: If username/email exists.
        """
        # Implementation here
```

**YOU MUST NOT:**

- Skip docstrings for public interfaces
- Use single-line docstrings for complex functions
- Mix docstring formats

</documentation_standards>

## <commenting_rules>

### Comments: WHY not WHAT

**FORBIDDEN:**

```python
# Increment counter
counter += 1

# Check if admin
if user.role == "admin":
    pass
```

**REQUIRED:**

```python
# Batch size of 500: testing showed memory issues >1000, performance degradation <100
BATCH_SIZE = 500

# Workaround for upstream bug v2.1.0 - remove after v2.2.0 (issue #1234)
result = library_function(data, _internal_flag=True)
```

</commenting_rules>

## <error_handling>

### Comprehensive Errors ONLY

**YOU MUST create specific exceptions:**

```python
class UserNotFoundError(Exception):
    def __init__(self, user_id: int, lookup_field: str = "id"):
        super().__init__(f"User not found: {lookup_field}={user_id}")

class ValidationError(Exception):
    def __init__(self, field: str, value: Any, constraint: str):
        super().__init__(
            f"Validation failed for '{field}': "
            f"value={value!r} violates {constraint}"
        )
```

**YOU MUST include full context:**

```python
except PaymentGatewayError as e:
    raise PaymentProcessingError(
        f"Payment failed for order {order.id}: "
        f"amount=${order.total}, customer={order.customer_id}, "
        f"gateway_response={e.response_code}"
    ) from e
```

**NEVER:**

- Use bare `except:` clauses
- Return `None` for failures
- Catch generic `Exception`

</error_handling>

## <logging_standards>

### Structured Logging with structlog

**YOU MUST log business events:**

```python
import structlog
logger = structlog.get_logger(__name__)

logger.info(
    "user_action_completed",
    user_id=user.id,
    action="password_reset",
    duration_ms=elapsed_time
)
```

**YOU MUST NOT:**

```python
print(f"User {user_id} logged in")  # FORBIDDEN - NEVER use print
logger.error(f"Error: {e}")  # FORBIDDEN - exceptions logged centrally
```

**Log Levels:**

- `INFO`: Business events (login, order placed)
- `WARNING`: Concerning situations (approaching limits)
- `DEBUG`: Diagnostic info (dev only)
- Never use `ERROR` or `CRITICAL` - handled centrally

</logging_standards>

## <package_management>

### Use uv Exclusively

```bash
uv init                      # Initialize project
uv add fastapi sqlalchemy    # Add dependencies
uv add --dev pytest mypy     # Add dev dependencies
uv sync                      # Install from pyproject.toml
uv run python main.py        # Run scripts
```

NEVER use pip or requirements.txt

</package_management>

## <quality_commands>

### Run Before EVERY Commit

```bash
ruff check . --fix    # Fix linting
ruff format .         # Format code
mypy .               # Type check
```

</quality_commands>

## <architectural_decisions>

### Fix Issues Properly

**YOU MUST:**

1. Analyze root cause - never patch symptoms
2. Follow framework conventions
3. Implement proper abstractions
4. Prioritize maintainability over quick fixes

**YOU MUST NOT:**

- Apply workarounds without understanding
- Violate framework patterns
- Create technical debt

</architectural_decisions>

## <prohibited_patterns>

### ABSOLUTELY FORBIDDEN

```python
# FORBIDDEN: Backward compatibility
def old_function():  # DELETE IMMEDIATELY
    return new_function()

# FORBIDDEN: Over-engineering
class AbstractFactoryBuilderStrategy:  # NO

# FORBIDDEN: Hiding errors
try:
    risky_operation()
except:
    return None  # NEVER

# FORBIDDEN: Missing type hints
def process(data):  # WHERE ARE TYPE HINTS?
    return data

# FORBIDDEN: Generic exceptions
except Exception as e:  # Too generic

# FORBIDDEN: Inline imports (except circular deps)
def function():
    import pandas  # MOVE TO TOP
```

</prohibited_patterns>

## <final_mandate>

**THESE RULES ARE MANDATORY. EVERY SINGLE ONE.**

**Core Requirements:**

- Delete deprecated code IMMEDIATELY
- Detailed errors ALWAYS
- Type hints EVERYWHERE
- Google docstrings for ALL public interfaces
- Comment only WHY, never WHAT
- structlog for business events
- Break and rebuild for better architecture

**Violations are UNACCEPTABLE.**

</final_mandate>
