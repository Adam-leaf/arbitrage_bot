# Built-in
import os
from decimal import Decimal

# External 
from web3 import Web3
from dotenv import load_dotenv
from contracts.abi.base_uniswapV2_router02 import router02_abi
from contracts.abi.base_uniswapV2_lp import v2_lp_abi

load_dotenv()

# Web3 Functions
def init_web3():
    infura_key = os.getenv("BASE_INFURA_API_KEY")
    base_rpc = f'https://base-mainnet.infura.io/v3/{infura_key}'

    # Connect to Node
    w3 = Web3(Web3.HTTPProvider(base_rpc))

    return w3

def create_contract_instance(w3, address, contract_abi):
    contract_instance = w3.eth.contract(
        address=Web3.to_checksum_address(address),
        abi=contract_abi
    )
    return contract_instance

# Utility
def convert_to_wei(amount, decimals=18):
    """
    Convert amount to Wei based on decimal places
    
    Args:
        amount: Amount to convert
        decimals: Number of decimal places (default 18 for ETH)
    
    Returns:
        Amount in Wei
    """
    return int(Decimal(str(amount)) * Decimal('10') ** decimals)

def convert_from_wei(amount_in_wei, decimals=18):
    """
    Convert Wei amount to decimal based on decimal places
    
    Args:
        amount_in_wei: Amount in Wei to convert
        decimals: Number of decimal places (default 18 for ETH)
    
    Returns:
        Decimal amount
    """
    return Decimal(str(amount_in_wei)) / Decimal('10') ** decimals

# Body Funcs
def calculate_min_amount_out(amount_out, slippage_tolerance):
    """
    Calculate minimum amount out based on slippage tolerance
    
    Args:
        amount_out: Expected output amount in Wei
        slippage_tolerance: Slippage tolerance percentage (e.g., 0.5 for 0.5%)
        
    Returns:
        Minimum amount out in Wei accounting for slippage
    """
    amount_out_decimal = Decimal(str(amount_out))
    slippage_decimal = Decimal(str(slippage_tolerance)) / Decimal('100')
    
    min_amount_out = amount_out_decimal * (Decimal('1') - slippage_decimal)
    
    return int(min_amount_out)

def get_amounts_out(amount_in, pair_contract, router02_contract, slippage_tolerance=0.5):
    """
    Get swap amounts with slippage calculation
    
    Args:
        amount_in: Input amount in Wei
        pair_contract: Uniswap V2 pair contract instance
        router02_contract: Router02 contract instance
        slippage_tolerance: Maximum allowed slippage percentage (default 0.5%)
    """
    token0_address = pair_contract.functions.token0().call() # Virtual
    token1_address = pair_contract.functions.token1().call() # Luna

    # Get amounts out for token0 to token1
    amounts_0_to_1 = router02_contract.functions.getAmountsOut(
        amount_in,
        [token0_address, token1_address]
    ).call()
    
    # Calculate minimum amount out based on slippage tolerance
    min_amount_out = calculate_min_amount_out(amounts_0_to_1[1], slippage_tolerance)
        
    # Convert to readable format for display
    amount_0_to_1 = convert_from_wei(amounts_0_to_1[1])
    min_amount_0_to_1 = convert_from_wei(min_amount_out)
    input_amount = convert_from_wei(amount_in)
    
    print(f"\nSwap Quote using Router02:")
    print(f"Input: {input_amount} Token0")
    print(f"Expected Output: {amount_0_to_1} Token1")
    print(f"Minimum Output ({slippage_tolerance}% slippage): {min_amount_0_to_1} Token1")
    
    return {
        'expected_amount_out': amounts_0_to_1[1],
        'min_amount_out': min_amount_out
    }

def main():
    w3 = init_web3()

    # Contract addresses
    base_luna_virt_pair = '0xa8e64FB120CE8796594670BAE72279C8aA1e5359'
    router02_address = '0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24'

    # Create contract instances
    pair_contract = create_contract_instance(w3, base_luna_virt_pair, v2_lp_abi)
    router02_contract = create_contract_instance(w3, router02_address, router02_abi)

    # Convert 1 token0 to Wei (assuming 18 decimals)
    amount_in = convert_to_wei(1)
    
    # Get amounts with 0.5% slippage tolerance
    swap_amounts = get_amounts_out(amount_in, pair_contract, router02_contract, slippage_tolerance=0.5)

if __name__ == "__main__":
    main()