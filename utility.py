import requests
import os
from web3 import Web3
from dotenv import load_dotenv

def get_raydium_lp_liquidity(lp_address):

    """
    Fetch liquidity pool information and calculate USD liquidity
    
    Args:
        lp_address (str): The LP pool address

    """
    url = f"https://api-v3.raydium.io/pools/info/ids?ids={lp_address}"
    headers = {'accept': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        pool_data = data['data'][0]
        lp_price = pool_data['lpPrice']
        lp_amount = pool_data['lpAmount']
        
        liquidity_usd = lp_price * lp_amount
        return liquidity_usd
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    
def query_uniswap_liquidity(lp_address):
    """
    Query liquidity information from a Uniswap V2 pair contract
    
    """

    infura_key = os.getenv("BASE_INFURA_API_KEY")
    base_rpc = f'https://base-mainnet.infura.io/v3/{infura_key}'
    w3 = Web3(Web3.HTTPProvider(base_rpc))
    
    PAIR_ABI = [
        {
            "inputs": [],
            "name": "getReserves",
            "outputs": [
                {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "token0",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "token1",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    contract = w3.eth.contract(address=lp_address, abi=PAIR_ABI)
    
    # Get reserves
    reserves = contract.functions.getReserves().call()
    token0 = contract.functions.token0().call()
    token1 = contract.functions.token1().call()
    
    return {
        'token0_address': token0,
        'token1_address': token1,
        'reserve0': reserves[0],
        'reserve1': reserves[1],
        'timestamp': reserves[2]
    }