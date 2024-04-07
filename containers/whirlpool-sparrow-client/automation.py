from time import sleep
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
    
    sleep(2)
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
    
    check = check_wallet_initialization('output.txt')
    if check == 1:
        start_mixing_keystrokes = ['P', 'Enter', 'S', 'Enter', 'Tab', 'Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Enter', 'Tab', 'Enter', 'Tab', 'Enter'] #TODO
        utility.send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes, options)
        sleep(10)

def check_for_init_UTXO(tmux_session_name, file_path, options, date_pattern, counter):
    refresh_mixing_keystrokes = ['Tab', 'Tab', 'Enter', 'Tab'] 

    while counter > 0:
        sleep(10)
        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                if re.search(date_pattern, content):
                    print("\033[32mDate pattern found in content\033[0m")
                    return 0

                elif "Unconfirmed" in content:
                    for _ in range(120):
                        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)

                        with open(file_path, 'r') as file:
                            content = file.read()

                        if re.search(date_pattern, content):
                            print("\033[32mDate pattern found in content\033[0m")
                            return 0

                        elif "Unconfirmed" not in content:
                            break

                        else:
                            sleep(35)

                else:
                    print(f"{counter} \033[31m  Date pattern not found in content. Waiting for input UTXO\033[0m")
                    print(counter)
                    if ((counter % 5) == 1):
                        print("in refresh")
                        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                        utility.send_keystroke_to_tmux(tmux_session_name, refresh_mixing_keystrokes, options)
                        sleep(35)
                        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                    counter -= 1
                    continue

                return 1  
            
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return 2

        except Exception as e:
            print(f"An error occurred: {e}")
            return 2
    
    return 1
        
def add_to_pool(tmux_session_name, options, file_path, mix_type):
    #start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'Enter', 'U', 'Enter', 'Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Tab', 'Enter', 'Tab', 'Enter', 'Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Enter']
    date_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"
    is_defined = 1
    
    if mix_type == 1:
        start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'U', 'Enter']  #First time wallet use
    else:
        start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'Enter', 'U', 'Enter']
    
    utility.send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes, options)
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)

    sleep(1.5)
    
    is_defined = check_for_init_UTXO(tmux_session_name, file_path, options, date_pattern, 2500)
    if is_defined:
        print("\033[31mDate pattern not found in content.\033[0m")
        return 2
    
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
    transaction_zero_UTXO = utility.check_for_UTXO('output.txt')
    
    while transaction_zero_UTXO != 0:
        loop_keystrokes = ['Enter', 'Down']
        utility.send_keystroke_to_tmux(tmux_session_name, loop_keystrokes, options)
        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
        
        transaction_zero_UTXO = utility.check_for_UTXO('output.txt')
        
    start_mixing_keystrokes = ['Enter', 'Tab', 'Tab', 'Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes, options)
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)

    sleep(5)
    
    if is_defined == 0:
        keystrokes = ['Tab', 'Enter']
        keystrokes_2 = ['Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Enter']
        continue_loop = True
        
        while continue_loop:
            print("In LOOP")
            utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                
            try:
                print("In try")
                with open('output.txt', 'r') as file:
                    content = file.read()
                    if ("Calculating..." not in content) and ("Fetching" not in content):
                        print("In calculating")
                        utility.send_keystroke_to_tmux(tmux_session_name, keystrokes, options)
                        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                            
                        while "Broadcast Successful" not in content:
                            sleep(5) #Broadcasting premix
                            utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                            
                            with open('output.txt', 'r') as file:
                                content = file.read()
                            
                        utility.send_keystroke_to_tmux(tmux_session_name, keystrokes_2, options)
                        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                        continue_loop = False
                        
            except FileNotFoundError:
                print(f"File not found: {'output.txt'}")
                
            except Exception as e:
                print(f"An error occurred: {e}")    
                
            sleep(3)
        
def start_mix(tmux_session_name, options, pp): #pp_variable = Premix/Postmix variable
    counter = 0 
    start_UTXO = 0
    
    start_mixing_keystrokes_premix = ['W', 'Enter', 'Enter', 'P', 'Enter', 'T', 'Enter']
    start_mixing_keystrokes_postmix = ['W', 'Enter', 'Enter', 'P', 'P', 'Enter', 'T', 'Enter']
    refresh_mixing_keystrokes = ['Tab','Tab','Enter'] 
    return_from_transac_keystrokes = ['Tab','Enter']
    
    utility.send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes_premix if pp else start_mixing_keystrokes_postmix, options)
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
        
    start_UTXO = utility.check_for_UTXO('output.txt')
    
    if (start_UTXO == 0): #If there was a problem with loading UTXO
        utility.send_keystroke_to_tmux(tmux_session_name, refresh_mixing_keystrokes, options)
        
        sleep(30)
        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)

        start_UTXO = utility.check_for_UTXO('output.txt')
        
        while (start_UTXO == 0):  
            utility.send_keystroke_to_tmux(tmux_session_name, ['Enter'], options)
            utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                
            start_UTXO = utility.check_for_UTXO('output.txt')
            
        utility.send_keystroke_to_tmux(tmux_session_name, refresh_mixing_keystrokes, options)
        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
            
    else: #If there was no problem loading UTXO
        utility.send_keystroke_to_tmux(tmux_session_name, return_from_transac_keystrokes, options)
        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
        
    utility.send_keystroke_to_tmux(tmux_session_name, ['U','Enter'], options)
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)

    try:
        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
        with open('output.txt', 'r') as file:
            content = file.read()
            if "Stop Mixing" not in content:
                print("Starting mixing")
                start_mixing_keystrokes_2 = ['Tab', 'Enter']
                utility.send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes_2, options)
                utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
            else:
                print("Mixing already in progress")
    
    except FileNotFoundError:
        print(f"File not found: {'output.txt'}")
        
    except Exception as e:
        print(f"An error occurred: {e}")               
    
    try:
        with open('output.txt', 'r') as file:
            content = file.read()
            if "Stop Mixing" not in content:
                for _ in range(20):
                    print("Checking if mixing started")
                    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                        
                    with open('output.txt', 'r') as file:
                        content = file.read()
                        
                    if "Stop Mixing" not in content:
                        sleep(5)
                        
                    else:
                        counter = 1
                        break
            else:
                counter = 1 
                    
    except FileNotFoundError:
        print(f"File not found: {'output.txt'}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        
    late_UTXO = utility.check_for_UTXO('output.txt')
    print(f"UTXO IN  WALLET {late_UTXO}")
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                
    if pp == 1:
        try:
            now_UTXO = start_UTXO
            print(now_UTXO)
            while(now_UTXO > 0):
                utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                now_UTXO = utility.check_for_UTXO('output.txt')
                print(f"Remaining UTXO {now_UTXO}")
                sleep(25)
            
            utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
            print(f"All {start_UTXO} UTXOs have been mixed")
            
        except FileNotFoundError:
            print(f"File not found: {'output.txt'}")
            
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        while True:
                utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
                now_UTXO = utility.check_for_UTXO('output.txt')
                print(f"Remaining UTXO {now_UTXO}")
                sleep(60)
    
    #return to start after premix
    stop_start_mixing_keystrokes = ['Tab', 'Tab','Enter', 'Tab', 'Tab', 'Enter'] #['Tab', 'Tab', 'Tab', 'Enter', 'Tab', 'Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, stop_start_mixing_keystrokes, options)
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
    
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
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
    
    continue_keystrokes = list(options.name)
    utility.send_keystroke_to_tmux(tmux_session_name, continue_keystrokes, options)
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
    
    continue_keystrokes_2 = ['Tab', 'Enter', 'Enter', 'Tab', 'Tab', 'Tab', 'Enter', 'Enter', '1', '1', '1', 'Enter', 'Tab', 'Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, continue_keystrokes_2, options)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    
    parsed_seed_words = utility.parse_seed('output.txt',seed_file)
    print(parsed_seed_words)    
    if options.debug: 
        utility.print_tmux_screen('output.txt')
    
    continue_keystrokes_3 = ['Tab','Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, continue_keystrokes_3, options)
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
    
    while True:
        utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)
        try:
            with open('output.txt', 'r') as file:
                content = file.read()

                if ("Discovering accounts..." in content):
                    print("Discovering accounts. Sleepin...")
                    sleep(5)
                    
                else:
                    break
                    
        except FileNotFoundError:
            print(f"File not found: {'output.txt'}")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            
    continue_keystrokes_4 = ['Tab', 'Enter', 'Tab', 'Enter']           
    utility.send_keystroke_to_tmux(tmux_session_name, continue_keystrokes_4, options)
    utility.capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt', options)

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
    sleep(5)
    utility.capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    
    address = utility.parse_address("output.txt")
    print(F"$$Wallet$$Address$$: {address}")
    
    return_keystrokes = ['Tab', 'Enter', 'Tab', 'Enter']
    utility.send_keystroke_to_tmux(tmux_session_name, return_keystrokes, options)

def main():
    options = parse_arguments()
    
    if options.debugf:
        options.debug = True
    sleep(10)
    tmux_session_name = "sparrow_wallet"
    sparrow_command = "./Sparrow/bin/Sparrow --network testnet --dir .sparrow"
    utility.system_info(options)
    
    for attempt in range(5):  
        utility.start_tmux_session(tmux_session_name, sparrow_command)
        sleep(10)  
        connected_status = utility.retry_if_not_connected('sparrow_wallet', '0', 'output.txt', options)
        
        if connected_status == 0:
            print(f"\033[32mWallet successfully connected to bitcoin node.\033[0m")
            break  
        else:
            print("\033[31mWallet failed to connect to bitcoin node. Restarting session.\033[0m")
            utility.kill_tmux_session(tmux_session_name) 

        if attempt == 4:  # Last attempt failed
            print("\033[31mFailed to connect after 3 attempts. Exiting.\033[0m")
            return  # Exit the program

    if connected_status == 0:
        # Initialize the wallet
        if options.create:
            create_wallet(tmux_session_name, options)
            get_adress(tmux_session_name, options)
            
        else:
            initialize_wallet(tmux_session_name, options)

        if options.pool:
            ret_val = add_to_pool(tmux_session_name, options, 'output.txt', 1)
            if ret_val == 2:
                return 
            sleep(6)
            
        # Start premix
        if options.mix:
            start_mix(tmux_session_name, options, 1)
            sleep(120)
            start_mix(tmux_session_name, options, 0)

        while True:
            sleep(1)

if __name__ == '__main__':
    main()
