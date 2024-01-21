import subprocess
import time
import re
import argparse
import utility

class Options:
    def __init__(self, debug, debugf, pool, mix, create, name):
        self.debug = debug
        self.debugf = debugf
        self.pool = pool
        self.mix = mix
        self.create = create
        self.name = name
        
def parse_arguments():
    parser = argparse.ArgumentParser(description='Automation Script')

    parser.add_argument('-debug', '--debug', action='store_true', help='Enable debug option')
    parser.add_argument('-debugf', '--debugf', action='store_true', help='Enable full debug option')
    parser.add_argument('-pool', '--pool', action='store_true', help='Enable pool option')
    parser.add_argument('-mix', '--mix', action='store_true', help='Enable mix option')
    parser.add_argument('-create', '--create', action='store_true', help='Set the name')
    parser.add_argument('-name', '--name', action='store', type=str, help='Set the name')
    
    args = parser.parse_args()
    return Options(debug=args.debug, debugf=args.debugf, pool=args.pool, mix=args.mix, create=args.create, name=args.name)

def check_wallet_initialization(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()

            if ("Wallets" in content) and ("Preferences" in content) and ("Quit" in content) and ("Connecting" not in content):
                print("\033[32mWallet initialization successful\033[0m")
                return 0
            else:
                print("\033[31mWallet initialization not confirmed\033[0m")
                return 1
                
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

def initialize_wallet(tmux_session_name, options):
    start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'Enter', 'Enter', 'Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes, options)
    time.sleep(2)
    
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    if options.debug: 
        utility.print_tmux_screen('output.txt')
    
    check = check_wallet_initialization('output.txt')
    if check == 1:
        start_mixing_keystrokes = ['P', 'Enter', 'S', 'Enter', 'Tab', 'Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Enter', 'Tab', 'Enter', 'Tab', 'Enter'] #TODO
        utility.send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes, options)
        time.sleep(10)

def add_to_pool(tmux_session_name, options, file_path):
    #start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'Enter', 'U', 'Enter', 'Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Tab', 'Enter', 'Tab', 'Enter', 'Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Enter']
    is_defined = False
    start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'Enter', 'U', 'Enter']
    back_keystrokes = ['Tab', 'Enter', 'Tab', 'Tab', 'Enter']
    date_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"
    
    utility.send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes, options)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    if options.debug: 
        utility.print_tmux_screen('output.txt')
    time.sleep(1.5)
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            
            if re.search(date_pattern, content):
                print("\033[32mDate pattern found in content\033[0m")
                
            elif "Undefined" in content:
                for _ in range(25):
                    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
                    if options.debug: 
                        utility.print_tmux_screen('output.txt')
                        
                    with open(file_path, 'r') as file:
                        content = file.read()
                        
                    if "Undefined" in content:
                        time.sleep(25)
                    else:
                        break
            
            else:
                is_defined = True
                print("\033[31mDate pattern not found in content\033[0m")
                back_keystrokes = ['Tab', 'Enter', 'Tab', 'Tab', 'Enter']
                
    except FileNotFoundError:
        print(f"File not found: {file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")
    
    start_mixing_keystrokes = ['Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Tab', 'Enter', 'Tab', 'Enter', 'Enter', 'Tab', 'Enter', 'Tab', 'Enter']
    final_keystrokes = back_keystrokes if is_defined else start_mixing_keystrokes
    
    utility.send_keystroke_to_tmux(tmux_session_name, final_keystrokes, options)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    if options.debug: 
        utility.print_tmux_screen('output.txt')
    
def start_mix(tmux_session_name, options):
    counter = 0
    #start premix 
    start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'P', 'Enter', 'U', 'Enter', 'Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes, options)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    
    if options.debug: 
        utility.print_tmux_screen('output.txt')
    
    try:
        with open('output.txt', 'r') as file:
            content = file.read()
            if "Stop Mixing" not in content:
                for _ in range(20):
                    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
                    if options.debug: 
                        utility.print_tmux_screen('output.txt')
                        
                    with open('output.txt', 'r') as file:
                        content = file.read()
                        
                    if "Stop Mixing" not in content:
                        time.sleep(5)
                        
                    else:
                        counter += 1
                        break
            else:
                counter = 1 
                    
    except FileNotFoundError:
        print(f"File not found: {'output.txt'}")

    except Exception as e:
        print(f"An error occurred: {e}")
                            
    #return to start after premix
    stop_start_mixing_keystrokes = ['Tab', 'Tab', 'Tab', 'Enter', 'Tab', 'Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, stop_start_mixing_keystrokes, options)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    if options.debug: 
        utility.print_tmux_screen('output.txt')
    
    try:
        with open('output.txt', 'r') as file:
            content = file.read()

            if ("Wallets" in content) and ("Preferences" in content) and ("Quit" in content) and ("Connecting" not in content) and (counter == 1):
                print("\033[32mWallet mixing started/stopped successful\033[0m")
                
            else:
                print("\033[31mWallet mixing started/stopped unsuccessful\033[0m")
                
    except FileNotFoundError:
        print(f"File not found: {'output.txt'}")

    except Exception as e:
        print(f"An error occurred: {e}")
    
def create_wallet(tmux_session_name, options):
    seed_file = 'seed.txt'
    start_keystrokes = ['W', 'Enter', 'C', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, start_keystrokes, options)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    
    if options.debug: 
        utility.print_tmux_screen('output.txt')
    
    continue_keystrokes = list(options.name)
    utility.send_keystroke_to_tmux(tmux_session_name, continue_keystrokes, options)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    
    if options.debug: 
        utility.print_tmux_screen('output.txt')
    
    continue_keystrokes_2 = ['Tab', 'Enter', 'Enter', 'Tab', 'Tab', 'Tab', 'Enter', 'Enter', '1', '1', '1', 'Enter', 'Tab', 'Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, continue_keystrokes_2, options)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    
    parsed_seed_words = utility.parse_seed('output.txt',seed_file)
    print(parsed_seed_words)    
    if options.debug: 
        utility.print_tmux_screen('output.txt')
    
    continue_keystrokes_3 = ['Tab', 'Tab', 'Enter', 'Tab', 'Enter', 'Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, continue_keystrokes_3, options)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')

    if options.debug: 
        utility.print_tmux_screen('output.txt')

    try:
        with open('output.txt', 'r') as file:
            content = file.read()

            if ("Wallets" in content) and ("Preferences" in content) and ("Quit" in content) and ("Connecting" not in content):
                print(f"\033[32mWallet creation successful. Seed can be found {seed_file}.\033[0m")
                return 0
            else:
                print("\033[31mWallet creation failed\033[0m")
                return 1
                
    except FileNotFoundError:
        print(f"File not found: {'output.txt'}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
def get_adress(tmux_session_name, options):
    start_keystrokes = ['W', 'Enter', 'Enter', 'R', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, start_keystrokes, options)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    
    address = utility.parse_address("output.txt")
    print(F"$$Wallet$$Address$$: {address}")
    
    return_keystrokes = ['Tab', 'Enter', 'Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, return_keystrokes, options)

def main():
    options = parse_arguments()
    tmux_session_name = "sparrow_wallet"
    sparrow_command = "/usr/src/app/Sparrow/bin/Sparrow --network testnet"
    
    utility.start_tmux_with_app(tmux_session_name, sparrow_command)
    time.sleep(5)
    utility.system_info(options)
    
    #initialize the wallet
    if options.create:
        create_wallet(tmux_session_name, options)
        get_adress(tmux_session_name, options)
    else:
        initialize_wallet(tmux_session_name, options)
    #add to pool
    if options.pool:
        add_to_pool(tmux_session_name, options, 'output.txt')
    #start premix 
    if options.mix:
        start_mix(tmux_session_name, options)
    #stop premix
    #time.sleep(25)
    #start_mix(tmux_session_name, options)
    
    while(1):
       time.sleep(1)

if __name__ == '__main__':
    main()
