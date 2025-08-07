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
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Logging setup
LOG_FILE = Path(__file__).parent / "execution.log"

def log_to_file(message: str, level: str = "INFO"):
    """Log messages to file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write to log: {e}", file=sys.stderr)

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
        
        # Return the step instruction for Cursor AI to execute
        # The MCP framework will handle passing this to the AI
        return f"**STEP {step_number}:** {description}\n\nPlease execute this step using your available tools."
    
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
        
        # Clear the log file to start fresh
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")  # Empty the log file
            print("🗑️ Log file cleared for fresh monitoring", file=sys.stderr)
            log_to_file("🔄 CACHE CLEARED - Log file emptied for fresh execution monitoring", "STARTUP")
        except Exception as e:
            print(f"Failed to clear log file: {e}", file=sys.stderr)
            
        print("🔄 Cache cleared and instructions reloaded", file=sys.stderr)


# Global executor instance
executor = InstructionExecutor()


async def mcp_server():
    """Main MCP server loop"""
    global executor
    
    print("🚀 Starting Instruction Executor MCP server...", file=sys.stderr)
    print("✅ MCP server ready to receive tool calls", file=sys.stderr)
    print("💡 Available tools: run_full_execution, get_current_state, reset_execution, get_history, clear_cache", file=sys.stderr)
    
    # Initialize logging
    log_to_file("=" * 80, "STARTUP")
    log_to_file("🚀 INSTRUCTION EXECUTOR MCP SERVER STARTED", "STARTUP")
    log_to_file(f"Log file location: {LOG_FILE}", "STARTUP")
    log_to_file("Available tools: run_full_execution, get_current_state, reset_execution, get_history, clear_cache", "STARTUP")
    log_to_file("Enhanced message interception and user prompt detection active", "STARTUP")
    log_to_file("=" * 80, "STARTUP")
    
    # MCP server loop
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            
            # ===== MESSAGE INTERCEPTION =====
            # Log all incoming messages for analysis
            method = msg.get("method", "unknown")
            msg_id = msg.get("id", "no-id")
            print(f"📨 Incoming: {method} (ID: {msg_id})", file=sys.stderr)
            
            # Log every message to file
            log_to_file(f"INCOMING MESSAGE: {method} (ID: {msg_id})")
            log_to_file(f"MESSAGE CONTENT: {json.dumps(msg, indent=2)}")
            
            # Detect potential user prompts/questions
            msg_str = json.dumps(msg).lower()
            
            # Look for user interaction patterns
            user_prompt_indicators = [
                "user",
                "input", 
                "prompt",
                "question",
                "ask",
                "confirm",
                "choose",
                "select",
                "enter",
                "provide"
            ]
            
            # Enhanced patterns for actual user chat prompts
            chat_prompt_patterns = [
                "what would you like",
                "please provide",
                "please enter",
                "please specify",
                "please choose",
                "please select",
                "do you want",
                "would you prefer",
                "which option",
                "how would you like",
                "please confirm",
                "please tell me",
                "what should",
                "please input",
                "enter your",
                "type your",
                "specify the"
            ]
            
            user_interaction_detected = False
            detected_indicator = None
            chat_prompt_detected = False
            detected_chat_pattern = None
            
            # Check for basic user interaction patterns
            for indicator in user_prompt_indicators:
                if indicator in msg_str:
                    user_interaction_detected = True
                    detected_indicator = indicator
                    print(f"🔍 DETECTED USER INTERACTION: '{indicator}' in message", file=sys.stderr)
                    print(f"🔍 Full message content: {json.dumps(msg, indent=2)}", file=sys.stderr)
                    
                    # LOG USER INTERACTION DETECTION
                    log_to_file(f"🚨 USER INTERACTION DETECTED: '{indicator}' found in message", "ALERT")
                    log_to_file(f"USER INTERACTION DETAILS: {json.dumps(msg, indent=2)}", "ALERT")
                    break
            
            # Check for actual chat prompt patterns
            for pattern in chat_prompt_patterns:
                if pattern in msg_str:
                    chat_prompt_detected = True
                    detected_chat_pattern = pattern
                    print(f"💬 DETECTED CHAT PROMPT: '{pattern}' in message", file=sys.stderr)
                    
                    # LOG CHAT PROMPT DETECTION
                    log_to_file(f"🚨 CHAT PROMPT DETECTED: '{pattern}' found in message", "CHAT_PROMPT")
                    log_to_file(f"CHAT PROMPT DETAILS: {json.dumps(msg, indent=2)}", "CHAT_PROMPT")
                    break
            
            # Detect execution status messages and extract chat content
            if method == "notifications/message" or "content" in msg_str:
                content = msg.get("params", {}).get("content", "")
                if content:
                    print(f"💬 Content message: {content[:100]}...", file=sys.stderr)
                    log_to_file(f"CONTENT MESSAGE: {content}")
                    
                    # Look for question patterns in content
                    question_patterns = ["?", "please", "enter", "input", "choose", "select"]
                    if any(pattern in content.lower() for pattern in question_patterns):
                        print(f"❓ POSSIBLE USER QUESTION DETECTED in content", file=sys.stderr)
                        log_to_file(f"🚨 POSSIBLE USER QUESTION: {content}", "ALERT")
                        
                        # Log the full chat message that's prompting the user
                        log_to_file(f"🗨️ FULL CHAT PROMPT MESSAGE: {content}", "CHAT_MESSAGE")
            
            # Enhanced content extraction for different message types
            params = msg.get("params", {})
            
            # Check for text content in various message formats
            text_content = ""
            if "text" in params:
                text_content = params.get("text", "")
            elif "messages" in params:
                messages = params.get("messages", [])
                for message in messages:
                    if isinstance(message, dict):
                        if "content" in message:
                            content_obj = message.get("content", {})
                            if isinstance(content_obj, dict) and "text" in content_obj:
                                text_content += content_obj.get("text", "") + "\n"
                            elif isinstance(content_obj, str):
                                text_content += content_obj + "\n"
                        elif "text" in message:
                            text_content += message.get("text", "") + "\n"
            
            # If we found text content, check for chat prompts
            if text_content:
                text_lower = text_content.lower()
                log_to_file(f"EXTRACTED TEXT CONTENT: {text_content[:500]}...", "TEXT_CONTENT")
                
                # Check for chat prompt patterns in extracted text
                for pattern in chat_prompt_patterns:
                    if pattern in text_lower:
                        print(f"💬 CHAT PROMPT IN TEXT: '{pattern}' found", file=sys.stderr)
                        log_to_file(f"🚨 CHAT PROMPT IN TEXT: '{pattern}' detected", "CHAT_PROMPT")
                        log_to_file(f"🗨️ FULL PROMPT TEXT: {text_content}", "CHAT_MESSAGE")
                        break
                
                # Check for question indicators in text
                if "?" in text_content or any(word in text_lower for word in ["please", "enter", "input", "choose", "select", "confirm"]):
                    log_to_file(f"🚨 QUESTION DETECTED IN TEXT CONTENT", "CHAT_PROMPT")
                    log_to_file(f"🗨️ QUESTION TEXT: {text_content}", "CHAT_MESSAGE")
            
            # Track execution flow
            if method == "tools/call":
                tool_name = msg.get("params", {}).get("name", "unknown")
                print(f"🛠️ Tool called: {tool_name}", file=sys.stderr)
                log_to_file(f"TOOL CALLED: {tool_name}")
                
                # Detect if this is during a run_full_execution
                if tool_name == "run_full_execution":
                    print(f"🚀 FULL EXECUTION STARTED - Now monitoring for user interactions", file=sys.stderr)
                    log_to_file("🚀 FULL EXECUTION STARTED - Enhanced monitoring active", "EXECUTION")
                    executor.add_to_history("Monitoring started", "Watching for user prompts during execution")
            
            # Enhanced user interaction detection
            params = msg.get("params", {})
            
            # Check for sampling requests (AI asking questions)
            if method == "sampling/createMessage":
                print(f"🧠 AI SAMPLING REQUEST detected", file=sys.stderr)
                log_to_file("🧠 AI SAMPLING REQUEST detected", "AI_ACTIVITY")
                
                messages = params.get("messages", [])
                for message in messages:
                    content = message.get("content", {})
                    if isinstance(content, dict):
                        text = content.get("text", "")
                    else:
                        text = str(content)
                    
                    log_to_file(f"AI MESSAGE CONTENT: {text}", "AI_ACTIVITY")
                    
                    if "?" in text or any(word in text.lower() for word in ["ask", "input", "enter", "provide"]):
                        print(f"❓ AI ASKING QUESTION: {text[:200]}...", file=sys.stderr)
                        log_to_file(f"🚨 AI ASKING QUESTION: {text}", "ALERT")
            
            # Check for user responses
            if "response" in msg_str or "answer" in msg_str:
                print(f"💭 Possible user response detected", file=sys.stderr)
                log_to_file("💭 Possible user response detected", "USER_ACTIVITY")
            
            # Log message size for debugging
            if len(msg_str) > 1000:
                print(f"📏 Large message detected: {len(msg_str)} chars", file=sys.stderr)
                log_to_file(f"📏 Large message detected: {len(msg_str)} chars", "DEBUG")
            
            # Log summary of detection results
            if chat_prompt_detected:
                log_to_file(f"🚨 SUMMARY: CHAT PROMPT detected via '{detected_chat_pattern}' in {method} message", "SUMMARY")
            elif user_interaction_detected:
                log_to_file(f"🚨 SUMMARY: User interaction detected via '{detected_indicator}' in {method} message", "SUMMARY")
            else:
                log_to_file(f"✅ SUMMARY: No user interaction detected in {method} message", "DEBUG")
            # ===== END MESSAGE INTERCEPTION =====
            
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
                
                if tool_name == "get_current_state":
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
                    # Reset execution and start fresh
                    log_to_file("🚀 RUN_FULL_EXECUTION CALLED - Starting comprehensive execution", "EXECUTION")
                    executor.clear_cache()
                    
                    # Get all steps from instructions
                    instructions_data = json.loads(executor.instructions_file.read_text()) if executor.instructions_file.exists() else {}
                    steps = instructions_data.get("steps", [])
                    
                    if not steps:
                        log_to_file("❌ No steps found in instructions file", "ERROR")
                        send_mcp({
                            "jsonrpc": "2.0",
                            "id": msg.get("id"),
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "❌ No steps found in instructions file. Please ensure instructions.json exists with proper step definitions."
                                    }
                                ],
                                "isError": True
                            }
                        })
                    else:
                        # Provide all steps as a comprehensive execution plan
                        goal = instructions_data.get("goal", "Complete the instructions")
                        description = instructions_data.get("description", "Instruction Execution")
                        
                        execution_plan = f"""# {description}

## Goal: {goal}

## Full Execution Plan - Execute All Steps:

"""
                        
                        for step in steps:
                            step_num = step.get("step", 0)
                            step_desc = step.get("description", "")
                            execution_plan += f"""**STEP {step_num}:** {step_desc}

"""
                        
                        execution_plan += f"""
**YOUR TASK:** Execute all {len(steps)} steps above in sequence using your available tools.

**AVAILABLE TOOLS:**
- File operations (read_file, write, search_replace, etc.)
- Terminal commands (run_terminal_cmd)
- Web browser control (for opening files)
- Any other tools you have access to

**EXECUTION APPROACH:**
1. Read through all steps to understand the complete workflow
2. Execute each step in order
3. Verify completion of each step before moving to the next
4. Report progress as you complete each step

**IMPORTANT:** Execute the actual steps using real tools - do not simulate or skip any steps.

Begin execution now with Step 1."""

                        # Mark execution as started
                        executor.add_to_history("Full execution started", f"Executing {len(steps)} steps")
                        
                        # Log the execution plan
                        log_to_file(f"✅ EXECUTION PLAN CREATED: {len(steps)} steps for goal: {goal}", "EXECUTION")
                        log_to_file(f"EXECUTION PLAN CONTENT:\n{execution_plan}", "EXECUTION")
                        
                        send_mcp({
                            "jsonrpc": "2.0",
                            "id": msg.get("id"),
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": execution_plan
                                    }
                                ],
                                "isError": False
                            }
                        })
                        
                        log_to_file("📤 EXECUTION PLAN SENT TO CURSOR - Now monitoring for user interactions", "EXECUTION")
                    
                elif tool_name == "clear_cache":
                    # Clear cache and reload instructions
                    log_to_file("🧹 CLEAR_CACHE CALLED - Preparing for fresh execution monitoring", "EXECUTION")
                    executor.clear_cache()
                    
                    send_mcp({
                        "jsonrpc": "2.0",
                        "id": msg.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Cache cleared, log file emptied, and instructions reloaded successfully. Ready for fresh execution monitoring."
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
            log_to_file(f"❌ ERROR processing message: {str(e)}", "ERROR")
            if "msg" in locals():
                log_to_file(f"ERROR MESSAGE CONTENT: {json.dumps(msg, indent=2)}", "ERROR")
            
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