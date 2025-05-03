# UnitMCP Documentation Standards

This document outlines the documentation standards for the UnitMCP project. Following these guidelines ensures consistency across the codebase and makes it easier for developers to understand and contribute to the project.

## Module Documentation

Every Python module should include a docstring at the top of the file with the following sections:

```python
"""
Module Name: [module_name]

This module provides [brief description].

Classes:
    ClassName: [brief description]

Functions:
    function_name: [brief description]

Attributes:
    attribute_name: [brief description]

Example:
    ```python
    from unitmcp.[module_name] import ClassName
    
    instance = ClassName()
    result = instance.method()
    ```
"""
```

## Class Documentation

Classes should include a docstring with the following sections:

```python
class ClassName:
    """
    Brief description of the class.
    
    Detailed description of the class, its purpose, and behavior.
    
    Attributes:
        attribute_name (type): Description of the attribute.
    
    Example:
        ```python
        instance = ClassName(param1, param2)
        result = instance.method()
        ```
    """
```

## Method and Function Documentation

Methods and functions should include a docstring with the following sections:

```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description of the function.
    
    Detailed description of the function, its purpose, and behavior.
    
    Args:
        param1: Description of param1.
        param2: Description of param2.
    
    Returns:
        Description of return value.
        
    Raises:
        ExceptionType: Description of when this exception is raised.
    
    Example:
        ```python
        result = function_name(param1, param2)
        ```
    """
```

## Type Annotations

All public APIs should include type annotations for parameters and return values. Use the `typing` module for complex types:

```python
from typing import Dict, List, Optional, Union

def function_name(param1: str, param2: Optional[int] = None) -> Dict[str, List[str]]:
    """Function documentation."""
    # Function implementation
```

## README Files

Each module or component should have a README.md file with the following sections:

1. **Overview**: Brief description of the module/component
2. **Installation**: How to install or set up the module
3. **Usage**: How to use the module, with examples
4. **API Reference**: Description of public APIs
5. **Configuration**: Configuration options
6. **Examples**: Practical examples
7. **Troubleshooting**: Common issues and solutions

## Example Documentation

Examples should include:

1. A descriptive filename
2. A docstring at the top explaining the purpose of the example
3. Inline comments explaining key steps
4. A README.md file if the example is complex

## Error Messages

Error messages should be:

1. Clear and specific
2. Include actionable information
3. Reference documentation where appropriate

## Logging

Logging should follow these guidelines:

1. **DEBUG**: Detailed information, typically of interest only when diagnosing problems
2. **INFO**: Confirmation that things are working as expected
3. **WARNING**: Indication that something unexpected happened, but the application still works
4. **ERROR**: Due to a more serious problem, the application has not been able to perform a function
5. **CRITICAL**: A serious error, indicating that the application itself may be unable to continue running

## Documentation Generation

API documentation is generated using Sphinx. To ensure your documentation is properly included:

1. Follow the docstring format described above
2. Run `make docs` to generate the documentation
3. Check the generated documentation for completeness and accuracy

## Updating Documentation

When making changes to the code:

1. Update the relevant documentation
2. Update examples if behavior has changed
3. Update the CHANGELOG.md file

## Documentation Review

Documentation should be reviewed as part of the code review process. Reviewers should check that:

1. Documentation is complete and accurate
2. Examples work as described
3. Type annotations are correct
4. Error messages are clear and actionable
