# Base Imports
import os

# External Imports
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

# Base Side Inits
infura_key = os.getenv("BASE_INFURA_API_KEY")
base_rpc = f'https://base-mainnet.infura.io/v3/{infura_key}'
w3 = Web3(Web3.HTTPProvider(base_rpc))

# Solana Side Inits