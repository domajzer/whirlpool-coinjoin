import pandas as pd
import requests 
import mix as MixingClass
import user as UserClass
from itertools import product
from boltzmann.linker.txos_linker import TxosLinker
import requests
import transaction as TxoClass

column_names_mix = [
    "ID", "Time_Start", "Time_End", "BTC_Amount", "Transaction_ID",
    "Value1", "AnonSet", "Premix", "PostMix", "Value2", "Total_Value",
    "Fee", "Unkown", "Unkown2", "Status", "None1", "None2", "Raw_Transaction",
    "Additional_Info"
]
column_names_activity = [
    "Date",	"Activity",	"PoolSize",	"TransactionID", "Details", "IP", "ClientDetails"
]

def get_transaction_details(txid):

    url = f"https://mempool.space/testnet/api/tx/{txid}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        inputs = [
            TxoClass.TxO(address=inp.get('prevout', {}).get('scriptpubkey_address'), 
                value=inp.get('prevout', {}).get('value'), 
                inputVal=True)
            for inp in data.get('vin', []) if inp.get('prevout')
        ]

        outputs = [
            TxoClass.TxO(address=out.get('scriptpubkey_address'), 
                value=out.get('value'), 
                inputVal=False)
            for out in data.get('vout', []) if out.get('scriptpubkey_address')
        ]
        
        fees = data.get('fee', 0)
        return inputs, outputs, fees
    
    else:
        print(f"Failed to fetch data for transaction {txid}: {response.status_code}")
        return [], [], 0

def initiate_mixClass(mixs, mix_dic):
    for _, row in mixs.iterrows():
        tx_id = row["Raw_Transaction"]
        anonSet = row["AnonSet"]
        premixSet = row["Premix"]
        postmixSet = row["PostMix"]
        
        inputs, outputs, fees = get_transaction_details(tx_id)
        mix = MixingClass.Mix(inputs=inputs, outputs=outputs, transactionID=tx_id, anonSet=anonSet, premixSet=premixSet, postmixSet=postmixSet, fees=fees)
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

def transform_txo_data(txo_list):
    return [(txo.address, txo.value) for txo in txo_list]

def print_analysis(linkability_matrix, num_combinations, sorted_inputs, sorted_outputs):
    print("Linkability Matrix:\n", linkability_matrix)
    print("Number of Combinations:", num_combinations)
    print("Sorted Inputs:", sorted_inputs)
    print("Sorted Outputs:", sorted_outputs)
    print("--------------------------------------------------------------------------------")

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

    #for tx_id, mix in mix_dic.items():
        #input_addresses = ", ".join([inp.address for inp in mix.inputs])
        #output_addresses = ", ".join([out.address for out in mix.outputs])
        #print(f"Transaction ID: {tx_id}, AnonSet: {mix.anonSet}, PremixSet: {mix.premixSet}, PostmixSet: {mix.postmixSet}, Inputs: {input_addresses}, Outputs: {output_addresses}")

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
            if mix_input.address == user_input:
                mix.input_pair.append([mix.transactionID, mix_input, user.ip])
                mix.mix_ips.append(user.ip)
        #for pair in mix.input_pair:
            #print(f"Transaction ID: {pair[0]}, Input: {pair[1]}, User IP: {pair[2]}")

    for mix in mix_dic.values():
        for user in user_dic.values():
            
            if user.ip in mix.mix_ips:
                for mix_output in mix.outputs:
                    for user_input in user.inputs:
                        if mix_output.address == user_input:
                            mix.output_pair.append([mix.transactionID, mix_output, user.ip])
    
    for mix in mix_dic.values():
        for input in mix.input_pair:
            for output in mix.output_pair:
                if input[0] == output[0] and input[2] == output[2]:
                    mix.pairs[input[2]] = {input[1]:output[1]}
                    #print(input[0], input[1], output[1], input[2], output[2])
        #print(mix.pairs)
    linked_txos = []  

    for mix in mix_dic.values():
        print(f"MixID= {mix.transactionID}")
        print(f"Expected AnonSet= {mix.anonSet} Real AnonSet= {(len(mix.inputs) - len(mix.pairs))}/{mix.anonSet}")
        print(f"Premix= {mix.premixSet} Postmix= {mix.postmixSet}")

        current_linked_set = set()
        for ip, address_dict in mix.pairs.items():
            if address_dict: 
                for input_address, output_address in address_dict.items():
                    print(f"IP:{ip}, Input address= {input_address.address}, Output address= {output_address.address}")
                    current_linked_set.update([input_address.address, output_address.address])
            else:
                print(ip, "No values available")

        if current_linked_set:
            linked_txos.append(current_linked_set)

        extracted_inputs, extracted_outputs = transform_txo_data(mix.inputs), transform_txo_data(mix.outputs)
        
        linker = TxosLinker(inputs=extracted_inputs, outputs=extracted_outputs, fees=mix.fees)
        linkability_matrix, num_combinations, sorted_inputs, sorted_outputs = linker.process(
            linked_txos=linked_txos, 
            options=[TxosLinker.LINKABILITY, TxosLinker.PRECHECK]
        )
        
        print_analysis(linkability_matrix, num_combinations, sorted_inputs, sorted_outputs)
        linked_txos = [] #If each transaction should be evaluated solo. Removed or commented will create an enviroemtn where all input/outputs are saved.

if __name__ == "__main__":
    main()

    