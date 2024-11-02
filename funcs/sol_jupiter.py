import os
from decimal import Decimal

# External
import requests
import aiohttp
import base58
import asyncio 
from dotenv import load_dotenv
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair  
from solders.transaction import VersionedTransaction
from solders.message import Message
from solders.signature import Signature
from base64 import b64decode

# Utils
def convert_to_decimal_amount(amount: float, decimals: int) -> str:
    """Convert human readable amount to token decimal precision."""
    scale = Decimal(10) ** decimals
    return str(int(Decimal(str(amount)) * scale))

def convert_from_decimal_amount(amount: str, decimals: int) -> float:
    """Convert token decimal precision to human readable amount."""
    scale = Decimal(10) ** decimals
    return float(Decimal(amount) / scale)

# Core
async def quote_jupiter(in_token, out_token, amount, in_decimals):
    """Get a quote from Jupiter for token swap."""
    decimal_amount = convert_to_decimal_amount(amount, in_decimals)
    
    url = f"https://quote-api.jup.ag/v6/quote?inputMint={in_token}&outputMint={out_token}&amount={decimal_amount}"
    headers = {'Accept': 'application/json'}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()