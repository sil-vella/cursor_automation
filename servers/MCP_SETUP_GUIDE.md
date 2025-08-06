# MCP Server Setup Guide for Cursor

This guide explains how to create and configure MCP (Model Context Protocol) servers that work with Cursor IDE.

## Overview

MCP (Model Context Protocol) allows Cursor to communicate with external servers that provide tools, resources, and prompts. This enables powerful integrations like build automation, database access, API calls, and more.

## Protocol Requirements

### JSON-RPC 2.0 Format
All MCP servers **MUST** use JSON-RPC 2.0 message format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "method_name",
  "params": {}
}
```

### Required Message Flow

1. **Client sends `initialize` request**
2. **Server responds with capabilities**
3. **Client requests `tools/list`**
4. **Server responds with available tools**
5. **Client can call tools via `tools/call`**

## Basic Server Template

```python
#!/usr/bin/env python3
"""
Basic MCP server template for Cursor
"""

import json
import sys

def send_mcp(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

# Wait for initialization request from Cursor
for line in sys.stdin:
    try:
        msg = json.loads(line)
        
        # Handle initialization
        if msg.get("method") == "initialize":
            send_mcp({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": {
                        "name": "your_server_name",
                        "version": "1.0.0"
                    }
                }
            })
            
        # Handle tools/list
        elif msg.get("method") == "tools/list":
            send_mcp({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "your_tool_name",
                            "title": "Your Tool Title",
                            "description": "Description of what your tool does",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "param1": {
                                        "type": "string",
                                        "description": "Description of parameter"
                                    }
                                }
                            }
                        }
                    ]
                }
            })
            
        # Handle tools/call
        elif msg.get("method") == "tools/call":
            tool_name = msg.get("params", {}).get("name")
            arguments = msg.get("params", {}).get("arguments", {})
            
            if tool_name == "your_tool_name":
                # Your tool logic here
                result_text = "Your tool executed successfully!"
                
                send_mcp({
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result_text
                            }
                        ],
                        "isError": False
                    }
                })
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
```

## Cursor Configuration

### Global Configuration
Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "your_server_name": {
      "command": "/path/to/python",
      "args": ["/path/to/your/server.py"]
    }
  }
}
```

### Project-Specific Configuration
Create `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "project_server": {
      "command": "/path/to/python",
      "args": ["/path/to/project/server.py"]
    }
  }
}
```

## Key Requirements

### 1. Server Must Wait for Initialize
❌ **Wrong** - Don't send unsolicited messages:
```python
# Don't do this
send_mcp({"type": "hello", ...})
```

✅ **Correct** - Wait for initialize request:
```python
# Do this
if msg.get("method") == "initialize":
    send_mcp({"jsonrpc": "2.0", "id": msg.get("id"), "result": {...}})
```

### 2. Use JSON-RPC 2.0 Format
❌ **Wrong** - Old protocol format:
```python
{"type": "register_tool", "name": "tool_name"}
```

✅ **Correct** - JSON-RPC 2.0 format:
```python
{"jsonrpc": "2.0", "method": "tools/list", "id": 1}
```

### 3. Proper Error Handling
```python
try:
    # Your logic here
    send_mcp({"jsonrpc": "2.0", "id": msg.get("id"), "result": {...}})
except Exception as e:
    send_mcp({
        "jsonrpc": "2.0",
        "id": msg.get("id"),
        "error": {
            "code": -32603,
            "message": str(e)
        }
    })
```

## Testing Your Server

### Manual Testing
```bash
# Test initialization
echo '{"jsonrpc": "2.0", "method": "initialize", "id": 1}' | python your_server.py

# Test tools listing
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 2}' | python your_server.py

# Test tool call
echo '{"jsonrpc": "2.0", "method": "tools/call", "id": 3, "params": {"name": "your_tool", "arguments": {}}}' | python your_server.py
```

### Cursor Testing
1. Restart Cursor completely
2. Check MCP settings for green dot
3. Try commands in chat: "List available tools"

## Common Issues

### 1. "No tools or prompts" Error
- **Cause**: Server not following correct protocol
- **Fix**: Use JSON-RPC 2.0 format and wait for initialize

### 2. Server Not Starting
- **Cause**: Incorrect path or Python environment
- **Fix**: Use absolute paths and correct Python executable

### 3. Tools Not Appearing
- **Cause**: Protocol mismatch or server errors
- **Fix**: Check server logs and ensure proper JSON-RPC responses

## Advanced Features

### Environment Variables
```json
{
  "mcpServers": {
    "my_server": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "API_KEY": "your_api_key",
        "DEBUG": "true"
      }
    }
  }
}
```

### Multiple Tools
```python
"tools": [
    {
        "name": "tool1",
        "title": "First Tool",
        "description": "Description 1",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "tool2", 
        "title": "Second Tool",
        "description": "Description 2",
        "inputSchema": {"type": "object", "properties": {}}
    }
]
```

### Tool Parameters
```python
"inputSchema": {
    "type": "object",
    "properties": {
        "required_param": {
            "type": "string",
            "description": "Required parameter"
        },
        "optional_param": {
            "type": "string",
            "description": "Optional parameter"
        }
    },
    "required": ["required_param"]
}
```

## Best Practices

1. **Always wait for initialize** - Don't send unsolicited messages
2. **Use proper error handling** - Return JSON-RPC errors for failures
3. **Validate inputs** - Check tool parameters before processing
4. **Use descriptive names** - Make tool names and descriptions clear
5. **Test thoroughly** - Verify with manual testing before Cursor integration
6. **Log errors** - Use stderr for debugging information
7. **Handle timeouts** - Implement proper timeout handling for long operations

## Example: Build Server

See `servers/build_with_telegram/simple_test.py` for a working example that follows all these guidelines. 