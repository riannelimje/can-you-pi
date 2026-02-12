"""
MCP Server for Can You Pi?
Supports real-time batch digit verification
"""

import json
import random
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
            # Stop checking at first wrong digit
            return {
                "game_id": game_id,
                "sequence_provided": sequence,
                "digits_checked": len(results),
                "correct_count": correct_count,
                "all_correct": False,
                "wrong_at_position": first_wrong_position + 1,
                "expected_digit": expected_digit,
                "got_digit": digit,
                "current_score": game.current_index,
                "correct_sequence": f"3.{game.pi_decimals[:game.current_index]}",
                "message": f"Wrong at position {first_wrong_position + 1}! You said '{digit}', but it should be '{expected_digit}'. Current score: {game.current_index}"
            }
    
    # All digits were correct!
    return {
        "game_id": game_id,
        "sequence_provided": sequence,
        "digits_checked": len(results),
        "correct_count": correct_count,
        "all_correct": True,
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
        "sequence_so_far": f"3.{game.pi_decimals[:game.current_index]}",
        "next_10_digits": game.pi_decimals[game.current_index:game.current_index + 10],
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


def guess_pi_position(position: int = None, max_position: int = 100) -> dict:
    """
    Start a position guessing quiz - guess what digit is at a specific position
    
    Args:
        position: Specific position to ask about (1-indexed). If None, random position chosen.
        max_position: Maximum position for random selection (default 100)
    
    Returns:
        Dictionary with quiz_id and the position to guess
    """
    game = Game()
    
    if position is None:
        position = random.randint(1, max_position)
    
    # Validate position
    if position < 1 or position > len(game.pi_decimals):
        return {
            "error": f"Position out of range. Must be between 1 and {len(game.pi_decimals)}"
        }
    
    quiz_id = str(uuid4())
    games[quiz_id] = game
    
    return {
        "quiz_id": quiz_id,
        "position": position,
        "message": f"What is the {position}th decimal of Pi?",
        "hint": f"Position {position} (after 3.)"
    }


def check_position_guess(quiz_id: str, guess: str, position: int) -> dict:
    """
    Check if the user's guess for a specific position is correct
    
    Args:
        quiz_id: The quiz ID from guess_pi_position
        guess: The user's digit guess
        position: The position being guessed (1-indexed)
    
    Returns:
        Dictionary with result and correct answer if wrong
    """
    if quiz_id not in games:
        return {"error": "Quiz not found. Start a new quiz first."}
    
    game = games[quiz_id]
    
    # Validate input
    if not guess.isdigit() or len(guess) != 1:
        return {
            "error": "Guess must be a single digit (0-9)",
            "quiz_id": quiz_id
        }
    
    # Check answer
    expected_digit = game.pi_decimals[position - 1]
    is_correct = guess == expected_digit
    
    if is_correct:
        return {
            "quiz_id": quiz_id,
            "position": position,
            "guess": guess,
            "correct": True,
            "message": "Correct! Well done!"
        }
    else:
        return {
            "quiz_id": quiz_id,
            "position": position,
            "guess": guess,
            "correct": False,
            "expected_digit": expected_digit,
            "message": f"Wrong! The digit at position {position} is {expected_digit}, not {guess}."
        }


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
    },
    {
        "type": "function",
        "function": {
            "name": "guess_pi_position",
            "description": "Start a position guessing quiz. User guesses what digit is at a specific position in Pi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "position": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Specific position to ask about (1-indexed). If not provided, random position is chosen."
                    },
                    "max_position": {
                        "type": "integer",
                        "minimum": 1,
                        "default": 100,
                        "description": "Maximum position for random selection (default 100)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_position_guess",
            "description": "Check if the user's guess for a specific position is correct",
            "parameters": {
                "type": "object",
                "properties": {
                    "quiz_id": {
                        "type": "string",
                        "description": "The quiz ID from guess_pi_position"
                    },
                    "guess": {
                        "type": "string",
                        "description": "The user's digit guess (single digit 0-9)"
                    },
                    "position": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "The position being guessed (1-indexed)"
                    }
                },
                "required": ["quiz_id", "guess", "position"]
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
    elif tool_name == "guess_pi_position":
        return guess_pi_position(**arguments)
    elif tool_name == "check_position_guess":
        return check_position_guess(**arguments)
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
    
    # Test position guessing quiz
    print("\n" + "=" * 70)
    print("Testing Position Guessing Quiz")
    print("=" * 70)
    
    print("\n5. Starting position quiz...")
    result = guess_pi_position()
    print(json.dumps(result, indent=2))
    quiz_id = result["quiz_id"]
    position = result["position"]
    
    print(f"\n6. Guessing wrong answer for position {position}...")
    result = check_position_guess(quiz_id, "9", position)
    print(json.dumps(result, indent=2))
    
    print(f"\n7. Starting new quiz at position 10...")
    result = guess_pi_position(position=10)
    print(json.dumps(result, indent=2))
    quiz_id2 = result["quiz_id"]
    
    print(f"\n8. Guessing correct answer (5) for position 10...")
    result = check_position_guess(quiz_id2, "5", 10)
    print(json.dumps(result, indent=2))
    
    print("\n" + "=" * 70)