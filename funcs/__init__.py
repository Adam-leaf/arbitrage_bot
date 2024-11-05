# Base Imports
import os
import json

# External Imports
from dotenv import load_dotenv
from web3 import Web3
from web3 import AsyncHTTPProvider, AsyncWeb3
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient

load_dotenv()

# Base Side Inits
infura_key = os.getenv("BASE_INFURA_API_KEY")
base_rpc = f'https://base-mainnet.infura.io/v3/{infura_key}'

w3 = Web3(Web3.HTTPProvider(base_rpc))
w3_async = AsyncWeb3(AsyncHTTPProvider(base_rpc))

# Solana Side Inits
sol_rpc = os.getenv("SOL_RPC")
sol_client_async = AsyncClient(sol_rpc)
sol_client = Client(sol_rpc)

def save_trade_data(trade_data, filename='trade_data.json'):
    with open(filename, 'w') as f:
        json.dump(trade_data, f, indent=4)
    return filename
