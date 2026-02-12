from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from typing import List, Dict, Any

import random
import sys
import os
import json
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))
from game_logic import Game

# Import MCP server functions
sys.path.append(str(Path(__file__).parent.parent / "mcp"))
from server import MCP_TOOLS, execute_tool

load_dotenv()

router = APIRouter()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Store chat conversations (in-memory)
conversations: Dict[str, List[Dict[str, Any]]] = {}

# Chat Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    tool_calls: List[Dict[str, Any]] = []

class StartGameRequest(BaseModel):
    mode: int = 1  # 1: Standard, 2: Custom
    start_position: int = 1  # Used for Custom Mode (1-indexed)

class StartGameResponse(BaseModel):
    game_id: str
    mode: str
    current_position: int
    message: str
    total_digits_available: int

games = {} # In-memory storage for active games

# ============================================================
# AI Chat Endpoints (MCP Integration)
# ============================================================

@router.post("/chat", response_model=ChatResponse)
def chat_with_ai(request: ChatRequest):
    """
    Chat with AI assistant that can play Pi games via MCP tools.
    The AI can start games, verify sequences, give hints, and more.
    """
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    
    # Get or create conversation
    conversation_id = request.conversation_id or str(uuid4())
    
    if conversation_id not in conversations:
        # Initialize with system prompt
        conversations[conversation_id] = [
            {
                "role": "system",
                "content": """
                    You are a Pi memorization game assistant. 

                    GAME FLOW:
                    1. When user wants to start: call start_pi_game
                    2. When user says digits: call verify_pi_sequence
                    3. When all_correct=true: Celebrate and ask for more digits
                    4. When all_correct=false: Tell them the mistake, current score, and ask if they want to continue or restart
                    5. When user says "continue": Just ask them for the next digits (DON'T start new game)
                    6. When user says "new game" or "restart": call start_pi_game

                    KEY RULES:
                    - verify_pi_sequence always works - there's no "game over" state
                    - "continue" means keep playing from current position - just prompt for next digits
                    - Only call start_pi_game when explicitly starting/restarting
                    - Be energetic and brief between verifications
                    - After wrong answer: "Wrong at position X! You said 'Y' but it's 'Z'. Score: N. Continue or new game?"
                    - After correct: "Nice! Score: N. Keep going!"

                    Example flow:
                    User: "3.14159"
                    AI: [verify] "Correct! Score: 5. Next digits?"
                    User: "99999"
                    AI: [verify] "Wrong at position 6! You said '9' but it's '2'. Score: 5. Continue or restart?"
                    User: "continue"
                    AI: "You're at 3.14159. What comes next?"
                    User: "265358"
                    AI: [verify] "Perfect! Score: 11. More!"
                    """
            }
        ]
    
    conversation_history = conversations[conversation_id]
    
    # Add user message
    conversation_history.append({
        "role": "user",
        "content": request.message
    })
    
    # Call Groq with MCP tools
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=conversation_history,
            tools=MCP_TOOLS,
            tool_choice="auto",
            max_tokens=1500,
            temperature=0.7
        )
        
        message = response.choices[0].message
        tool_calls_info = []
        
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
                
                # Execute MCP tool
                tool_result = execute_tool(tool_name, arguments)
                
                tool_calls_info.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": tool_result
                })
                
                # Add to history
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                })
            
            # Get final response
            final_response = groq_client.chat.completions.create(
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
        
        # Update stored conversation
        conversations[conversation_id] = conversation_history
        
        return ChatResponse(
            conversation_id=conversation_id,
            message=ai_message,
            tool_calls=tool_calls_info
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{conversation_id}/history")
def get_conversation_history(conversation_id: str):
    """
    Get the conversation history for a specific conversation.
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Filter to only return user and assistant messages (not system/tool)
    history = [
        {"role": msg["role"], "content": msg.get("content", "")}
        for msg in conversations[conversation_id]
        if msg["role"] in ["user", "assistant"]
    ]
    
    return {"conversation_id": conversation_id, "history": history}


@router.delete("/chat/{conversation_id}")
def delete_conversation(conversation_id: str):
    """
    Delete a conversation.
    """
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"message": "Conversation deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")


# ============================================================
# Original Game Endpoints
# ============================================================

@router.post("/start", response_model=StartGameResponse)
def start_game(request: StartGameRequest):
    """
    Start a new Pi memorization game.
    Mode 1: Standard (starts from beginning)
    Mode 2: Custom (starts from specified position)
    """
    game = Game()
    
    mode_name = "standard"
    if request.mode == 2: 
        game.current_index = request.start_position - 1
        mode_name = "custom"
    
    game_id = str(uuid4())
    games[game_id] = game

    return StartGameResponse(
        game_id=game_id,
        mode=mode_name,
        current_position=game.current_index + 1,
        message=f"Game started! Say the digits of Pi: 3.1415...",
        total_digits_available=len(game.pi_decimals)
    )
    
class GuessRequest(BaseModel):
    input: str  

class GuessResponse(BaseModel):
    correct: bool
    expected_digit: str | None = None
    current_index: int
    game_over: bool
    message: str

@router.post("/game/{game_id}/play", response_model=GuessResponse)
def play_turn(game_id: str, request: GuessRequest):
    game = games.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    user_input = request.input

    if game.is_exit(user_input):
        return GuessResponse(
            correct=False,
            current_index=game.current_index,
            game_over=True,
            message="Game exited"
        )

    if not game.is_valid_input(user_input):
        raise HTTPException(status_code=400, detail="Input must be a single digit")

    is_correct, expected_digit = game.check_input(user_input)

    if game.is_complete():
        return GuessResponse(
            correct=True,
            current_index=game.current_index,
            game_over=True,
            message="You completed all digits!"
        )

    return GuessResponse(
        correct=is_correct,
        expected_digit=expected_digit,
        current_index=game.current_index,
        game_over=game.is_game_over,
        message="Correct!" if is_correct else f"Wrong! Expected {expected_digit}"
    )

# Batch Verification Models
class VerifySequenceRequest(BaseModel):
    sequence: str

class VerifySequenceResponse(BaseModel):
    game_id: str
    sequence_provided: str
    digits_checked: int
    correct_count: int
    all_correct: bool
    current_score: int = 0
    wrong_at_position: int | None = None
    expected_digit: str | None = None
    got_digit: str | None = None
    correct_sequence: str | None = None
    message: str

@router.post("/game/{game_id}/verify", response_model=VerifySequenceResponse)
def verify_sequence(game_id: str, request: VerifySequenceRequest):
    """
    Verify a batch of Pi digits at once.
    Stops at the first wrong digit and returns detailed feedback.
    """
    game = games.get(game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Clean the sequence (remove spaces, "3.", etc.)
    clean_sequence = request.sequence.replace(" ", "").replace(".", "")
    
    # Remove leading "3" if present
    if clean_sequence.startswith("3"):
        clean_sequence = clean_sequence[1:]
    
    if not clean_sequence:
        raise HTTPException(status_code=400, detail="No digits provided")
    
    # Verify each digit
    correct_count = 0
    first_wrong_position = None
    
    for i, digit in enumerate(clean_sequence):
        if not digit.isdigit():
            continue  # Skip non-digits
        
        is_correct, expected_digit = game.check_input(digit)
        
        if is_correct:
            correct_count += 1
        else:
            first_wrong_position = game.current_index - 1
            # Stop checking at first wrong digit
            return VerifySequenceResponse(
                game_id=game_id,
                sequence_provided=request.sequence,
                digits_checked=i + 1,
                correct_count=correct_count,
                all_correct=False,
                wrong_at_position=first_wrong_position + 1,
                expected_digit=expected_digit,
                got_digit=digit,
                current_score=game.current_index,
                correct_sequence=f"3.{game.pi_decimals[:game.current_index]}",
                message=f"Wrong at position {first_wrong_position + 1}! You said '{digit}', but it should be '{expected_digit}'. Current score: {game.current_index}"
            )
    
    # All digits were correct!
    return VerifySequenceResponse(
        game_id=game_id,
        sequence_provided=request.sequence,
        digits_checked=len([d for d in clean_sequence if d.isdigit()]),
        correct_count=correct_count,
        all_correct=True,
        current_score=game.current_index,
        message=f"All {correct_count} digits correct! Current score: {game.current_index}. Keep going!"
    )

# Game Status Models
class GameStatusResponse(BaseModel):
    game_id: str
    current_position: int
    score: int
    sequence_so_far: str
    next_10_digits: str
    total_digits_available: int

@router.get("/game/{game_id}/status", response_model=GameStatusResponse)
def get_game_status(game_id: str):
    """
    Get current game status including score and progress.
    """
    game = games.get(game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return GameStatusResponse(
        game_id=game_id,
        current_position=game.current_index + 1,
        score=game.current_index,
        sequence_so_far=f"3.{game.pi_decimals[:game.current_index]}",
        next_10_digits=game.pi_decimals[game.current_index:game.current_index + 10],
        total_digits_available=len(game.pi_decimals)
    )

# Hint Models
class HintResponse(BaseModel):
    game_id: str
    hint: str
    start_position: int
    count: int
    message: str

@router.get("/game/{game_id}/hint", response_model=HintResponse)
def get_hint(game_id: str, count: int = 1):
    """
    Get hint for the next N digits.
    Query parameter: count (default: 1)
    Example: GET /game/{game_id}/hint?count=5
    """
    game = games.get(game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.is_complete():
        raise HTTPException(status_code=400, detail="You've completed all digits!")
    
    if count < 1:
        raise HTTPException(status_code=400, detail="Count must be at least 1")
    
    # Get next N digits
    start = game.current_index
    end = min(start + count, len(game.pi_decimals))
    next_digits = game.pi_decimals[start:end]
    
    return HintResponse(
        game_id=game_id,
        hint=next_digits,
        start_position=start + 1,
        count=len(next_digits),
        message=f"Next {len(next_digits)} digit(s): {next_digits}"
    )

# End Game Models
class EndGameResponse(BaseModel):
    game_id: str
    final_score: int
    sequence: str
    message: str

@router.delete("/game/{game_id}")
def end_game(game_id: str):
    """
    End a game and clean up resources.
    Returns final statistics.
    """
    game = games.get(game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    response = EndGameResponse(
        game_id=game_id,
        final_score=game.current_index,
        sequence=f"3.{game.pi_decimals[:game.current_index]}",
        message=f"Game ended. You recalled {game.current_index} digits!"
    )
    
    # Clean up
    del games[game_id]
    
    return response

# Position Quiz Models and Endpoints
class DecimalGuessGame:
    def __init__(self, position: int, expected_digit: str):
        self.position = position
        self.expected_digit = expected_digit
        self.is_done = False

decimal_games = {}

class StartQuizRequest(BaseModel):
    position: int | None = None
    max_position: int = 100

class StartQuizResponse(BaseModel):
    quiz_id: str
    position: int
    message: str
    hint: str

@router.post("/quiz/start", response_model=StartQuizResponse)
def start_position_quiz(request: StartQuizRequest = StartQuizRequest()):
    """
    Start a position guessing quiz.
    Guess what digit is at a specific position in Pi.
    If position not provided, a random position (1 to max_position) is chosen.
    """
    game = Game()
    
    position = request.position
    if position is None:
        position = random.randint(1, request.max_position)
    
    # Validate position
    if position < 1 or position > len(game.pi_decimals):
        raise HTTPException(
            status_code=400, 
            detail=f"Position out of range. Must be between 1 and {len(game.pi_decimals)}"
        )
    
    expected_digit = game.pi_decimals[position - 1]
    decimal_game = DecimalGuessGame(position, expected_digit)
    
    quiz_id = str(uuid4())
    decimal_games[quiz_id] = decimal_game

    return StartQuizResponse(
        quiz_id=quiz_id,
        position=position,
        message=f"What is the {position}th decimal of Pi?",
        hint=f"Position {position} (after 3.)"
    )

class CheckGuessRequest(BaseModel):
    guess: str

class CheckGuessResponse(BaseModel):
    quiz_id: str
    position: int
    guess: str
    correct: bool
    expected_digit: str | None = None
    message: str

@router.post("/quiz/{quiz_id}/check", response_model=CheckGuessResponse)
def check_position_guess(quiz_id: str, request: CheckGuessRequest):
    """
    Check if the user's guess for a specific position is correct.
    """
    quiz = decimal_games.get(quiz_id)

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if quiz.is_done:
        raise HTTPException(status_code=400, detail="Quiz already completed")

    if not request.guess.isdigit() or len(request.guess) != 1:
        raise HTTPException(status_code=400, detail="Guess must be a single digit (0-9)")

    quiz.is_done = True

    if request.guess == quiz.expected_digit:
        return CheckGuessResponse(
            quiz_id=quiz_id,
            position=quiz.position,
            guess=request.guess,
            correct=True,
            message="Correct! Well done!"
        )
    
    return CheckGuessResponse(
        quiz_id=quiz_id,
        position=quiz.position,
        guess=request.guess,
        correct=False,
        expected_digit=quiz.expected_digit,
        message=f"Wrong! The digit at position {quiz.position} is {quiz.expected_digit}, not {request.guess}."
    )

