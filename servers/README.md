# MCP Servers

This directory contains various MCP (Model Context Protocol) servers for Cursor automation.

## Available Servers

### 1. build_with_telegram
A Telegram bot that integrates with MCP for automated build-test-fix loops across multiple projects.

**Location**: `build_with_telegram/`
**Technology**: Python
**Features**:
- Multi-project support with environment variable injection
- Interactive Telegram control for build processes
- MCP integration for automated workflows

**Setup**:
```bash
# Install Python dependencies
pip install -r ../../requirements.txt

# Run the server
cd build_with_telegram
python build_with_telegram.py --project-dir /path/to/your/project
```

### 2. devtools-mcp
A TypeScript-based MCP server for Chrome DevTools Protocol integration.

**Location**: `devtools-mcp/`
**Technology**: Node.js/TypeScript
**Features**:
- Chrome DevTools Protocol integration
- Real-time browser debugging via MCP
- CDP command execution

**Setup**:
```bash
# Install Node.js dependencies
cd devtools-mcp
npm install

# Run the server
npm start
# or
npm run dev
```

## MCP Configuration

These servers are configured in your Cursor MCP settings at `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "builder": {
      "command": "python",
      "args": ["/path/to/cursor_automation/servers/build_with_telegram/build_with_telegram.py"]
    },
    "devtools": {
      "command": "npx",
      "args": ["-y", "tsx", "/path/to/cursor_automation/servers/devtools-mcp/src/index.ts"]
    }
  }
}
```

## Project Structure

```
servers/
├── build_with_telegram/          # Python MCP Build Server
│   ├── build_with_telegram.py    # Main server file
│   └── README.md                 # Server documentation
├── devtools-mcp/                 # TypeScript MCP Server
│   ├── src/                      # Source code
│   │   ├── index.ts              # Main entry point
│   │   ├── cdp-mcp-server.ts     # CDP MCP server implementation
│   │   ├── cdp-client.ts         # CDP client implementation
│   │   └── utils.ts              # Utility functions
│   ├── package.json              # Node.js dependencies
│   ├── tsconfig.json             # TypeScript configuration
│   └── README.md                 # Server documentation
└── README.md                     # This file
```

## Dependencies

### Python Dependencies (build_with_telegram)
Managed in the root `requirements.txt`:
- `flask==2.3.3` - Web framework
- `requests==2.31.0` - HTTP library
- `python-dotenv==1.0.0` - Environment variables
- `python-telegram-bot==20.7` - Telegram bot library

### Node.js Dependencies (devtools-mcp)
Managed in `devtools-mcp/package.json`:
- `@modelcontextprotocol/sdk` - MCP SDK
- `ws` - WebSocket library
- `tsx` - TypeScript execution
- `typescript` - TypeScript compiler

## Adding New Servers

To add a new MCP server:

1. Create a new directory in `servers/`
2. Implement your server following MCP protocol
3. Add configuration to `~/.cursor/mcp.json`
4. Document the server in this README
5. Include appropriate dependency management (requirements.txt for Python, package.json for Node.js)

## Development Setup

### For Python Servers
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### For Node.js Servers
```bash
# Navigate to server directory
cd servers/[server-name]

# Install dependencies
npm install

# Run in development mode
npm run dev
``` 