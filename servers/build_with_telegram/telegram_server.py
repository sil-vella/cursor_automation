#!/usr/bin/env python3
"""
Telegram Server MCP - Handles socket communication with build scripts
"""

import socket
import threading
import json
import time
import os
import sys
import asyncio
import subprocess
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

class TelegramServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.clients = []
        self.bot = None
        self.app = None
        self.current_build_id = None
        self.build_sessions = {}
        self.server_socket = None
        self.server_running = False
        
    def start_bot(self):
        """Start the Telegram bot"""
        if not BOT_TOKEN or not CHAT_ID:
            print("❌ Telegram credentials not configured", file=sys.stderr)
            return False
            
        try:
            self.app = ApplicationBuilder().token(BOT_TOKEN).build()
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_telegram_message))
            
            print("✅ Telegram bot initialized", file=sys.stderr)
            # Start bot in background thread with proper async handling
            bot_thread = threading.Thread(target=self._run_bot)
            bot_thread.daemon = True
            bot_thread.start()
            return True
            
        except Exception as e:
            print(f"❌ Bot failed: {e}", file=sys.stderr)
            return False
    
    def _run_bot(self):
        """Run the bot in a separate thread"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Use asyncio.run() to properly handle the event loop
            async def run_bot():
                await self.app.initialize()
                await self.app.start()
                await self.app.updater.start_polling()
                # Keep the bot running
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    await self.app.stop()
                    await self.app.shutdown()
            
            loop.run_until_complete(run_bot())
        except Exception as e:
            print(f"❌ Bot polling failed: {e}", file=sys.stderr)
    
    async def handle_telegram_message(self, update, context):
        """Handle incoming Telegram messages"""
        message_text = update.message.text.strip()
        chat_id = update.message.chat_id
        
        print(f"📥 Telegram: {message_text}", file=sys.stderr)
        
        if message_text.lower() == "help":
            help_text = """
🤖 Build with Telegram Bot

Commands:
• `help` - Show this help

Usage:
1. Reply to bot questions about your build
2. Get real-time build updates
            """
            await update.message.reply_text(help_text.strip())
            
        elif self.current_build_id and message_text:
            # Forward message to current build session
            await self.forward_to_build(message_text, chat_id)
            
        else:
            await update.message.reply_text("❌ No active build session.")
    

    
    async def forward_to_build(self, message, chat_id):
        """Forward Telegram message to active build session"""
        if self.current_build_id and self.current_build_id in self.build_sessions:
            session = self.build_sessions[self.current_build_id]
            
            # Send message to build script via socket
            try:
                response = {
                    "type": "user_response",
                    "message": message,
                    "chat_id": chat_id
                }
                session['socket'].send(json.dumps(response).encode())
                await self.send_telegram_message("✅ Response sent to build script")
            except Exception as e:
                await self.send_telegram_message(f"❌ Failed to send response: {e}")
    
    async def send_telegram_message(self, message):
        """Send message to Telegram"""
        if self.app:
            try:
                await self.app.bot.send_message(chat_id=CHAT_ID, text=message)
            except Exception as e:
                print(f"❌ Failed to send Telegram message: {e}", file=sys.stderr)
    
    def handle_client(self, client_socket, address):
        """Handle individual client connections"""
        print(f"🔌 Client connected: {address}", file=sys.stderr)
        
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                message = json.loads(data.decode())
                print(f"📨 From build script: {message}", file=sys.stderr)
                
                # Handle different message types
                if message.get('type') == 'build_start':
                    self.current_build_id = message.get('build_id')
                    self.build_sessions[self.current_build_id] = {
                        'socket': client_socket,
                        'status': 'running'
                    }
                    asyncio.run(self.send_telegram_message(f"🚀 Build started: {message.get('description', 'Unknown')}"))
                    
                elif message.get('type') == 'build_progress':
                    asyncio.run(self.send_telegram_message(f"📊 Progress: {message.get('message', '')}"))
                    
                elif message.get('type') == 'build_question':
                    asyncio.run(self.send_telegram_message(f"❓ Question: {message.get('message', '')}"))
                    
                elif message.get('type') == 'build_error':
                    asyncio.run(self.send_telegram_message(f"❌ Error: {message.get('message', '')}"))
                    
                elif message.get('type') == 'build_complete':
                    asyncio.run(self.send_telegram_message(f"✅ Build complete: {message.get('message', '')}"))
                    if self.current_build_id in self.build_sessions:
                        del self.build_sessions[self.current_build_id]
                    self.current_build_id = None
                    
        except Exception as e:
            print(f"❌ Client error: {e}", file=sys.stderr)
        finally:
            client_socket.close()
            print(f"🔌 Client disconnected: {address}", file=sys.stderr)
    
    def start_server(self):
        """Start the socket server"""
        if self.server_running:
            print("✅ Telegram server already running", file=sys.stderr)
            return True
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_running = True
            
            print(f"🚀 Telegram server started on {self.host}:{self.port}", file=sys.stderr)
            
            # Start bot
            if not self.start_bot():
                return False
            
            # Start server in background thread
            server_thread = threading.Thread(target=self._run_server)
            server_thread.daemon = True
            server_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Server error: {e}", file=sys.stderr)
            return False
    
    def _run_server(self):
        """Run the server in a separate thread"""
        try:
            while self.server_running:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
        except Exception as e:
            print(f"❌ Server thread error: {e}", file=sys.stderr)
    
    def stop_server(self):
        """Stop the server"""
        self.server_running = False
        if self.server_socket:
            self.server_socket.close()
        print("🛑 Telegram server stopped", file=sys.stderr)

def send_mcp(msg):
    """Send MCP message"""
    print(json.dumps(msg), flush=True)

async def mcp_server():
    """Main MCP server loop"""
    global telegram_server_instance
    
    print("🚀 Starting Telegram MCP server...", file=sys.stderr)
    print("✅ MCP server ready to receive tool calls", file=sys.stderr)
    print("💡 Telegram server will auto-start on initialization", file=sys.stderr)
    
    # MCP server loop
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            
            # Handle initialization
            if msg.get("method") == "initialize":
                # Auto-start Telegram server during initialization
                print("🚀 Auto-starting Telegram server...", file=sys.stderr)
                telegram_server_instance = TelegramServer(host="localhost", port=5000)
                server_started = telegram_server_instance.start_server()
                
                if server_started:
                    print("✅ Telegram server auto-started successfully", file=sys.stderr)
                else:
                    print("⚠️ Failed to auto-start Telegram server (check BOT_TOKEN and CHAT_ID)", file=sys.stderr)
                
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
                            "name": "telegram-server",
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
                                "name": "start_telegram_server",
                                "title": "Start Telegram Server",
                                "description": "Start the Telegram server for build communication",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "host": {
                                            "type": "string",
                                            "description": "Host address (default: localhost)"
                                        },
                                        "port": {
                                            "type": "integer",
                                            "description": "Port number (default: 5000)"
                                        }
                                    }
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
                
                if tool_name == "start_telegram_server":
                    host = arguments.get("host", "localhost")
                    port = arguments.get("port", 5000)
                    
                    # Create and start Telegram server
                    telegram_server_instance = TelegramServer(host=host, port=port)
                    success = telegram_server_instance.start_server()
                    
                    if success:
                        send_mcp({
                            "jsonrpc": "2.0",
                            "id": msg.get("id"),
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"✅ Telegram server started successfully on {host}:{port}"
                                    }
                                ],
                                "isError": False
                            }
                        })
                    else:
                        send_mcp({
                            "jsonrpc": "2.0",
                            "id": msg.get("id"),
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"❌ Failed to start Telegram server on {host}:{port}. Check BOT_TOKEN and CHAT_ID environment variables."
                                    }
                                ],
                                "isError": True
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
    # Run the MCP server
    asyncio.run(mcp_server()) 