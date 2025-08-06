# Cursor Automation

A comprehensive automation framework for Cursor IDE using Model Context Protocol (MCP) servers.

## Overview

This project provides a collection of MCP servers and utilities for automating development tasks in Cursor IDE. It includes:

- **Execution MCP**: Step-by-step instruction execution with AI assistance
- **DevTools MCP**: Chrome DevTools Protocol integration for web testing
- **Telegram MCP**: Build communication via Telegram
- **Ref MCP**: Documentation search and reference tools

## Project Structure

```
cursor_automation/
├── servers/
│   ├── execution-mcp/          # Instruction execution server
│   ├── devtools-mcp/           # Chrome DevTools integration
│   └── build_with_telegram/    # Telegram build communication
├── venv/                       # Main Python virtual environment
├── requirements.txt            # Main project dependencies
└── README.md                  # This file
```

## Servers

### Execution MCP (`servers/execution-mcp/`)

A step-by-step instruction execution server that can:
- Read instructions from JSON files
- Execute tasks with AI assistance
- Track execution history
- Provide real-time feedback

**Features:**
- Instruction parsing from JSON format
- Step-by-step execution with AI interpretation
- History tracking and state management
- Cache management for performance

### DevTools MCP (`servers/devtools-mcp/`)

Chrome DevTools Protocol integration for web testing and automation.

**Features:**
- Chrome browser automation
- Page content verification
- Web testing capabilities
- DevTools protocol communication

### Telegram MCP (`servers/build_with_telegram/`)

Build communication and notifications via Telegram.

**Features:**
- Build status notifications
- Telegram bot integration
- Build process monitoring
- Real-time communication

## Setup

### Prerequisites

- Python 3.11+
- Node.js (for devtools-mcp)
- Chrome browser (for devtools-mcp)
- Telegram bot token (for telegram-mcp)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd cursor_automation
   ```

2. **Set up the main virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up individual servers:**

   **Execution MCP:**
   ```bash
   cd servers/execution-mcp
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

   **DevTools MCP:**
   ```bash
   cd servers/devtools-mcp
   npm install
   ```

   **Telegram MCP:**
   ```bash
   cd servers/build_with_telegram
   # Follow server-specific setup instructions
   ```

### MCP Configuration

Add the following to your `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "instruction_executor": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/servers/execution-mcp/instruction_executor.py"],
      "cwd": "/path/to/cursor_automation"
    },
    "devtools": {
      "command": "npx",
      "args": ["-y", "tsx", "/path/to/servers/devtools-mcp/src/index.ts"]
    },
    "telegram_server": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/servers/build_with_telegram/telegram_server.py"]
    }
  }
}
```

## Usage

### Execution MCP

1. **Create instructions file:**
   ```json
   {
     "goal": "Create a simple web page",
     "description": "Web Development Test",
     "steps": [
       {
         "step": 1,
         "description": "Read requirements from rule.md"
       },
       {
         "step": 2,
         "description": "Create HTML page"
       }
     ],
     "requirements": {
       "rule_file": "rule.md",
       "html_file": "test.html"
     }
   }
   ```

2. **Start execution:**
   ```python
   # Use the MCP tools in Cursor
   start_execution()
   execute_next_step()
   ```

### DevTools MCP

1. **Open a web page in Chrome**
2. **Use DevTools commands:**
   ```python
   # Navigate to a page
   mcp_devtools_cdp_command("Page.navigate", '{"url": "https://example.com"}')
   
   # Get page content
   mcp_devtools_cdp_command("Runtime.evaluate", '{"expression": "document.body.innerHTML"}')
   ```

### Telegram MCP

1. **Set up Telegram bot token**
2. **Start the server:**
   ```python
   mcp_telegram_server_start_telegram_server()
   ```

## Development

### Adding New Servers

1. Create a new directory in `servers/`
2. Implement the MCP server protocol
3. Add configuration to `~/.cursor/mcp.json`
4. Update this README

### Testing

Each server includes its own test suite:

```bash
# Test execution-mcp
cd servers/execution-mcp
python test_paths.py

# Test devtools-mcp
cd servers/devtools-mcp
npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the individual server documentation
- Review the MCP_SETUP_GUIDE.md
- Open an issue on GitHub 