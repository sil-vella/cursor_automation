#!/usr/bin/env python3
"""
Test script for interruption handling in the instruction executor.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from instruction_executor import ExecutionInterruptionHandler, InstructionExecutor

def test_interruption_detection():
    """Test the interruption detection functionality."""
    print("🧪 Testing interruption detection...")
    
    handler = ExecutionInterruptionHandler()
    
    # Test cases
    test_messages = [
        "Do you want to continue? (y/n)",
        "Are you sure you want to delete this file?",
        "File already exists. Overwrite? (y/n)",
        "This action cannot be undone. Proceed?",
        "Permission denied. Continue anyway?",
        "Normal execution message",
        "Type 'y' to confirm deletion",
        "Press Enter to continue"
    ]
    
    for message in test_messages:
        detected = handler.detect_interruption(message)
        status = "✅ DETECTED" if detected else "❌ NOT DETECTED"
        print(f"{status}: {message}")
        
        if detected:
            response = handler.handle_interruption()
            print(f"   🔄 Auto-response: {response.strip()}")
        
        handler.reset()
    
    print("\n✅ Interruption detection test completed!")

def test_executor_with_interruptions():
    """Test the instruction executor with interruption handling."""
    print("\n🧪 Testing instruction executor with interruptions...")
    
    executor = InstructionExecutor()
    
    # Test timeout detection
    print(f"⏰ Timeout setting: {executor.execution_timeout} seconds")
    print(f"⏰ Auto-confirm: {executor.interruption_handler.auto_confirm}")
    
    # Test interruption handling
    test_message = "Do you want to delete this file? (y/n)"
    response = executor.handle_execution_interruption(test_message)
    print(f"🔄 Interruption response: {response.strip()}")
    
    print("\n✅ Executor interruption test completed!")

if __name__ == "__main__":
    test_interruption_detection()
    test_executor_with_interruptions() 