"""
MCP Server for Can You Pi?
Supports real-time batch digit verification
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

# Add parent directory to path to import game_logic
sys.path.append(str(Path(__file__).parent.parent))
from game_logic import Game

# Store active games (in-memory)
games: Dict[str, Game] = {}


def start_pi_game(mode: str = "standard", start_position: int = 1) -> dict:
    """
    Start a new Pi memorization game
    
    Args:
        mode: "standard" (from beginning) or "custom" (from specific position)
        start_position: Starting position for custom mode (1-indexed)
    
    Returns:
        Dictionary with game_id and status
    """
    game = Game()
    
    if mode == "custom":
        game.current_index = start_position - 1
    
    game_id = str(uuid4())
    games[game_id] = game
    
    return {
        "game_id": game_id,
        "mode": mode,
        "current_position": game.current_index + 1,
        "message": f"Game started! Say the digits of Pi: 3.1415...",
        "total_digits_available": len(game.pi_decimals)
    }


def verify_pi_sequence(game_id: str, sequence: str) -> dict:
    """
    Verify a sequence of Pi digits in real-time
    Stops at the first wrong digit
    
    Args:
        game_id: The game ID from start_pi_game
        sequence: String of digits to verify (e.g., "14159265")
    
    Returns:
        Dictionary with verification results
    """
    if game_id not in games:
        return {
            "error": "Game not found. Start a new game first.",
            "game_id": game_id
        }
    
    game = games[game_id]
    
    if game.is_game_over:
        return {
            "error": "Game is already over.",
            "game_id": game_id,
            "final_score": game.current_index
        }
    
    # Clean the sequence (remove spaces, "3.", etc.)
    clean_sequence = sequence.replace(" ", "").replace(".", "")
    
    # Remove leading "3" if present
    if clean_sequence.startswith("3"):
        clean_sequence = clean_sequence[1:]
    
    if not clean_sequence:
        return {
            "error": "No digits provided",
            "game_id": game_id
        }
    
    # Verify each digit
    results = []
    correct_count = 0
    first_wrong_position = None
    
    for i, digit in enumerate(clean_sequence):
        if not digit.isdigit():
            continue  # Skip non-digits
        
        is_correct, expected_digit = game.check_input(digit)
        
        position = game.current_index  # Position before this guess
        
        results.append({
            "digit": digit,
            "position": position + 1,  # 1-indexed for display
            "correct": is_correct
        })
        
        if is_correct:
            correct_count += 1
        else:
            first_wrong_position = position
            # Game is over, stop checking
            return {
                "game_id": game_id,
                "sequence_provided": sequence,
                "digits_checked": len(results),
                "correct_count": correct_count,
                "all_correct": False,
                "game_over": True,
                "wrong_at_position": first_wrong_position + 1,
                "expected_digit": expected_digit,
                "got_digit": digit,
                "final_score": game.current_index,
                "correct_sequence": f"3.{game.pi_decimals[:game.current_index]}",
                "message": f"Wrong at position {first_wrong_position + 1}! You said '{digit}', but it should be '{expected_digit}'. Final score: {game.current_index}"
            }
    
    # All digits were correct!
    return {
        "game_id": game_id,
        "sequence_provided": sequence,
        "digits_checked": len(results),
        "correct_count": correct_count,
        "all_correct": True,
        "game_over": False,
        "current_score": game.current_index,
        "current_sequence": f"3.{game.pi_decimals[:game.current_index]}",
        "message": f"All {correct_count} digits correct! Current score: {game.current_index}. Keep going!"
    }


def get_pi_hint(game_id: str, count: int = 1) -> dict:
    """
    Get hint(s) for the next digit(s)
    
    Args:
        game_id: The game ID
        count: Number of digits to show (default 1)
    
    Returns:
        Dictionary with the hint
    """
    if game_id not in games:
        return {"error": "Game not found."}
    
    game = games[game_id]
    
    if game.is_game_over:
        return {"error": "Game is over."}
    
    if game.is_complete():
        return {"message": "You've completed all digits!"}
    
    # Get next N digits
    start = game.current_index
    end = min(start + count, len(game.pi_decimals))
    next_digits = game.pi_decimals[start:end]
    
    return {
        "game_id": game_id,
        "hint": next_digits,
        "start_position": start + 1,
        "count": len(next_digits),
        "message": f"Next {len(next_digits)} digit(s): {next_digits}"
    }


def get_game_status(game_id: str) -> dict:
    """
    Get current game status
    
    Args:
        game_id: The game ID
    
    Returns:
        Dictionary with game statistics
    """
    if game_id not in games:
        return {"error": "Game not found."}
    
    game = games[game_id]
    
    return {
        "game_id": game_id,
        "current_position": game.current_index + 1,
        "score": game.current_index,
        "game_over": game.is_game_over,
        "sequence_so_far": f"3.{game.pi_decimals[:game.current_index]}",
        "next_10_digits": game.pi_decimals[game.current_index:game.current_index + 10] if not game.is_game_over else "",
        "total_digits_available": len(game.pi_decimals)
    }


def end_game(game_id: str) -> dict:
    """
    End a game and clean up
    
    Args:
        game_id: The game ID
    
    Returns:
        Dictionary with final stats
    """
    if game_id not in games:
        return {"error": "Game not found."}
    
    game = games[game_id]
    
    response = {
        "game_id": game_id,
        "final_score": game.current_index,
        "sequence": f"3.{game.pi_decimals[:game.current_index]}",
        "message": f"Game ended. You recalled {game.current_index} digits!"
    }
    
    del games[game_id]
    
    return response


# Tool definitions for Groq
MCP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "start_pi_game",
            "description": "Start a new Pi memorization game",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["standard", "custom"],
                        "default": "standard"
                    },
                    "start_position": {
                        "type": "integer",
                        "minimum": 1,
                        "default": 1
                    }
                },
                "required" :[]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verify_pi_sequence",
            "description": "Verify a sequence of Pi digits. Checks each digit in order and stops at the first mistake. User can say '3.14159...' all at once.",
            "parameters": {
                "type": "object",
                "properties": {
                    "game_id": {
                        "type": "string",
                        "description": "The game ID"
                    },
                    "sequence": {
                        "type": "string",
                        "description": "The sequence of digits to verify (e.g., '3.14159' or '14159265')"
                    }
                },
                "required": ["game_id", "sequence"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pi_hint",
            "description": "Get the next N digits as a hint",
            "parameters": {
                "type": "object",
                "properties": {
                    "game_id": {"type": "string"},
                    "count": {
                        "type": "integer",
                        "minimum": 1,
                        "default": 1,
                        "description": "Number of digits to show"
                    }
                },
                "required": ["game_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_game_status",
            "description": "Get current game status and score",
            "parameters": {
                "type": "object",
                "properties": {
                    "game_id": {"type": "string"}
                },
                "required": ["game_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "end_game",
            "description": "End the game",
            "parameters": {
                "type": "object",
                "properties": {
                    "game_id": {"type": "string"}
                },
                "required": ["game_id"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Execute an MCP tool by name"""
    if tool_name == "start_pi_game":
        return start_pi_game(**arguments)
    elif tool_name == "verify_pi_sequence":
        return verify_pi_sequence(**arguments)
    elif tool_name == "get_pi_hint":
        return get_pi_hint(**arguments)
    elif tool_name == "get_game_status":
        return get_game_status(**arguments)
    elif tool_name == "end_game":
        return end_game(**arguments)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


if __name__ == "__main__":
    # Test the tools
    print("=" * 70)
    print("Testing MCP Server - Real-Time Verification")
    print("=" * 70)
    
    # Start game
    print("\n1. Starting game...")
    result = start_pi_game()
    print(json.dumps(result, indent=2))
    game_id = result["game_id"]
    
    # Test real-time verification
    print("\n2. Testing real-time: '3.14159265'")
    result = verify_pi_sequence(game_id, "3.14159265")
    print(json.dumps(result, indent=2))
    
    # Continue
    print("\n3. Continue: '35897932'")
    result = verify_pi_sequence(game_id, "35897932")
    print(json.dumps(result, indent=2))
    
    # Wrong digit
    print("\n4. Wrong digit: '99999'")
    result = verify_pi_sequence(game_id, "99999")
    print(json.dumps(result, indent=2))
    
    print("\n" + "=" * 70)