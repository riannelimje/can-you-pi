with open("../assets/pi.txt", "r") as file: 
    data = file.read()
    cleaned = data.replace("\n", "").replace(" ", "")[2:] # remove newlines, spaces and 3. to keep it just decimals 
    # idk if i should keep the 3. - KIV this first 
    print(cleaned)

with open("../assets/pi_decimals.txt", "w") as file:
    file.write(cleaned)