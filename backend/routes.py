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
