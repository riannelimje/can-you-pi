import readchar
import sys

from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from game_logic import Game

def start(): 
    print("Welcome to the 'Can You Pi?' game!")
    print("Try to recall as many digits of Pi as you can.")
    print("Type 'q' to quit the game at any time.")

    print("Choose a game mode:")
    print("1. Standard Mode (start from the beginning)")
    print("2. Custom Mode (start from a specific position)")
    while True:
        mode_input = input("Enter 1 or 2: ").strip()
        if mode_input == '1':
            print("Starting: 3.", end="\n")
            game = Game()
            play_cli(game)
            break
        elif mode_input == '2':
            play_from_position()
            break
        else:
            print("Invalid input. Please enter 1 or 2.")


def play_cli(game): 

    while not game.is_game_over and game.current_index < len(game.pi_decimals):
        user_input = readchar.readkey().strip()
        if game.is_exit(user_input):
            print("Thanks for playing! Goodbye.")
            break
        if not game.is_valid_input(user_input):
            print("Please enter a valid single digit.")
            continue
        is_correct, expected_digit = game.check_input(user_input)
        if is_correct:
            print(user_input, end="", flush=True)
            continue 
        else: 
            print(f"\nGame Over! The correct digit was: {expected_digit}")
            print(f"You've recalled {game.current_index} decimals of Pi correctly.") # no need to minus 1 since i start from 0 
            break

    if game.is_complete():
        print("Incredible! You've recalled 1 million decimals of Pi!")

def play_from_position():
    game = Game()
    
    while True:
        start_pos_input = input("Enter the starting position for the decimal (0-indexed): ").strip()
        if start_pos_input.lower() == 'q':
            print("Thanks for playing! Goodbye.")
            return
        if not start_pos_input.isdigit():
            print("Please enter a valid number.")
            continue
        start_pos = int(start_pos_input)
        if start_pos < 0 or start_pos >= len(game.pi_decimals):
            print("Starting position out of range. Please try again.")
            continue
        break

    game.current_index = start_pos

    print(f"Starting from position {game.current_index}: 3.{game.pi_decimals[:game.current_index]}", end="\n")

    play_cli(game)

if __name__ == "__main__":
    start()