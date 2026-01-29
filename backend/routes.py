from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4

import random
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from game_logic import Game

router = APIRouter()

class StartGameRequest(BaseModel):
    mode: int = 1  # 1: Standard, 2: Custom
    start_position: int = 0  # Used for Custom Mode

class StartGameResponse(BaseModel):
    game_id: str
    message: str
    start_position: int = 1

games = {} # In-memory storage for active games

@router.post("/start", response_model=StartGameResponse)
def start_game(request: StartGameRequest):
    game = Game()

    if request.mode == 2: 
        game.current_index = request.start_position - 1
    
    game_id = str(uuid4())
    games[game_id] = game

    return StartGameResponse(
        game_id=game_id,
        message=f"Game started in mode {request.mode}",
        start_position=game.current_index
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
    game_over: bool
    current_score: int = 0
    wrong_at_position: int | None = None
    expected_digit: str | None = None
    got_digit: str | None = None
    final_score: int | None = None
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
    
    if game.is_game_over:
        raise HTTPException(
            status_code=400, 
            detail=f"Game is already over. Final score: {game.current_index}"
        )
    
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
            # Game is over, stop checking
            return VerifySequenceResponse(
                game_id=game_id,
                sequence_provided=request.sequence,
                digits_checked=i + 1,
                correct_count=correct_count,
                all_correct=False,
                game_over=True,
                wrong_at_position=first_wrong_position + 1,
                expected_digit=expected_digit,
                got_digit=digit,
                final_score=game.current_index,
                correct_sequence=f"3.{game.pi_decimals[:game.current_index]}",
                message=f"Wrong at position {first_wrong_position + 1}! You said '{digit}', but it should be '{expected_digit}'. Final score: {game.current_index}"
            )
    
    # All digits were correct!
    return VerifySequenceResponse(
        game_id=game_id,
        sequence_provided=request.sequence,
        digits_checked=len([d for d in clean_sequence if d.isdigit()]),
        correct_count=correct_count,
        all_correct=True,
        game_over=False,
        current_score=game.current_index,
        message=f"All {correct_count} digits correct! Current score: {game.current_index}. Keep going!"
    )

# Game Status Models
class GameStatusResponse(BaseModel):
    game_id: str
    current_position: int
    score: int
    game_over: bool
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
        game_over=game.is_game_over,
        sequence_so_far=f"3.{game.pi_decimals[:game.current_index]}",
        next_10_digits=game.pi_decimals[game.current_index:game.current_index + 10] if not game.is_game_over else "",
        total_digits_available=len(game.pi_decimals)
    )

class DecimalGuessGame:
    def __init__(self, position: int, expected_digit: str):
        self.position = position
        self.expected_digit = expected_digit
        self.is_done = False

decimal_games = {}

class StartDecimalGameResponse(BaseModel):
    game_id: str
    position: int
    message: str

@router.post("/decimal/start", response_model=StartDecimalGameResponse)
def start_decimal_game():
    """
    Guess the decimal at a random position in Pi
    """
    game = Game()

    position = random.randint(1, 100)
    expected_digit = game.pi_decimals[position - 1]

    decimal_game = DecimalGuessGame(position, expected_digit)

    game_id = str(uuid4())
    decimal_games[game_id] = decimal_game

    return StartDecimalGameResponse(
        game_id=game_id,
        position=position,
        message=f"What is the {position}th decimal of Pi?"
    )

class DecimalGuessRequest(BaseModel):
    input: str

class DecimalGuessResponse(BaseModel):
    correct: bool
    expected_digit: str | None = None
    message: str

@router.post("/decimal/{game_id}/guess", response_model=DecimalGuessResponse)
def guess_decimal(game_id: str, request: DecimalGuessRequest):
    game = decimal_games.get(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.is_done:
        raise HTTPException(status_code=400, detail="Game already completed")

    if not request.input.isdigit() or len(request.input) != 1:
        raise HTTPException(status_code=400, detail="Input must be a single digit")

    game.is_done = True

    if request.input == game.expected_digit:
        return DecimalGuessResponse(
            correct=True,
            message="Correct!"
        )

    return DecimalGuessResponse(
        correct=False,
        expected_digit=game.expected_digit,
        message="Wrong answer"
    )
