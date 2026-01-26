from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from game_logic import Game

router = APIRouter()

class StartGameRequest(BaseModel):
    mode: int  # 1: Standard, 2: Custom, 3: Decimal Guess
    start_position: int = 0  # Used for Custom Mode
    # decimal_to_guess: int = 0  # Used for Decimal Guess Mode

class StartGameResponse(BaseModel):
    game_id: str
    message: str
    start_position: int = 0

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
    
