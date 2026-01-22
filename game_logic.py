def load_pi_decimals():
    with open("assets/pi_decimals.txt", "r") as file: 
        return file.read().strip()
    
PI_DECIMALS = load_pi_decimals()

class Game:
    def __init__(self):
        self.pi_decimals = PI_DECIMALS
        self.current_index = 0 
        self.is_game_over = False

    def start(self):
        print("Welcome to the 'Can You Pi?' game!")
        print("Try to recall as many digits of Pi as you can.")
        print("Type 'exit' to quit the game at any time.")
        print("Starting: 3.", end=" ")
        self.play()

    def check_input(self, user_input):
        if user_input.lower() == 'exit':
            self.is_game_over = True
            print("Thanks for playing!")
            return None, None
        if not user_input.isdigit():
            print("Please enter a valid digit.")
            return None, None
        
        expected_digit = self.pi_decimals[self.current_index]
        if user_input == expected_digit:
            self.current_index += 1
            return True, None
        else:
            self.is_game_over = True
            return False, expected_digit

    def play(self):
        while not self.is_game_over and self.current_index < len(self.pi_decimals):
            user_input = input().strip()
            is_correct, expected_digit = self.check_input(user_input)
            if is_correct is True:
                continue # i just wanna continue in the same line 
            else: 
                print(f"Game Over! The correct digit was: {expected_digit}")
                print(f"You've recalled {self.current_index} digits of Pi correctly.") # no need to minus 1 since i start from 0 
                break
        if self.current_index == len(self.pi_decimals):
            print("Congratulations! You've recalled a million decimals of pi!")
            
def main():
    game = Game()
    game.start()

if __name__ == "__main__":
    main()
       


