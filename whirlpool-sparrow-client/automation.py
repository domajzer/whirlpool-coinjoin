import pyautogui

def main():
    
    press_keys()

def press_keys():
    # Short delay to switch to the right window after running the script

    # Pressing the keys "W", "P", "P"
    pyautogui.press('w')
    pyautogui.press('p')
    pyautogui.press('p')

# Call the function to execute the key presses
press_keys()



if __name__ == '__main__':
    main()