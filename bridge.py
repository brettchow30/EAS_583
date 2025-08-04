from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd
import eth_account


def connect_to(chain):
    if chain == 'source':  # The source contract chain is avax
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'destination':  # The destination contract chain is bsc
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['source','destination']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
    try:
        with open(contract_info, 'r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( f"Failed to read contract info\nPlease contact your instructor\n{e}" )
        return 0
    return contracts[chain]



def scan_blocks(chain, contract_info="contract_info.json"):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    # This is different from Bridge IV where chain was "avax" or "bsc"
    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return 0
    
    #YOUR CODE HERE
    if chain == 'source':
        chain2 = 'destination'
    else:
        chain2 = 'source'

    w3 = connect_to(chain)
    w3_2 = connect_to(chain2)
    contract_info = get_contract_info(chain, "contract_info.json")
    contracts_info_2 = get_contract_info(chain2, "contract_info.json")
    sk = "9b016369b693495d5a90784ba3247e58281980dbe918b5a3fc03e572a0fece68"
    account = eth_account.Account.from_key(sk)

    chain1_contract = w3.eth.contract(address=contract_info['address'], abi=contract_info['abi'])
    chain2_contract = w3_2.eth.contract(address=contracts_info_2['address'], abi=contracts_info_2['abi'])

    start_block = max(0, w3.eth.block_number-10)


    if chain == 'source':
        event_filter = chain1_contract.events.Deposit.create_filter(from_block=start_block,to_block=w3.eth.block_number)
        events = event_filter.get_all_entries()
        # print(start_block, w3.eth.block_number)
        print(events)
        for evt in events:
            recipient = evt['args']['recipient']
            amount = evt['args']['amount']
            token = evt['args']['token']

            gas_price = chain2_contract.functions.wrap(token, recipient, amount).estimate_gas({'from': account.address})
            txn = chain2_contract.functions.wrap(token, recipient, amount).build_transaction({
                'from':account.address,
                'nonce': w3_2.eth.get_transaction_count(account.address),
                'gas':gas_price,
                'gasPrice':w3_2.eth.gas_price
            })
            signed_txn = account.sign_transaction(txn)
            txn_hash = w3_2.eth.send_raw_transaction(signed_txn.raw_transaction)
            print('Wrapped transaction sent on destination')  
    elif chain == 'destination':
        start_block = max(0, w3_2.eth.block_number-10)
        event_filter = chain1_contract.events.Unwrap.create_filter(from_block=start_block, to_block=w3_2.eth.block_number)
        events = event_filter.get_all_entries()

        for evt in events:
            user = evt['args']['recipient']
            amount = evt['args']['amount']
            token = evt['args']['wrapped_token']

            gas_price = chain2_contract.functions.withdraw(token, user, amount).estimate_gas({'from': account.address})
            txn = chain2_contract.functions.withdraw(token, user, amount).build_transaction({
                'from':account.address,
                'nonce': w3_2.eth.get_transaction_count(account.address),
                'gas':gas_price,
                'gasPrice':w3_2.eth.gas_price
            })
            signed_txn = account.sign_transaction(txn)
            txn_hash = w3_2.eth.send_raw_transaction(signed_txn.raw_transaction)
            print('Withdrawal transaction sent on source')

