import readchar
import random
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
    print("3. Decimal Guess Mode (guess a specific decimal of Pi)")

    while True:
        mode_input = input("Enter 1, 2, or 3: ").strip()
        if mode_input == '1':
            print("Starting: 3.", end="\n")
            game = Game()
            play_cli(game)
            break
        elif mode_input == '2':
            play_from_position()
            break
        elif mode_input == '3':
            play_decimal_at()
            break
        else:
            print("Invalid input. Please enter 1, 2, or 3.")

def handle_validation(game, user_input): 
    if game.is_exit(user_input):
        print("Thanks for playing! Goodbye.")
        return True
    if not game.is_valid_input(user_input):
        print("\nPlease enter a valid single digit.")
        return False
    return None


def play_cli(game): 

    while not game.is_game_over and game.current_index < len(game.pi_decimals):
        user_input = readchar.readkey()

        # is there a better way to do this??? kiv 
        is_valid = handle_validation(game, user_input)
        if is_valid:
            break
        if is_valid is False: # cannot put if not is_valid since None will return True
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
        start_pos_input = input("Enter the starting position for the decimal (1-indexed): ").strip()

        if handle_validation(game, start_pos_input):
            break

        start_pos = int(start_pos_input)
        if start_pos < 1 or start_pos > len(game.pi_decimals):
            print("Starting position out of range. Please try again.")
            continue
        break

    game.current_index = start_pos - 1

    print(f"Starting from position: 3.{game.pi_decimals[:game.current_index]}", end="\n")

    play_cli(game)

def play_decimal_at(): 
    game = Game()

    print("So you're gonna guess the specific digit of Pi!")
    print("eg. What's the 10th decimal of Pi? Answer: 5")

    while True: 
        position = random.randint(1, 100) # 1 to 100 for a start 
        print(f"What is the {position}th decimal of Pi?")
        user_input = input().strip()

        is_valid = handle_validation(game, user_input)
        if is_valid:
            break
        if is_valid is False:
            continue

        expected_digit = game.pi_decimals[position - 1] 
        if user_input == expected_digit:
            print("Correct!")
        else:
            print(f"Wrong! The correct digit was: {expected_digit}")
            break


if __name__ == "__main__":
    start()