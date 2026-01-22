def load_pi_decimals():
    with open("assets/pi_decimals.txt", "r") as file: 
        return file.read().strip()
    
PI_DECIMALS = load_pi_decimals()

class Game:
    def __init__(self):
        self.pi_decimals = PI_DECIMALS
        self.current_index = 0 
        self.is_game_over = False
        
    def is_exit(self, user_input):
        if user_input.lower() == 'exit':
            self.is_game_over = True
            return True
        return False
    
    def is_valid_input(self, user_input):
        return user_input.isdigit() and len(user_input) == 1
    
    def check_input(self, user_input):
        expected_digit = self.pi_decimals[self.current_index]
        if user_input == expected_digit:
            self.current_index += 1
            return True, None
        else:
            self.is_game_over = True
            return False, expected_digit
        
    def is_complete(self): # if someone magically manages to get to 1 million 
        return self.current_index >= len(self.pi_decimals)
