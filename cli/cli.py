import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from game_logic import Game

# TODO: find a way to type the numbers in a single line without pressing ENTERRRR
def play_cli(): 
    game = Game()
    
    print("Welcome to the 'Can You Pi?' game!")
    print("Try to recall as many digits of Pi as you can.")
    print("Type 'exit' or 'q' to quit the game at any time.")
    print("Starting: 3.", end="\n") 

    pi_so_far = "3."

    while not game.is_game_over and game.current_index < len(game.pi_decimals):
        user_input = input().strip()
        if game.is_exit(user_input):
            print("Thanks for playing! Goodbye.")
            break
        if not game.is_valid_input(user_input):
            print("Please enter a valid single digit.")
            continue
        is_correct, expected_digit = game.check_input(user_input)
        if is_correct:
            pi_so_far += user_input
            print((pi_so_far), end="")
            continue 
        else: 
            print(f"Game Over! The correct digit was: {expected_digit}")
            print(f"You've recalled {game.current_index} decimals of Pi correctly.") # no need to minus 1 since i start from 0 
            break

    if game.is_complete():
        print("Incredible! You've recalled 1 million decimals of Pi!")

if __name__ == "__main__":
    play_cli()