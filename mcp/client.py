"""
Groq + MCP Client for Can You Pi?
Real-time, fast-paced Pi digit verification
"""

import os
import json
import sys
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))
from server import MCP_TOOLS, execute_tool

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def chat_with_ai(user_message: str, conversation_history: list) -> tuple[str, list]:
    """
    Send message to Groq and handle MCP tool calls
    
    Args:
        user_message: User's message
        conversation_history: Conversation history
    
    Returns:
        Tuple of (AI response, updated history)
    """
    # Add user message
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Call Groq
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation_history,
        tools=MCP_TOOLS,
        tool_choice="auto",
        max_tokens=1500,
        temperature=0.7
    )
    
    message = response.choices[0].message
    
    # Handle tool calls
    if message.tool_calls:
        conversation_history.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        })
        
        # Execute tools
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            print(f"\n🔧 {tool_name}({json.dumps(arguments, separators=(',', ':'))})")
            
            # Execute MCP tool
            tool_result = execute_tool(tool_name, arguments)
            
            # Add to history
            conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })
        
        # Get final response
        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=conversation_history,
            max_tokens=1500,
            temperature=0.7
        )
        
        ai_message = final_response.choices[0].message.content
    else:
        ai_message = message.content
    
    # Add to history
    conversation_history.append({
        "role": "assistant",
        "content": ai_message
    })
    
    return ai_message, conversation_history


def main():
    """Main game loop"""
    print("=" * 70)
    print("🥧  Can You Pi? - Real-Time Edition")
    print("=" * 70)
    print("\n⚡ FAST-PACED MODE: Say digits rapid-fire!")
    print("\nHow to play:")
    print("  • Say: 'Start a game'")
    print("  • Then say Pi digits: '3.14159265358979323846...'")
    print("  • AI verifies in real-time and stops at first mistake!")
    print("\nExamples:")
    print("  You: 'Start'")
    print("  You: '3.14159265'")
    print("  You: '35897932384626' (continue)")
    print("  You: 'Give me a hint for next 5 digits'")
    print("\nType 'quit' to exit\n")
    
    # System prompt
    conversation_history = [
        {
            "role": "system",
            "content": """
                You are a Pi memorization game assistant. 

                IMPORTANT INSTRUCTIONS:
                1. When user wants to start, use start_pi_game
                2. When user says a sequence of digits (like "3.14159" or "14159265"), use verify_pi_sequence to check them
                3. The verify_pi_sequence tool checks ALL digits at once and tells you where the first mistake is
                4. Be encouraging and energetic! This is fast-paced!
                5. When they get digits right, celebrate briefly then prompt for more
                6. When they're wrong, tell them exactly where and what the right digit was

                Remember: Users will say multiple digits at once like "3.1415926535" - use verify_pi_sequence for this!
            """
        }
    ]
    
    print("AI: Hey! Ready to test your Pi memory? Say 'start' to begin! 🎯\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for playing!\n")
                break
            
            # Get AI response
            ai_response, conversation_history = chat_with_ai(user_input, conversation_history)
            
            print(f"\nAI: {ai_response}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Bye!\n")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found!")
        print("\nCreate a .env file in the project root:")
        print("GROQ_API_KEY=your_key_here\n")
    else:
        main()