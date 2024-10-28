import json
import time
import os
import requests
from web3 import Web3
from dotenv import load_dotenv
from contracts.abi.erc20_approve_abi import erc20_abi

load_dotenv()
infura_key = os.getenv("BASE_INFURA_API_KEY")
base_rpc = f'https://base-mainnet.infura.io/v3/{infura_key}'
w3 = Web3(Web3.HTTPProvider(base_rpc))

# Part 1
def quote_odos(in_token_address, out_token_address, chain_id = '8453', amount="1000000000000000000", user_addrs = '0x018C3FB97AB31e02C4Dc215B6b0b662A4dDf9428', slippage=0.3):
    """
    Get a quote from Odos API for token swaps.
    
    Args:
        input_token_address: The address of the input token
        output_token_address: The address of the output token
        amount: Amount of input token in wei
        chain_id: Chain ID - 8453 for Base
        slippage: Maximum slippage tolerance in percentage
    """
    
    base_url = "https://api.odos.xyz"
    
    payload = {
        "chainId": chain_id,
        "inputTokens": [
            {
                "tokenAddress": in_token_address,
                "amount": amount
            }
        ],
        "outputTokens": [
            {
                "tokenAddress": out_token_address,
                "proportion": 1
            }
        ],
        "userAddr": user_addrs,
        "slippageLimitPercent": slippage,
        "sourceBlacklist": [],
        "sourceWhitelist": [],
        "compact": True
    }
    
    try:
        response = requests.post(
            f"{base_url}/sor/quote/v2",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching quote from Odos API: {str(e)}")

def parse_odos_price(odos_quote):
    """
    Extracts the netOutValue from Odos quote response data.

    """
    try:
        return float(odos_quote['outValues'][0])
    except (KeyError, ValueError) as e:
        raise Exception(f"Error parsing Odos price data: {str(e)}")

def parse_path_id(odos_quote):
    try:
        return str(odos_quote['pathId'])
    except (KeyError, ValueError) as e:
        raise Exception(f"Error parsing Odos pathId: {str(e)}")

def price_checker(delay=5):
    """
    Continuously checks Odos price every {delay} seconds
    
    Args:
        delay: Time in seconds between each check (default: 10)
    """

    LUNA_BASE = '0x55cD6469F597452B5A7536e2CD98fDE4c1247ee4'
    USDC_BASE = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'

    arbitrage_check = False
    price_diff = 0

    while True:
        try:
            quote = quote_odos(LUNA_BASE, USDC_BASE) # in,out
            odos_price = parse_odos_price(quote)
            print(f"Current price: {odos_price}")
            price_diff = 10 # TEMP
            time.sleep(delay)

            if price_diff >= 5 :
                arbitrage_check = True
                break
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(delay)

    return arbitrage_check

# Part 2
def assemble_odos(user_addrs, pathId):
    """
    Assemble the odos quote
    
    """

    print(user_addrs)
    
    base_url = "https://api.odos.xyz"
    
    payload = {
        "userAddr": user_addrs,
        "pathId": pathId,
        "simulate": False
    }
    
    try:
        response = requests.post(
            f"{base_url}/sor/assemble",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching quote from Odos API: {str(e)}")

# Part 3 - Approvals

def check_token_approval(token_address, owner_address, spender_address):
    """Check if token approval is needed"""

    token_contract = w3.eth.contract(address=token_address, abi=erc20_abi)
    current_allowance = token_contract.functions.allowance(owner_address, spender_address).call()
    
    # Check if current allowance is "infinite enough" (very large number)
    LARGE_APPROVAL_THRESHOLD = 2**200  # If allowance is above this, we consider it infinite
    return current_allowance < LARGE_APPROVAL_THRESHOLD

def send_infinite_approval(token_address, spender_address):
    """Send infinite token approval transaction"""
    
    token_contract = w3.eth.contract(address=token_address, abi=abi)
    private_key = os.getenv("PRIVATE_KEY")
    account = w3.eth.account.from_key(private_key)
    
    # Maximum uint256 value for infinite approval
    MAX_INT = 2**256 - 1
    
    # Get the latest nonce and gas price
    latest_nonce = w3.eth.get_transaction_count(account.address, 'latest')
    gas_price = w3.eth.gas_price
    
    print(f"Using nonce: {latest_nonce}")
    
    try:
        # Build approval transaction
        approve_tx = token_contract.functions.approve(
            spender_address,
            MAX_INT
        ).build_transaction({
            'from': account.address,
            'nonce': latest_nonce,
            'gas': 100000,
            'gasPrice': gas_price,
            'chainId': 8453  # Base chain ID
        })
        
        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for transaction receipt
        print(f"Waiting for infinite approval transaction {tx_hash.hex()} to be mined...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return tx_receipt['status'] == 1
        
    except Exception as e:
        print(f"Error in approval transaction: {str(e)}")
        return False


# Part 4
def execute_transaction(assembled_transaction, chain_id=8453):
    """
    Execute a transaction and check its status
    
    """
    private_key = os.getenv("PRIVATE_KEY")
    transaction = assembled_transaction["transaction"]
    transaction["chainId"] = chain_id
    transaction["value"] = int(transaction["value"])
    
    try:
        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Wait for transaction receipt
        print(f"Waiting for transaction {tx_hash.hex()} to be mined...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Check transaction status
        if tx_receipt['status'] == 1:
            return {
                'success': True,
                'hash': tx_hash.hex(),
                'receipt': tx_receipt
            }
        else:
            # Try to get revert reason
            try:
                tx = w3.eth.get_transaction(tx_hash)
                # Simulate the failed transaction to get the revert reason
                w3.eth.call(
                    {
                        'from': tx['from'],
                        'to': tx['to'],
                        'data': tx['input'],
                        'value': tx['value'],
                        'gas': tx['gas'],
                        'gasPrice': tx['gasPrice'],
                    },
                    tx_receipt['blockNumber']
                )
            except Exception as call_error:
                error_message = str(call_error)
                return {
                    'success': False,
                    'hash': tx_hash.hex(),
                    'error': f"Transaction reverted: {error_message}",
                    'receipt': tx_receipt
                }
            
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to send transaction: {str(e)}"
        }

def main():

    # 1. Start price checker
    arbitrage_check = price_checker()

    # 2. If arbitrage_check == True, call decide_direction()
    if arbitrage_check == True:
        pass

    # 3. Decide direction will determine which is in/out token
    LUNA_BASE = '0x55cD6469F597452B5A7536e2CD98fDE4c1247ee4'
    USDC_BASE = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
    ODOS_ROUTER_V2 = "0x19cEeAd7105607Cd444F5ad10dd51356436095a1"

    in_token = LUNA_BASE
    out_token = USDC_BASE

    # 4. Initialize wallet, ie: wallet address
    user_addrs = '0x018C3FB97AB31e02C4Dc215B6b0b662A4dDf9428'

    # 5. Call quote_odos
    odos_quote = quote_odos(in_token, out_token, user_addrs=user_addrs, amount="1000000000000000000")
    path_id = parse_path_id(odos_quote)

    # 6. Assemble using assemble_odos
    assembled_transaction = assemble_odos(user_addrs, path_id)

    # Pre - Get token approval
    needs_approval = check_token_approval(in_token, user_addrs, ODOS_ROUTER_V2)

    if needs_approval:
        print("Token approval needed. Sending approval transaction...")
        approval_success = send_infinite_approval(in_token, ODOS_ROUTER_V2)
        if not approval_success:
            print("Approval failed!")
            return
        print("Approval successful!")

    # 7. Execute Transaction 
    tx_hash = execute_transaction(assembled_transaction)

    # 8. Print Results
    print(tx_hash)

main()