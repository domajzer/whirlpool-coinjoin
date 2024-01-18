import subprocess
import time
import re
import argparse
import os

class Options:
    def __init__(self, debug, debugf, pool, mix):
        self.debug = debug
        self.debugf = debugf
        self.pool = pool
        self.mix = mix
        
def parse_arguments():
    parser = argparse.ArgumentParser(description='Automation Script')

    parser.add_argument('-debug', '--debug', action='store_true', help='Enable debug option')
    parser.add_argument('-debugf', '--debugf', action='store_true', help='Enable full debug option')
    parser.add_argument('-pool', '--pool', action='store_true', help='Enable pool option')
    parser.add_argument('-mix', '--mix', action='store_true', help='Enable mix option')
    
    args = parser.parse_args()
    return Options(debug=args.debug, debugf=args.debugf, pool=args.pool, mix=args.mix)

def get_ip_address():
    try:
        result = subprocess.check_output("ip addr", shell=True).decode()
        
        ip_addresses = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', result)

        return ip_addresses 
    except subprocess.CalledProcessError as e:
        return f"An error occurred: {e}"

def system_info():
    system_var = os.uname()
    print(*system_var)
    print(get_ip_address())

def capture_tmux_output(session_name, pane_id, output_file):
    cmd = f"tmux capture-pane -p -t {session_name}:{pane_id}"
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    
    with open(output_file, "w") as file:
        file.write(output)

def start_tmux_with_app(session_name, app_command):
    subprocess.run(f"tmux new -d -s {session_name} {app_command}", shell=True)

def send_keystroke_to_tmux(session_name, keystrokes):
    for keystroke in keystrokes:
        subprocess.run(f"tmux send-keys -t {session_name} {keystroke}", shell=True)
        time.sleep(2.5)

def print_tmux_screen(file_path):
    with open(file_path, 'r') as file:
        contents = file.read()
        print(contents)

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
    send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes)
    time.sleep(2)
    
    capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    if options.debug: 
        print_tmux_screen('output.txt')
    
    check = check_wallet_initialization('output.txt')
    if check == 1:
        start_mixing_keystrokes = ['P', 'Enter', 'S', 'Enter', 'Tab', 'Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Tab', 'Enter'] #TODO
        send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes)
        time.sleep(1.5)

def add_to_pool(tmux_session_name, options, file_path):
    #start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'Enter', 'U', 'Enter', 'Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Tab', 'Enter', 'Tab', 'Enter', 'Enter', 'Tab', 'Enter', 'Tab', 'Tab', 'Enter']
    is_defined = False
    start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'Enter', 'U', 'Enter']
    back_keystrokes = ['Tab', 'Enter', 'Tab', 'Tab', 'Enter']
    date_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"
    
    send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes)
    capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    if options.debug: 
        print_tmux_screen('output.txt')
    time.sleep(1.5)
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            
            if re.search(date_pattern, content):
                print("\033[32mDate pattern found in content\033[0m")
                
            elif "Undefined" in content:
                for _ in range(25):
                    capture_tmux_output('sparrow_wallet', '0', 'output.txt')
                    if options.debug: 
                        print_tmux_screen('output.txt')
                        
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
    
    send_keystroke_to_tmux(tmux_session_name, final_keystrokes)
    capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    if options.debug: 
        print_tmux_screen('output.txt')
    
def start_mix(tmux_session_name, options):
    counter = 0
    #start premix 
    start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'P', 'Enter', 'U', 'Enter', 'Tab', 'Enter']
    send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes)
    capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    
    if options.debug: 
        print_tmux_screen('output.txt')
    
    try:
        with open('output.txt', 'r') as file:
            content = file.read()
            if "Stop Mixing" not in content:
                for _ in range(20):
                    capture_tmux_output('sparrow_wallet', '0', 'output.txt')
                    if options.debug: 
                        print_tmux_screen('output.txt')
                        
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
    send_keystroke_to_tmux(tmux_session_name, stop_start_mixing_keystrokes)
    capture_tmux_output('sparrow_wallet', '0', 'output.txt')
    if options.debug: 
        print_tmux_screen('output.txt')
    
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
    
def main():
    options = parse_arguments()
    tmux_session_name = "sparrow_wallet"
    sparrow_command = "/usr/src/app/Sparrow/bin/Sparrow --network testnet"
    
    start_tmux_with_app(tmux_session_name, sparrow_command)
    time.sleep(7)
    system_info()
    
    #initialize the wallet
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
