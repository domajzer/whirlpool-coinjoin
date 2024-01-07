import subprocess
import time

def start_tmux_with_app(session_name, app_command):
    subprocess.run(f"tmux new -d -s {session_name} {app_command}", shell=True)

def send_keystroke_to_tmux(session_name, keystrokes):
    for keystroke in keystrokes:
        subprocess.run(f"tmux send-keys -t {session_name} {keystroke}", shell=True)
        time.sleep(0.8)

def main():
    tmux_session_name = "sparrow_wallet"
    sparrow_command = "/usr/src/app/Sparrow/bin/Sparrow --network testnet"
    
    start_tmux_with_app(tmux_session_name, sparrow_command)
    time.sleep(10)
    
    #initialize the wallet
    start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'Enter', 'Enter', 'Enter', 'Tab', 'Enter']
    send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes)
    #start premix 
    start_mixing_keystrokes = ['W', 'Enter', 'Enter', 'P', 'Enter', 'U', 'Enter', 'Tab', 'Enter']
    send_keystroke_to_tmux(tmux_session_name, start_mixing_keystrokes)
    #return to start after premix
    stop_start_mixing_keystrokes = ['Tab', 'Enter', 'Tab', 'Tab', 'Enter']
    send_keystroke_to_tmux(tmux_session_name, stop_start_mixing_keystrokes)

if __name__ == '__main__':
    main()
