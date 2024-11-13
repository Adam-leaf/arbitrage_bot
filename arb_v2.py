# Base Imports
import os
import math
import asyncio
import time
from typing import Tuple, Optional

# External Imports
import requests
from config import token_configs
from funcs.base_odos import *
from funcs.sol_jupiter import *
from funcs import save_trade_data
from logging_utility import logger

ARB_PERCENT = 4 # Adjust to how aggresive the arbs needs to be
MINIMUM_TOKEN = 10000 # Decides what the minimum token value to swap $LUNA
MAX_TOKEN = 50000
INCREMENT = 100

MONITOR_DELAY = 1
MONITOR_IMPACT_MIN = 10000
PROFIT_TRESHOLD = 0

""" Utility """

def jup_find_price(token_address):
    base_url = "https://api.jup.ag/price/v2"
    
    try:
        response = requests.get(f"{base_url}?ids={token_address}")
        response.raise_for_status()
        
        data = response.json()
        price = float(data["data"][token_address]["price"])

        return price
        
    except requests.RequestException as e:
        print(f"Error fetching price: {e}")
        raise
    except KeyError as e:
        print(f"Error parsing response: {e}")
        raise

def parse_price(data, source, out_decimals=6, init_amount=10000.0):
    """
    Parse price data from different sources and normalize the price impact
    
    Args:
        data: Response data from the quote
        source: Source of the quote ("Jupiter" or "Odos")
        out_decimals: Decimals for the output token
        init_amount: Base amount used for the quote (default 1000.0)
    
    Returns:
        tuple: (price_per_token, price_impact_percentage)
    """
    
    try:
        if source == "Jupiter":
            total_out_amount = float(data['outAmount']) / (10 ** out_decimals)
            price_per_token = total_out_amount / init_amount

            # This is needed to change from TOKEN/SOL -> TOKEN/USD 
            sol_price = jup_find_price(token_configs["solana"]['tokens']['sol']['address'])
            token_price = price_per_token*sol_price

            # Jupiter impact is not in percentage need to *100
            impact = float(data['priceImpactPct'])*100

            # Find how much 1 LUNA -> SOL
            sol_luna_solana = price_per_token
            
            return token_price, impact, sol_luna_solana
        
        elif source == "Odos":
            total_out_amount = float(data['outValues'][0])
            price_per_token = total_out_amount / init_amount
            # Convert Odos impact to positive percentage, it is in percent
            impact = abs(float(data['priceImpact']))

            # Find how much 1 LUNA -> VIRTUAL
            init_out_amount = float(data['outAmounts'][0]) / (10 ** out_decimals)
            base_luna_virtual = init_out_amount/init_amount # Per token of LUNA, how many VIRTUAL

            return price_per_token, impact, base_luna_virtual
            
        else:
            print("Invalid Source")
            return None, None
    except Exception as e:
        print(f"Error parsing price for {source}: {e}")
        return None, None

def calc_balanced_swap(base_price_luna_virtual, sol_price_luna_solana, base_usd_price, solana_usd_price, base_impact, sol_impact, trade_action):
    """
    Calculate swap amount that ensures equal LUNA amounts on both sides while accounting for price impact
    
    Args:
        base_price_luna_virtual: Price of LUNA in terms of VIRTUAL tokens
        sol_price_luna_solana: Price of LUNA in terms of SOLANA tokens
        base_usd_price: Price of 1 LUNA on BASE
        solana_usd_price: Price of 1 LUNA on SOLANA
        base_impact: Price impact percentage for base token (0.3 means 0.3%)
        sol_impact: Price impact percentage for sol token (0.3 means 0.3%)
        trade_action: Either 'buy_base_sell_sol' or 'buy_sol_sell_base'
        
    Returns:
        tuple: (luna_amount, virtual_amount, solana_amount, expected_profit_usd)
    """
    # Convert impact from percentage to normalized decimals
    base_impact = (base_impact / 100) / math.sqrt(MONITOR_IMPACT_MIN)
    sol_impact = (sol_impact / 100) / math.sqrt(MONITOR_IMPACT_MIN)

    if trade_action == 'buy_base_sell_sol':
        # For buy_base_sell_sol:
        # VIRTUAL -> LUNA -> SOLANA
        # 
        # Amount of LUNA received from base (including impact):
        # luna_amount = (virtual_amount/base_price_luna_virtual) * (1 - base_impact*√x)
        #
        # Amount of LUNA sold on sol side (including impact):
        # luna_amount = x
        
        for x in range(MINIMUM_TOKEN, MAX_TOKEN, INCREMENT):

            virtual_usd = base_usd_price/base_price_luna_virtual
            solana_usd = solana_usd_price / sol_price_luna_solana

            # Calculate required VIRTUAL tokens for base side
            virtual_amount = (x * base_price_luna_virtual) / (1 - base_impact * math.sqrt(x))
            
            # Calculate expected SOLANA tokens from sol side
            solana_amount = x * sol_price_luna_solana * (1 - sol_impact * math.sqrt(x))
            
            # Convert to USD for profit calculation
            virtual_value_usd = virtual_amount * virtual_usd
            solana_value_usd = solana_amount * solana_usd
            
            # Check if profitable in USD terms
            profit_usd = solana_value_usd - virtual_value_usd
            
            if profit_usd > 0:
                logger.info(f"\n--------------------------------------\n"   
                f"Calculation for Ideal Swap (Before Quote and Transaction):\n"
                f"LUNA Amount: {x:.4f}\n"
                f"VIRTUAL Amount (spent): {virtual_amount:.4f} (${virtual_value_usd:.2f})\n"
                f"SOLANA Amount (received): {solana_amount:.4f} (${solana_value_usd:.2f})\n"
                f"Expected Profit (USD): ${profit_usd:.4f}\n"
                f"Base Impact: {base_impact * math.sqrt(x) * 100:.4f}%\n"
                f"Sol Impact: {sol_impact * math.sqrt(x) * 100:.4f}%\n"
                f"--------------------------------------")

                return x, virtual_amount, solana_amount, profit_usd
                
    else:  # buy_sol_sell_base
        # For buy_sol_sell_base:
        # SOLANA -> LUNA -> VIRTUAL
        
        for x in range(MINIMUM_TOKEN, MAX_TOKEN, INCREMENT):

            virtual_usd = base_usd_price/base_price_luna_virtual
            solana_usd = solana_usd_price / sol_price_luna_solana

            # Calculate required SOLANA tokens for sol side
            solana_amount = (x * sol_price_luna_solana) / (1 - sol_impact * math.sqrt(x))
            
            # Calculate expected VIRTUAL tokens from base side
            virtual_amount = x * base_price_luna_virtual * (1 - base_impact * math.sqrt(x))
            
            # Convert to USD for profit calculation
            virtual_value_usd = virtual_amount * virtual_usd
            solana_value_usd = solana_amount * solana_usd
            
            profit_usd = virtual_value_usd - solana_value_usd
            
            if profit_usd > 0:
                logger.info(f"\n--------------------------------------\n"   
                f"Calculation for Ideal Swap (Before Quote and Transaction):\n"
                f"LUNA Amount: {x:.4f}\n"
                f"SOLANA Amount (spent): {solana_amount:.4f} (${solana_value_usd:.2f})\n"
                f"VIRTUAL Amount (received): {virtual_amount:.4f} (${virtual_value_usd:.2f})\n"
                f"Expected Profit (USD): ${profit_usd:.4f}\n"
                f"Base Impact: {base_impact * math.sqrt(x) * 100:.4f}%\n"
                f"Sol Impact: {sol_impact * math.sqrt(x) * 100:.4f}%\n"
                f"--------------------------------------")

                return x, virtual_amount, solana_amount, profit_usd
    
    return 0, 0, 0, 0

""" Monitoring """
async def price_checker(delay: int = 1, init_amount: float = 1000.0):
    """
    Modified price checker to use balanced swap calculation.
    Skips rounds where either impact is 0.
    """
    base = token_configs["base"]
    sol = token_configs["solana"]
    
    try:
        # Run both quotes concurrently using gather
        quote_base, quote_sol = await asyncio.gather(
            quote_odos(
                base["tokens"]["luna"]["address"],
                base["tokens"]["virtual"]["address"],  # changed
                init_amount,
                base["tokens"]["luna"]["decimals"],
            ),
            quote_jupiter(
                sol["tokens"]["luna"]["address"],
                sol["tokens"]["sol"]["address"], # changed
                init_amount,  
                sol["tokens"]["luna"]["decimals"]
            )
        )
   
        # Parse prices from both sources
        base_price, base_impact , base_luna_virtual = parse_price(quote_base, "Odos", base["tokens"]["virtual"]["decimals"], init_amount=init_amount)
        sol_price, sol_impact, sol_luna_solana = parse_price(quote_sol, "Jupiter", sol["tokens"]["sol"]["decimals"], init_amount=init_amount)

        if base_price and sol_price:
            # Check for zero impacts - skip this round if found
            if base_impact == 0 or sol_impact == 0:
                logger.warning(f"\n--------------------------------------\n"
                f"Warning: Zero impact detected, skipping round\n"
                f"Base Impact: {base_impact}\n"
                f"Sol Impact: {sol_impact}\n"
                f"--------------------------------------")
                
                await asyncio.sleep(delay)
                return False, None, 0, 0

            avg_price = (base_price + sol_price) / 2
            price_diff = abs(base_price - sol_price) / avg_price * 100
            
            logger.info(f"\n--------------------------------------\n"
            f"Base Price: ${base_price:.6f}\n"
            f"Solana Price: ${sol_price:.6f}\n"
            f"Price Difference: {price_diff:.2f}%\n"
            f"Base Impact ({MONITOR_IMPACT_MIN}): {base_impact}\n"
            f"Sol Impact ({MONITOR_IMPACT_MIN}): {sol_impact}\n"
            f"--------------------------------------")

            # Determine trading action and calculate balanced amounts
            if base_price < sol_price:
                trade_action = "buy_base_sell_sol"
            else:
                trade_action = "buy_sol_sell_base"
            
            if price_diff >= ARB_PERCENT:
                logger.info(f"Arbitrage opportunity found! Action: {trade_action}")

                # Calculate balanced amounts
                luna_amount, virtual_amount, solana_amount, expected_profit_usd = calc_balanced_swap(
                    base_luna_virtual, sol_luna_solana, base_price, sol_price, base_impact, sol_impact, trade_action
                )

                # Can create a minimum profit variable with expected_profit_usd

                
                if luna_amount > 0 and expected_profit_usd > PROFIT_TRESHOLD:
                    logger.info(f"Expected Profit: {expected_profit_usd}")

                    # Return the balanced amounts
                    return True, trade_action, luna_amount, virtual_amount if trade_action == "buy_base_sell_sol" else solana_amount
                
                else:
                    logger.info(f"Calculated Profit is Lower than {PROFIT_TRESHOLD}: {expected_profit_usd}")
        
        await asyncio.sleep(delay)
        
    except Exception as e:
        logger.error(f"Error in price checker: {e}")
        await asyncio.sleep(delay)
        
    return False, None, 0, 0

def analyze_arb_quotes(quote_base, quote_sol, trade_action):
    """
    Analyze arbitrage quotes and calculate key metrics
    
    Args:
        quote_base: Quote response from Odos
        quote_sol: Quote response from Jupiter
        trade_action: Either 'buy_base_sell_sol' or 'buy_sol_sell_base'
        
    Returns:
        dict: Dictionary containing all key metrics
    """

    base = token_configs["base"]
    sol = token_configs["solana"]

    base_luna_dec = base["tokens"]["luna"]["decimals"]
    sol_luna_dec = sol["tokens"]["luna"]["decimals"]

    sol_solana_dec = sol["tokens"]["sol"]["decimals"]
    sol_solana_address = sol["tokens"]["sol"]["address"]

    try:
        # Initialize variables based on trade direction
        if trade_action == 'buy_base_sell_sol':
            # USDC -> LUNA (Base) and LUNA -> USDC (Sol)
            luna_base = float(quote_base['outAmounts'][0]) / (10 ** base_luna_dec)  # LUNA received from Base
            usdc_base = float(quote_base['inValues'][0])   # USDC spent on Base
            
            luna_sol = float(quote_sol['inAmount']) / (10 ** sol_luna_dec)  # LUNA spent on Sol

            sol_amount = float(quote_sol['outAmount']) / (10 ** sol_solana_dec)
            solana_price = jup_find_price(sol_solana_address)

            usdc_sol = float(sol_amount) * (solana_price) # What is the SOL received, value_usd
            
        else:  # buy_sol_sell_base
            # LUNA -> USDC (Base) and USDC -> LUNA (Sol)
            luna_base = float(quote_base['inAmounts'][0]) / (10 ** base_luna_dec)   # LUNA spent on Base
            usdc_base = float(quote_base['outValues'][0])  # USDC received from Base 
            
            luna_sol = float(quote_sol['outAmount']) / (10 ** sol_luna_dec)  # LUNA received from Sol
            
            sol_amount = float(quote_sol['inAmount']) / (10 ** sol_solana_dec)
            solana_price = jup_find_price(sol_solana_address)

            usdc_sol = float(sol_amount) * (solana_price) # What is the SOL spent, value_usd
        
        # Calculate profit (in USDC)
        if trade_action == 'buy_base_sell_sol':
            profit = usdc_sol - usdc_base
        else:
            profit = usdc_base - usdc_sol
            
        # Create results dictionary
        results = {
            "action": trade_action,
            "luna_sol": luna_sol,
            "luna_base": luna_base,
            "usdc_sol": usdc_sol,
            "usdc_base": usdc_base,
            "profit_usdc": profit,
        }
        
        # Print detailed analysis
        logger.info(f"\n=== Arbitrage Analysis ===\n"
        f"Action: {trade_action}\n"
        f"LUNA Sol: {luna_sol:.6f}\n"
        f"LUNA Base: {luna_base:.6f}\n"
        f"USDC Sol: ${usdc_sol:.2f}\n"
        f"USDC Base: ${usdc_base:.2f}\n"
        f"Profit: ${profit:.2f}\n"
        f"========================")
                    
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing arbitrage quotes: {e}")
        return None

""" Transactions """
async def execute_arbitrage(
    trade_action: str,
    amount_sell: float,
    amount_buy: float,
    base_priv_key: str,
    sol_priv_key: str
) -> Tuple[bool, Optional[str]]:
    """
    Execute the arbitrage trade across both chains
    Returns (success, error_message)
    """
    try:
        # Get addresses from config
        base = token_configs["base"]
        sol = token_configs["solana"]

        # Init tokens based on trade direction
        if trade_action == 'buy_base_sell_sol':
            base_in = base["tokens"]["virtual"]["address"] # changed
            base_out = base["tokens"]["luna"]["address"]
            base_in_dec = base["tokens"]["virtual"]["decimals"] # changed
            base_amount = amount_buy

            sol_in = sol["tokens"]["luna"]["address"]
            sol_out = sol["tokens"]["sol"]["address"] # changed
            sol_in_dec = sol["tokens"]["luna"]["decimals"]
            sol_amount = amount_sell

        else:  # buy_sol_sell_base
            base_in = base["tokens"]["luna"]["address"]
            base_out = base["tokens"]["virtual"]["address"] # changed
            base_in_dec = base["tokens"]["luna"]["decimals"]
            base_amount = amount_sell

            sol_in = sol["tokens"]["sol"]["address"] # changed
            sol_out = sol["tokens"]["luna"]["address"]
            sol_in_dec = sol["tokens"]["sol"]["decimals"] # changed
            sol_amount = amount_buy

        # Initialize wallet addresses
        base_user_addrs = '0x018C3FB97AB31e02C4Dc215B6b0b662A4dDf9428'
        sol_user_addrs = '9H9kY3pj1t2RdYH9cGDPnXgqh2F7BJvBehboktgVsj1c'

        try:
            # Get quotes
            quote_base, quote_sol = await asyncio.gather(
                quote_odos(base_in, base_out, base_amount, base_in_dec, user_addrs=base_user_addrs),
                quote_jupiter(sol_in, sol_out, sol_amount, sol_in_dec)
            )

            if not quote_base or not quote_sol:
                return False, "Failed to get valid quotes from both exchanges"
        
        except Exception as e:
            return False, f"Error getting quotes: {str(e)}"

        # Analyze the quotes
        arb_analysis = analyze_arb_quotes(quote_base, quote_sol, trade_action)
        if not arb_analysis or arb_analysis['profit_usdc'] <= 0:
            return False, "Arbitrage no longer profitable after final quote"

        # Save trade data - Debug
        #save_trade_data(quote_base, 'base.json')
        #save_trade_data(quote_sol, 'sol.json')

        try:

            # Assemble transactions
            odos_assembled, jup_assembled = await asyncio.gather(
                assemble_odos(base_user_addrs, quote_base),
                swap_jupiter(sol_user_addrs, quote_sol)
            )

            if not odos_assembled or not jup_assembled:
                return False, "Failed to assemble transactions"

        except Exception as e:
            return False, f"Error assembling transactions: {str(e)}"

        # Check approvals
        ODOS_ROUTER_V2 = base["odos_routerV2"]
        needs_approval = check_token_approval(base_in, base_user_addrs, ODOS_ROUTER_V2)

        if needs_approval:
            approval_success = send_infinite_approval(base_in, ODOS_ROUTER_V2)
            if not approval_success:
                return False, "Token approval failed"
        
        try:
            # Execute transactions
            base_tx_hash, solana_tx_hash = await asyncio.gather(
                execute_odos(odos_assembled, base_priv_key),
                execute_jupiter(jup_assembled, sol_priv_key)
            )

            if not base_tx_hash or not solana_tx_hash:
                    return False, "Failed to get transaction hashes"
                
        except Exception as e:
            return False, f"Error executing transactions: {str(e)}"

        logger.info(f"View on Basescan: https://basescan.org/tx/0x{base_tx_hash}")
        logger.info(f"View on Solscan: https://solscan.io/tx/{solana_tx_hash}")

        return True, None

    except Exception as e:
        return False, f"Error executing arbitrage: {str(e)}"

async def main():
    """
    Main function that runs the continuous arbitrage monitoring loop
    """
    # Get private keys from environment
    base_priv_key = os.getenv('BASE_PRIVATE_KEY')
    sol_priv_key = os.getenv('SOL_PRIVATE_KEY')
    
    if not base_priv_key or not sol_priv_key:
        logger.error("Error: Private keys not found in environment variables")
        return

    logger.info("Starting continuous arbitrage monitor...")
    
    while True:
        try:
            # Check for arbitrage opportunity
            arbitrage_check, trade_action, amount_in, amount_out = await price_checker(delay=1)

            if arbitrage_check:
                logger.info(f"\n!!! POSITIVE PROFIT ON ARBITRAGE !!!\n"
                f"--------------------------------------\n"
                f"Trade action: {trade_action}\n"
                f"Amount in: {amount_in}\n"
                f"Amount Out (Buy): {amount_out}\n"
                f"--------------------------------------")
                
                # Add validation before execution
                if not all([trade_action, amount_in, amount_out]):
                    logger.error("Invalid trade parameters detected")
                    logger.error(f"trade_action: {trade_action}")
                    logger.error(f"amount_in: {amount_in}")
                    logger.error(f"amount_out: {amount_out}")
                    continue

                # Execute the arbitrage
                success, error = await execute_arbitrage(
                    trade_action,
                    amount_in,
                    amount_out,
                    base_priv_key,
                    sol_priv_key
                )
                
                if success:
                    logger.info(f"!!! ARBITRAGE Complete !!!")
                else:
                    logger.error(f"Arbitrage execution failed: {error}")

                # Add a small delay after execution before resuming monitoring
                logger.info(f"Waiting {MONITOR_DELAY} seconds before resuming monitoring...")
                await asyncio.sleep(MONITOR_DELAY)
            else:
                # No arbitrage opportunity found, continue monitoring
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            # Add longer delay on error to prevent rapid retries
            logger.error("Error occurred, waiting 5 seconds before retrying...")
            await asyncio.sleep(5)
            continue

        # Optional: Add periodic status update
        if time.time() % 60 < 1:  # Approximately every minute
            logger.info(f"\n=== BOT STATUS UPDATE ===\n"
            f"Status: Running\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Activity: Monitoring for arbitrage opportunities\n"
            f"=======================")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"\nBot stopped due to error: {str(e)}")