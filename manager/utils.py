import re
import tempfile
import json

def batched(data, batch_size=1):
    length = len(data)
    for ndx in range(0, length, batch_size):
        yield data[ndx : min(ndx + batch_size, length)]
        
def update_coordinator_config(file_path, db_host, rpc_host, rpc_port, temp_dir=None):
    with open(file_path, 'r') as file:
        content = file.readlines()
        
    db_url_pattern = re.compile(r'^spring.datasource.dburl=.*$', re.M)
    rpc_host_pattern = re.compile(r'^server.rpc-client.host=.*$', re.M)
    rpc_port_pattern = re.compile(r'^server.rpc-client.port=.*$', re.M)
    
    new_db_url = f'spring.datasource.dburl=jdbc:mysql://{db_host}:3306/whirlpool_testnet\n'
    new_rpc_host = f'server.rpc-client.host={rpc_host}\n'
    new_rpc_port = f'server.rpc-client.port={rpc_port}\n'
    
    with tempfile.NamedTemporaryFile(mode='w+t', delete=False, dir=temp_dir) as tmp_file:
        temp_file_name = tmp_file.name
        
        for line in content:
            if db_url_pattern.match(line):
                tmp_file.write(new_db_url)
            elif rpc_host_pattern.match(line):
                tmp_file.write(new_rpc_host)
            elif rpc_port_pattern.match(line):
                tmp_file.write(new_rpc_port)
            else:
                tmp_file.write(line)
    
    print("Configuration written to file:", temp_file_name)
    return temp_file_name

def update_client_config(file_path, rpc_host, rpc_port, temp_dir=None):
    with open(file_path, 'r') as file:
        config = json.load(file)
    
    new_url = f"http://{rpc_host}:{rpc_port}"
    
    config["coreServer"] = new_url
    config["recentCoreServers"] = [new_url]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=temp_dir, suffix='.json') as tmp_file:
        json.dump(config, tmp_file, indent=4)
        temp_file_name = tmp_file.name 
    
    print("Configuration written to file:", temp_file_name)
    return temp_file_name
