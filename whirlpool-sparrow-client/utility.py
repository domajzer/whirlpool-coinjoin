import subprocess
import time
import re
import os

def get_ip_address():
    try:
        result = subprocess.check_output("ip addr", shell=True).decode()
        
        ip_addresses = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', result)

        return ip_addresses 
    except subprocess.CalledProcessError as e:
        return f"An error occurred: {e}"

def system_info(options):
    system_var = os.uname()
    print(*system_var)
    print(options.name)
    print(get_ip_address())

def capture_tmux_output(session_name, pane_id, output_file):
    cmd = f"tmux capture-pane -p -t {session_name}:{pane_id}"
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    
    with open(output_file, "w") as file:
        file.write(output)

def start_tmux_with_app(session_name, app_command):
    subprocess.Popen(f"tmux new -d -s {session_name} {app_command}", shell=True)

def send_keystroke_to_tmux(session_name, keystrokes, options):
    for keystroke in keystrokes:
        subprocess.run(f"tmux send-keys -t {session_name} {keystroke}", shell=True)
        time.sleep(3.2)
        #print(keystroke)
        if options.debugf:
            capture_and_print_tmux_screen('sparrow_wallet', '0', 'output.txt')

def print_tmux_screen(file_path):
    with open(file_path, 'r') as file:
        contents = file.read()
        print(contents)

def capture_and_print_tmux_screen(session_name, pane_id, output_file):
    capture_tmux_output(session_name, pane_id, output_file)
    print_tmux_screen(output_file)
    
def parse_seed(input_file, output_file):
    with open(input_file, 'r') as file:
        contents = file.read()
        lines = contents.split('\n')
        seed_words = []
        copy = False

        for line in lines:
            if 'Seed words' in line:
                copy = True
                
            if 'Passphrase' in line:
                break  
            
            if copy:
                words = line.strip()
                if words:
                    seed_words.append(words)
            
        seed = ' '.join(word.replace('│', '').strip() for word in seed_words)
        seed = re.sub(r' {2,}', '', seed)
        
        with open(output_file,'w') as output:
            output.write(seed)
            
    return seed
    
def parse_address(input_file):
    with open(input_file, 'r') as file:
        contents = file.read()
        lines = contents.split('\n')
        for line in lines:
            if " Address " in line:
                match = re.search(r'tb1[a-zA-Z0-9]{39,59}', line)
                if match:
                    return match.group()
    return "No address found"
