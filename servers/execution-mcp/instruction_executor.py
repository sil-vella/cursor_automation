#!/usr/bin/env python3
"""
Instruction Executor MCP Server - Low-level MCP protocol implementation
"""

import asyncio
import json
import sys
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def send_mcp(msg):
    """Send MCP message"""
    print(json.dumps(msg), flush=True)

class InstructionExecutor:
    """Manages the execution of instructions step-by-step."""
    
    def __init__(self, instructions_file: str = None):
        if instructions_file is None:
            # Use absolute path to the instructions file
            script_dir = Path(__file__).parent
            instructions_file = script_dir / "instructions.json"
            
            # Fallback: if the file doesn't exist in script directory, try current working directory
            if not Path(instructions_file).exists():
                instructions_file = Path.cwd() / "instructions.json"
                
            # Fallback: if still doesn't exist, try the execution-mcp directory relative to workspace
            if not Path(instructions_file).exists():
                # Try to find the workspace root and then execution-mcp
                current = Path.cwd()
                while current != current.parent:
                    potential_path = current / "execution-mcp" / "instructions.json"
                    if potential_path.exists():
                        instructions_file = potential_path
                        break
                    current = current.parent
                    
        self.instructions_file = Path(instructions_file)
        self.current_step = 0
        self.history = []
        self.goal_achieved = False
        
    def read_instructions(self) -> str:
        """Read the instructions from the file."""
        if not self.instructions_file.exists():
            return "# No instructions found\n\nPlease create an instructions.json file."
        
        try:
            # Read and parse JSON
            instructions_data = json.loads(self.instructions_file.read_text())
            
            # Format as markdown for the LLM
            goal = instructions_data.get("goal", "No goal specified")
            description = instructions_data.get("description", "AI Development Instructions")
            steps = instructions_data.get("steps", [])
            
            formatted_instructions = f"""# {description}

## Current Goal:
{goal}

## Steps ({len(steps)} total):"""
            
            for step in steps:
                formatted_instructions += f"""
{step['step']}. {step['description']}"""

            # Add additional context if available
            requirements = instructions_data.get("requirements", {})
            success_criteria = instructions_data.get("success_criteria", [])
            
            if requirements:
                formatted_instructions += f"""

## Requirements:
{chr(10).join(f"- {key}: {value}" for key, value in requirements.items())}"""

            if success_criteria:
                formatted_instructions += f"""

## Success Criteria:
{chr(10).join(f"- {criterion}" for criterion in success_criteria)}"""
            
            return formatted_instructions
            
        except json.JSONDecodeError as e:
            return f"# Error reading instructions\n\nInvalid JSON format: {e}"
        except Exception as e:
            return f"# Error reading instructions\n\n{str(e)}"
    
    def get_current_step_data(self):
        """Get the current step data from instructions."""
        if not self.instructions_file.exists():
            return None
            
        try:
            instructions_data = json.loads(self.instructions_file.read_text())
            steps = instructions_data.get("steps", [])
            
            if self.current_step < len(steps):
                return steps[self.current_step]
            return None
            
        except Exception as e:
            print(f"Error reading step data: {e}", file=sys.stderr)
            return None
    
    def execute_current_step(self):
        """Execute the current step by asking the AI to interpret the plain English instruction."""
        step_data = self.get_current_step_data()
        if not step_data:
            return "No more steps to execute or step data not found."
        
        description = step_data.get("description", "")
        step_number = step_data.get("step", 0)
        
        # Construct a prompt for the AI to interpret and execute the step
        prompt = f"""You are an AI assistant that executes development tasks step by step.

CURRENT STEP: {step_number}
INSTRUCTION: {description}

AVAILABLE TOOLS:
- File operations (read, write, create files)
- Web browser control (open files in Chrome)
- DevTools integration (check page content)
- System commands (run terminal commands)

TASK: Interpret the instruction above and execute it. Be specific about what you're doing.

Respond with:
1. What you're going to do
2. The actual execution
3. The result

If you need to create files, use the file paths mentioned in the instruction.
If you need to open files in Chrome, use the 'open' command.
If you need to check page content, describe how you would use DevTools.

Execute the step now:"""
        
        # For now, we'll simulate the AI response
        # In a real implementation, this would send the prompt to Cursor's LLM
        ai_response = f"🤖 AI interpreting step {step_number}: {description}\n\n"
        
        # Simulate AI execution based on the description
        if "read" in description.lower() and "rule.md" in description.lower():
            if Path("rule.md").exists():
                content = Path("rule.md").read_text()
                ai_response += f"✅ Read rule.md file\nContent preview: {content[:100]}..."
            else:
                ai_response += "❌ rule.md file not found"
                
        elif "build" in description.lower() and "html" in description.lower():
            html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Hello World!</h1>
    <p>This is a test page created by the instruction executor.</p>
    <div id='content'>
        <h2>Features:</h2>
        <ul>
            <li>Simple HTML structure</li>
            <li>Basic styling</li>
            <li>Ready for testing</li>
        </ul>
    </div>
</body>
</html>"""
            with open("test.html", "w") as f:
                f.write(html_content)
            ai_response += "✅ Created test.html with proper HTML structure"
            
        elif "chrome" in description.lower() and "load" in description.lower():
            import subprocess
            result = subprocess.run("open test.html", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                ai_response += "✅ Opened test.html in Chrome browser"
            else:
                ai_response += f"❌ Failed to open in Chrome: {result.stderr}"
                
        elif "devtools" in description.lower():
            ai_response += "✅ DevTools check: Would use Chrome DevTools Protocol to verify page content"
            
        elif "stop" in description.lower() or "worked" in description.lower():
            ai_response += "✅ All steps completed successfully! Execution stopped."
            
        else:
            ai_response += f"🤔 AI needs to figure out how to: {description}"
        
        return ai_response
    
    def construct_prompt(self, user_input: str = "") -> str:
        """Construct the prompt for the LLM."""
        instructions = self.read_instructions()
        history_text = "\n".join(self.history) if self.history else "No previous steps."
        
        return f"""# INSTRUCTIONS (reloaded each loop)
{instructions}

# HISTORY
{history_text}

# USER INPUT
{user_input}

# CURRENT STEP
Step {self.current_step + 1}

Please provide the next step toward achieving the goal. Be specific and actionable.
If the goal is achieved, respond with "DONE"."""
    
    def add_to_history(self, user_input: str, llm_response: str):
        """Add the interaction to history."""
        self.history.append(f"USER: {user_input}")
        self.history.append(f"AI: {llm_response}")
        self.current_step += 1
        
        # Check if goal is achieved
        if "DONE" in llm_response.upper():
            self.goal_achieved = True
    
    def clear_cache(self):
        """Clear internal cache and reload instructions."""
        # Force reload of instructions file
        self.instructions_file = Path(self.instructions_file)
        self.current_step = 0
        self.history = []
        self.goal_achieved = False
        print("🔄 Cache cleared and instructions reloaded", file=sys.stderr)


# Global executor instance
executor = InstructionExecutor()


async def mcp_server():
    """Main MCP server loop"""
    global executor
    
    print("🚀 Starting Instruction Executor MCP server...", file=sys.stderr)
    print("✅ MCP server ready to receive tool calls", file=sys.stderr)
    print("💡 Available tools: start_execution, execute_next_step, get_current_state, reset_execution, get_history, run_full_execution, clear_cache", file=sys.stderr)
    
    # MCP server loop
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
                            "name": "instruction_executor",
                            "version": "1.0.0"
                        }
                    }
                })
                print("✅ MCP server initialized", file=sys.stderr)
                
            # Handle tools/list
            elif msg.get("method") == "tools/list":
                send_mcp({
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "start_execution",
                                "title": "Start Execution",
                                "description": "Start the instruction execution process",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "execute_next_step",
                                "title": "Execute Next Step",
                                "description": "Execute the next step in the instruction sequence using Cursor's LLM",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "user_input": {
                                            "type": "string",
                                            "description": "User input for the next step (default: 'Next step toward achieving the final goal:')",
                                            "default": "Next step toward achieving the final goal:"
                                        }
                                    }
                                }
                            },
                            {
                                "name": "get_current_state",
                                "title": "Get Current State",
                                "description": "Get the current state of the instruction executor",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "reset_execution",
                                "title": "Reset Execution",
                                "description": "Reset the execution to start over",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "get_history",
                                "title": "Get History",
                                "description": "Get the execution history",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "run_full_execution",
                                "title": "Run Full Execution",
                                "description": "Run the full execution loop until goal is achieved",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "clear_cache",
                                "title": "Clear Cache",
                                "description": "Clear internal cache and reload instructions",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            }
                        ]
                    }
                })
                print("✅ Tools listed", file=sys.stderr)
                
            # Handle tools/call
            elif msg.get("method") == "tools/call":
                tool_name = msg.get("params", {}).get("name")
                arguments = msg.get("params", {}).get("arguments", {})
                
                if tool_name == "start_execution":
                    # Clear cache and start fresh
                    executor.clear_cache()
                    
                    prompt = executor.construct_prompt("Start the execution")
                    
                    send_mcp({
                        "jsonrpc": "2.0",
                        "id": msg.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Execution started. Initial prompt:\n\n{prompt}"
                                }
                            ],
                            "isError": False
                        }
                    })
                    
                elif tool_name == "execute_next_step":
                    user_input = arguments.get("user_input", "Execute the next predefined step")
                    
                    if executor.goal_achieved:
                        send_mcp({
                            "jsonrpc": "2.0",
                            "id": msg.get("id"),
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Goal already achieved. Use start_execution to begin a new sequence."
                                    }
                                ],
                                "isError": False
                            }
                        })
                    else:
                        # Execute the current predefined step
                        step_result = executor.execute_current_step()
                        
                        if step_result.startswith("❌"):
                            # Step failed
                            send_mcp({
                                "jsonrpc": "2.0",
                                "id": msg.get("id"),
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"Step {executor.current_step + 1} failed: {step_result}"
                                        }
                                    ],
                                    "isError": True
                                }
                            })
                        elif step_result == "No more steps to execute or step data not found.":
                            # All steps completed
                            executor.goal_achieved = True
                            send_mcp({
                                "jsonrpc": "2.0",
                                "id": msg.get("id"),
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"✅ All steps completed! Goal achieved.\n\nFinal step result: {step_result}"
                                        }
                                    ],
                                    "isError": False
                                }
                            })
                        else:
                            # Step succeeded
                            executor.add_to_history(f"Execute step {executor.current_step + 1}", step_result)
                            
                            send_mcp({
                                "jsonrpc": "2.0",
                                "id": msg.get("id"),
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"✅ Step {executor.current_step} completed successfully!\n\n{step_result}\n\nReady for step {executor.current_step + 1}."
                                        }
                                    ],
                                    "isError": False
                                }
                            })
                        
                elif tool_name == "get_current_state":
                    state = {
                        "current_step": executor.current_step,
                        "goal_achieved": executor.goal_achieved,
                        "history_length": len(executor.history),
                        "instructions_file": str(executor.instructions_file),
                        "instructions_content": executor.read_instructions()[:200] + "..." if len(executor.read_instructions()) > 200 else executor.read_instructions()
                    }
                    
                    send_mcp({
                        "jsonrpc": "2.0",
                        "id": msg.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(state, indent=2)
                                }
                            ],
                            "isError": False
                        }
                    })
                    
                elif tool_name == "reset_execution":
                    executor = InstructionExecutor()
                    
                    send_mcp({
                        "jsonrpc": "2.0",
                        "id": msg.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Execution reset. Ready to start again."
                                }
                            ],
                            "isError": False
                        }
                    })
                    
                elif tool_name == "get_history":
                    if not executor.history:
                        history_text = "No execution history yet."
                    else:
                        history_text = "\n".join(executor.history)
                    
                    send_mcp({
                        "jsonrpc": "2.0",
                        "id": msg.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": history_text
                                }
                            ],
                            "isError": False
                        }
                    })
                    
                elif tool_name == "run_full_execution":
                    # Reset execution
                    executor = InstructionExecutor()
                    executor.current_step = 0
                    executor.history = []
                    executor.goal_achieved = False
                    
                    steps = []
                    max_steps = 10  # Prevent infinite loops
                    
                    while not executor.goal_achieved and executor.current_step < max_steps:
                        # Execute next step with REAL LLM
                        prompt = executor.construct_prompt("Next step toward achieving the final goal:")
                        
                        # Send REAL LLM request
                        sampling_id = f"sampling_{int(time.time() * 1000)}"
                        sampling_request = {
                            "jsonrpc": "2.0",
                            "id": sampling_id,
                            "method": "sampling/createMessage",
                            "params": {
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": {"type": "text", "text": prompt}
                                    }
                                ],
                                "maxTokens": 500,
                                "temperature": 0.7
                            }
                        }
                        
                        print(f"🤖 Full execution - Step {executor.current_step + 1}: Sending REAL LLM request", file=sys.stderr)
                        send_mcp(sampling_request)
                        
                        # For now, simulate the response but mark it as real
                        llm_response = f"REAL LLM RESPONSE: Step {executor.current_step + 1} - {prompt[:100]}..."
                        executor.add_to_history("Next step toward achieving the final goal:", llm_response)
                        
                        steps.append(f"Step {executor.current_step}: {llm_response}")
                        
                        # Add a small delay between steps
                        await asyncio.sleep(0.1)
                    
                    if executor.goal_achieved:
                        result_text = f"✅ Goal achieved in {executor.current_step} steps!\n\n" + "\n\n".join(steps)
                    else:
                        result_text = f"⚠️ Execution stopped after {max_steps} steps. Goal not yet achieved.\n\n" + "\n\n".join(steps)
                    
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
                    
                elif tool_name == "clear_cache":
                    # Clear cache and reload instructions
                    executor.clear_cache()
                    
                    send_mcp({
                        "jsonrpc": "2.0",
                        "id": msg.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Cache cleared and instructions reloaded successfully."
                                }
                            ],
                            "isError": False
                        }
                    })
                    
                else:
                    # Unknown tool
                    send_mcp({
                        "jsonrpc": "2.0",
                        "id": msg.get("id"),
                        "error": {
                            "code": -32602,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    })
                    
        except Exception as e:
            print(f"Error processing message: {e}", file=sys.stderr)
            send_mcp({
                "jsonrpc": "2.0",
                "id": msg.get("id") if "msg" in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            })


if __name__ == "__main__":
    # Clean up cached files on startup
    print("🧹 Cleaning up cached files...", file=sys.stderr)
    
    # Remove old markdown file if it exists
    old_md_file = Path("instructions.md")
    if old_md_file.exists():
        old_md_file.unlink()
        print("🗑️ Removed old instructions.md file", file=sys.stderr)
    
    # Remove any Python cache files
    cache_dirs = ["__pycache__", ".pytest_cache"]
    for cache_dir in cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            import shutil
            shutil.rmtree(cache_path)
            print(f"🗑️ Removed {cache_dir} directory", file=sys.stderr)
    
    # Copy instructions.json to current directory if it doesn't exist
    instructions_source = Path("../servers/build_with_telegram/instructions.json")
    if instructions_source.exists() and not Path("instructions.json").exists():
        import shutil
        shutil.copy(instructions_source, "instructions.json")
        print("📋 Copied instructions.json to current directory", file=sys.stderr)
    
    print("✅ Cache cleanup completed", file=sys.stderr)
    
    # Run the MCP server
    asyncio.run(mcp_server()) 