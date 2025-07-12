# Error Handling Improvements

## Problem
Found **29 bare `except:` clauses** across the codebase - a serious code quality issue.

## Improvements Made

### Fixed Files:
1. **providers/gemini_provider.py** - JSON parsing error
2. **providers/exa_provider.py** - 3 instances (URL parsing, JSON parsing, health check)  
3. **providers/tavily_provider.py** - 3 instances (URL parsing, JSON parsing, health check)
4. **cleanup_sources.py** - URL parsing error

### Error Handling Patterns Applied:

#### Before (Bad):
```python
try:
    error_data = response.json()
except:
    error_data = {}
```

#### After (Good):
```python
try:
    error_data = response.json()
except (ValueError, TypeError, AttributeError) as e:
    logger.warning(f"Could not parse error response JSON: {e}")
    error_data = {}
```

### Benefits:

1. **Specific Exception Handling**: Catch only expected exceptions
2. **Proper Logging**: Log the actual error for debugging
3. **Maintainability**: Clear understanding of what can go wrong
4. **Debugging**: Stack traces are preserved for unexpected errors

### Remaining Work:

The following files still contain bare `except:` clauses and should be fixed using the same pattern:

- `search_service_multi.py` (9 instances)
- `data_extraction.py` (1 instance)  
- `providers/abacus_provider.py` (1 instance)
- `providers/firecrawl_provider.py` (1 instance)
- `providers/grok_provider.py` (1 instance)
- `providers/openrouter_provider.py` (1 instance)
- `providers/utils/firecrawl_utils.py` (1 instance)
- `search_service_multi_enhanced.py` (1 instance)

### Recommended Pattern:

```python
# For JSON parsing
except (ValueError, TypeError, AttributeError) as e:
    logger.warning(f"Could not parse JSON: {e}")

# For URL parsing  
except (ValueError, TypeError) as e:
    logger.debug(f"Could not parse URL: {e}")

# For HTTP requests
except (httpx.RequestError, httpx.HTTPStatusError, Exception) as e:
    logger.warning(f"API request failed: {e}")
```

This systematic approach to error handling significantly improves code quality and debugging capabilities.