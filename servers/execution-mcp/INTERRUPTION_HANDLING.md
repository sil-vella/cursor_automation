# Interruption Handling in Execution MCP

## Overview

The Execution MCP server now includes intelligent interruption handling to prevent execution from being halted by user prompts, confirmations, or other interactive requests.

## Problem

During execution, Cursor AI may encounter situations that require user input:
- File deletion confirmations
- Overwrite file prompts
- Permission requests
- Terminal command confirmations
- Installation prompts

These interruptions can halt the execution process and require manual intervention.

## Solution

The `ExecutionInterruptionHandler` class automatically detects and handles these interruptions:

### Detection

The system monitors for common interruption patterns:
- "Do you want to continue?"
- "Are you sure you want to delete?"
- "File already exists. Overwrite?"
- "This action cannot be undone"
- "Permission denied. Continue anyway?"
- "Type 'y' to confirm"
- "Press Enter to continue"

### Auto-Response

When an interruption is detected, the system automatically responds:
- **Deletions**: `y` (confirm)
- **Overwrites**: `y` (confirm)
- **Continue prompts**: `Enter` or `y`
- **General confirmations**: `y` (default)

## Configuration

### Instructions File Configuration

Add an `execution_config` section to your `instructions.json`:

```json
{
  "goal": "Your goal here",
  "steps": [...],
  "execution_config": {
    "auto_confirm": true,
    "timeout_seconds": 300,
    "handle_interruptions": true,
    "max_retries": 3
  }
}
```

### Configuration Options

- **`auto_confirm`**: Whether to automatically confirm prompts (default: `true`)
- **`timeout_seconds`**: Maximum time per step (default: `300`)
- **`handle_interruptions`**: Enable interruption handling (default: `true`)
- **`max_retries`**: Maximum retry attempts per step (default: `3`)

## Usage

### Automatic Handling

The interruption handling is automatic during execution. When a step is executed:

1. The system monitors for interruption patterns
2. If detected, automatically responds appropriately
3. Continues execution without user intervention

### Manual Handling

You can also manually handle interruptions using the `handle_interruption` tool:

```python
# Handle a specific interruption
mcp_instruction_executor_handle_interruption(
    message="Do you want to delete this file? (y/n)",
    auto_confirm=True
)
```

### Testing

Run the test script to verify interruption detection:

```bash
cd servers/execution-mcp
python3 test_interruption_handling.py
```

## Examples

### File Operations

**Before (interruption):**
```
$ rm important_file.txt
rm: remove 'important_file.txt'? 
```

**After (auto-handled):**
```
$ rm important_file.txt
rm: remove 'important_file.txt'? y
✅ File deleted successfully
```

### Installation Prompts

**Before (interruption):**
```
$ pip install package
Do you want to continue? (y/n)
```

**After (auto-handled):**
```
$ pip install package
Do you want to continue? (y/n) y
✅ Package installed successfully
```

### Permission Requests

**Before (interruption):**
```
$ sudo command
Password: 
```

**After (auto-handled):**
```
$ sudo command
Password: [auto-filled or skipped]
✅ Command executed successfully
```

## Advanced Features

### Timeout Detection

The system includes timeout detection to prevent infinite waits:

- **Default timeout**: 5 minutes per step
- **Configurable**: Set via `timeout_seconds` in config
- **Automatic**: Steps are marked as failed if they timeout

### Retry Logic

Failed steps can be retried:

- **Max retries**: Configurable via `max_retries`
- **Smart retry**: Only retry on certain failure types
- **Backoff**: Increasing delays between retries

### Custom Responses

You can customize auto-responses for specific scenarios:

```python
# In the interruption handler
if "delete" in message.lower():
    return "y\n"  # Confirm deletion
elif "overwrite" in message.lower():
    return "y\n"  # Confirm overwrite
elif "continue" in message.lower():
    return "\n"   # Press Enter
```

## Troubleshooting

### Common Issues

1. **Interruption not detected**: Add the pattern to `interruption_indicators`
2. **Wrong auto-response**: Customize the response logic
3. **Timeout too short**: Increase `timeout_seconds`
4. **Too many retries**: Adjust `max_retries`

### Debug Mode

Enable debug logging to see interruption detection:

```python
# The system logs interruption detection to stderr
print(f"⚠️ Interruption detected: {message}", file=sys.stderr)
print(f"🔄 Auto-responding: {response.strip()}", file=sys.stderr)
```

## Best Practices

1. **Test thoroughly**: Run interruption tests before production
2. **Monitor logs**: Check for unexpected interruptions
3. **Update patterns**: Add new interruption patterns as needed
4. **Configure carefully**: Set appropriate timeouts and retry limits
5. **Document exceptions**: Note any manual intervention required

## Future Enhancements

- **Machine learning**: Learn from user responses
- **Context awareness**: Different responses based on context
- **User preferences**: Allow user to set default responses
- **Integration**: Better integration with other MCP servers 