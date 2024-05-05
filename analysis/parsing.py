import pandas as pd
import requests 
import mix as MixingClass
import user as UserClass
from itertools import product
import boltzmann

column_names_mix = [
    "ID", "Time_Start", "Time_End", "BTC_Amount", "Transaction_ID",
    "Value1", "AnonSet", "Premix", "PostMix", "Value2", "Total_Value",
    "Fee", "Unkown", "Unkown2", "Status", "None1", "None2", "Raw_Transaction",
    "Additional_Info"
]
column_names_activity = [
    "Date",	"Activity",	"PoolSize",	"TransactionID", "Details", "IP", "ClientDetails"
]

import requests

def get_transaction_details(txid):
    url = f"https://mempool.space/testnet/api/tx/{txid}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        inputs = [inp.get('prevout', {}).get('scriptpubkey_address') 
                  for inp in data.get('vin', []) if inp.get('prevout') and inp.get('prevout').get('scriptpubkey_address')]
        
        outputs = [out.get('scriptpubkey_address') 
                   for out in data.get('vout', []) if out.get('scriptpubkey_address')]
        
        return inputs, outputs
    
    else:
        print(f"Failed to fetch data for transaction {txid}: {response.status_code}")
        return [], []

def initiate_mixClass(mixs, mix_dic):
    for _, row in mixs.iterrows():
        tx_id = row["Raw_Transaction"]
        anonSet = row["AnonSet"]
        premixSet = row["Premix"]
        postmixSet = row["PostMix"]
        
        inputs, outputs = get_transaction_details(tx_id)
        mix = MixingClass.Mix(inputs=inputs, outputs=outputs, transactionID=tx_id, anonSet=anonSet, premixSet=premixSet, postmixSet=postmixSet)
        mix_dic[tx_id] = mix 

def create_user_wallets(activity, user_wallets):
    unique_ips = activity['IP'].unique()

    for ip in unique_ips:
        transactions = activity[activity['IP'] == ip]['TransactionID'].unique()
        cleaned_transactions = [tx for tx in transactions if tx is not None and tx == tx]
        wallet = UserClass.UserWallet(transaction_path=list(cleaned_transactions), ip=ip)
        user_wallets[ip] = wallet

    #for wallet in user_wallets.values():
    #    print(wallet.ip, wallet.input_path)
            
def find_pool_size(poolsize):
    filtered_activity = poolsize.dropna(subset=['PoolSize'])
    first_full_entry = filtered_activity['PoolSize'].iloc[0] if not filtered_activity.empty else None
    
    return first_full_entry.removesuffix("btc")

def main():
    mix_dic = {}
    user_dic = {}
    index = -1
    mixs = pd.read_csv('mixs.csv', header=0, names=column_names_mix, usecols=["AnonSet", "Premix", "PostMix", "Raw_Transaction"])
    activity = pd.read_csv('activity.csv', header=0, names=column_names_activity, usecols=["TransactionID", "Details", "IP"])
    poolsize = pd.read_csv('activity.csv', header=0, names=column_names_activity, usecols=["PoolSize"])
    poolsize = find_pool_size(poolsize)
    
    initiate_mixClass(mixs, mix_dic)
    create_user_wallets(activity, user_dic)

    for user in user_dic.values():
        for txid in user.transaction_path:
            txid_split = txid.split(':')
            txid_split, numbers = txid_split[0],txid_split[1]
        
            url = f"https://mempool.space/testnet/api/tx/{txid_split}#vout={numbers}"
            response = requests.get(url)
            transaction_data = response.json()
            #print(transaction_data)
            
            for output in transaction_data['vout']:
                if output['scriptpubkey_type'] == "op_return":
                    index = 0

            if len(transaction_data['vout']) >= int(numbers):
                third_output = transaction_data['vout'][int(numbers) + index]
                #print(third_output)
                address = third_output.get('scriptpubkey_address') 
                
                user.inputs.append(address)
                user.adresses_pairs[txid] = address
                #print(txid, address)
    
    for mix, user in product(mix_dic.values(), user_dic.values()):
        for mix_input, user_input in product(mix.inputs, user.inputs):
            if mix_input == user_input:
                mix.input_pair.append([mix.transactionID, mix_input, user.ip])
                mix.mix_ips.append(user.ip)
       #print(mix.input_pair)
    
    for mix in mix_dic.values():
        for user in user_dic.values():
            
            if user.ip in mix.mix_ips:
                for mix_output in mix.outputs:
                    for user_input in user.inputs:
                        if mix_output == user_input:
                            mix.output_pair.append([mix.transactionID, mix_output, user.ip])
    
    for mix in mix_dic.values():
        for input in mix.input_pair:
            for output in mix.output_pair:
                if input[0] == output[0] and input[2] == output[2]:
                    mix.pairs[input[2]] = {input[1]:output[1]}
                    #print(input[0], input[1], output[1], input[2], output[2])
        #print(mix.pairs)
        
    for mix in mix_dic.values():
        print(f"MixID= {mix.transactionID}")
        print(f"Expected AnonSet= {mix.anonSet} Real AnonSet= {(len(mix.inputs) - len(mix.pairs))}/{mix.anonSet}")
        
        for ip, address_dict in mix.pairs.items():
            if address_dict: 
                for input_address, output_address in address_dict.items():
                    print(f"IP:{ip}, Input address= {input_address}, Output address= {output_address}")
                    
            else:
                print(ip, "No values available")

        #print(mix.input_pair)
        #print(mix.output_pair)
        #for pair_input in mix.input_pair:
            #for pair_output in mix.output_pair:
                

    #for tx_id, mix in mix_dic.items():
        #print(f"Transaction ID: {tx_id}, AnonSet: {mix.anonSet}, PremixSet: {mix.premixSet}, PostmixSet: {mix.postmixSet}, Inputs: {mix.inputs}, Outputs: {mix.outputs}")


if __name__ == "__main__":
    main()

    