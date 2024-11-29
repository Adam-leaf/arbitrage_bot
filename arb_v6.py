# Base Imports
import os
import asyncio
import time
from typing import Tuple, Optional

# External Imports
import requests
from config import token_configs
from funcs.base_odos import *
from funcs.sol_jupiter import *
from logging_utility import logger
from funcs import save_trade_data
from utility import get_raydium_lp_liquidity, query_uniswap_liquidity

ARB_PERCENT = 0.01 # Adjust to how aggresive the arbs needs to be
MONITOR_DELAY = 1
PROFIT_TRESHOLD = 0

TARGET_TOKEN = "sam"
TARGET_CLOSE = 1 # 1 means 100% close fully
SIZE_WEIGHT = 0.7

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

def parse_price(data, source, out_decimals=6):
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
            price_per_token = float(data['outAmount']) / (10 ** out_decimals)

            # This is needed to change from TOKEN/SOL -> TOKEN/USD 
            sol_price = jup_find_price(token_configs["solana"]['tokens']['sol']['address'])
            token_price = price_per_token*sol_price

            # Find how much 1 LUNA -> SOL
            sol_luna_solana = price_per_token
            
            return token_price, sol_luna_solana
        
        elif source == "Odos":
            total_out_amount = float(data['outValues'][0])
            price_per_token = total_out_amount / 1

            # Find how much 1 LUNA -> VIRTUAL
            base_luna_virtual = float(data['outAmounts'][0]) / (10 ** out_decimals) # Per token of LUNA, how many VIRTUAL

            return price_per_token, base_luna_virtual
            
        else:
            print("Invalid Source")
            return None, None
    except Exception as e:
        print(f"Error parsing price for {source}: {e}")
        return None, None

def calc_swap(base_price_luna_virtual, sol_price_luna_solana, base_usd_price, solana_usd_price, trade_action, target_close = TARGET_CLOSE):
    """
    Calculate swap amount that ensures equal LUNA amounts on both sides while accounting for price impact
    
    Args:
        base_price_luna_virtual: LUNA/VIRTUAL price
        sol_price_luna_solana: LUNA/SOLANA price
        base_usd_price: LUNA/USD price on BASE
        solana_usd_price: LUNA/USD price on SOLANA


        base_impact: Price impact percentage for base token (0.3 means 0.3%)
        sol_impact: Price impact percentage for sol token (0.3 means 0.3%)
        trade_action: Either 'buy_base_sell_sol' or 'buy_sol_sell_base'
        
    Returns:
        tuple: (luna_amount, virtual_amount, solana_amount, expected_profit_usd)
    """

    # 1. Calculate price gap
    price_gap = abs(base_usd_price - solana_usd_price)
    target_gap = price_gap * (1 - target_close) # remaining gap after trade
    price_move = (price_gap - target_gap) / 2 # how much each side should move
    
    virtual_token_usd_price = base_usd_price / base_price_luna_virtual
    solana_token_usd_price = solana_usd_price / sol_price_luna_solana

    logger.info(f"\n\n=== Initial Parameters ===\n"
    f"Base Price {TARGET_TOKEN}/VIRTUAL: {base_price_luna_virtual:.6f}\n"
    f"Sol Price {TARGET_TOKEN}/SOLANA: {sol_price_luna_solana:.6f}\n"
    f"Base USD Price: ${base_usd_price:.6f}\n"
    f"Solana USD Price: ${solana_usd_price:.6f}\n"
    f"Trade Action: {trade_action}"
    f"\n\n=== Gaps Calc ===\n"
    f"Current Price Gap: ${price_gap:.8f}\n"
    f"Required Price Move Per Side: ${price_move:.8f}")

    # 2. Get LP Liquidity USD Value
    base_lp_address = token_configs["base"]["tokens"][TARGET_TOKEN]["lp_address"]
    sol_lp_address = token_configs["solana"]["tokens"][TARGET_TOKEN]["lp_address"]
    
    # *Base Uniswap Finding Pool Depth
    base_pool_data = query_uniswap_liquidity(base_lp_address)
    base_virtual_dec = token_configs["base"]["tokens"]["virtual"]["decimals"]
    base_token0_reserve = float(base_pool_data['reserve0'])/ (10 ** base_virtual_dec) # Token0 - VIRTUALS: Token1 - LUNA
    
    # *Calculate pool token amounts from USD depth
    base_pool_usd_depth = base_token0_reserve * virtual_token_usd_price * 2  # Total pool value
    sol_pool_usd_depth = get_raydium_lp_liquidity(sol_lp_address)

    logger.info(f"\n\n=== Pool Information ===\n"
    f"Base Pool USD Depth: ${base_pool_usd_depth:.2f}\n" 
    f"Solana Pool USD Depth: ${sol_pool_usd_depth:.2f}\n"
    f"VIRTUAL Token USD Price: ${virtual_token_usd_price:.6f}\n"
    f"SOLANA Token USD Price: ${solana_token_usd_price:.6f}")

    # 3. Calculate LUNA amount needed to close gap
    if trade_action == 'buy_base_sell_sol':

        # Uniswap V2 (Base)
        target_base_price = base_usd_price + price_move
        base_token0_reserve = float(base_pool_data['reserve0']) / (10 ** base_virtual_dec)  # VIRTUAL
        virtual_pool_liquidity = base_token0_reserve * virtual_token_usd_price # Approximate per-token liquidity (Only 1 side)

        # Calculate amount of LUNA to buy to achieve target_base_price
        delta_luna_base = (price_move / base_usd_price) * virtual_pool_liquidity

        # Raydium (Solana)
        target_sol_price = solana_usd_price - price_move
        sol_pool_liquidity = sol_pool_usd_depth / 2  # Approximate per-token liquidity

        # Calculate amount of LUNA to sell to achieve target_sol_price
        delta_luna_sol = (price_move / solana_usd_price) * sol_pool_liquidity  # LUNA to sell on Solana

        price_impact_base = target_base_price/base_usd_price * 100 - 100
        price_impact_sol = target_sol_price/solana_usd_price * 100 - 100

        logger.info(f"\n\n=== Required Moves ===\n"
                    f"Base: Need to BUY {delta_luna_base:.4f} {TARGET_TOKEN} to move price "
                    f"\nPrice Impact: {price_impact_base}"
                    f"\n${base_usd_price:.6f} -> ${target_base_price:.6f}"
                    f"\nSol: Need to SELL {delta_luna_sol:.4f} {TARGET_TOKEN} to move price "
                    f"${solana_usd_price:.6f} -> ${target_sol_price:.6f}"
                    f"\nPrice Impact: {price_impact_sol}")
        
    elif trade_action == 'buy_sol_sell_base':
        # Uniswap V2 (Base)
        target_base_price = base_usd_price - price_move
        base_token0_reserve = float(base_pool_data['reserve0']) / (10 ** base_virtual_dec)  # VIRTUAL
        virtual_pool_liquidity = base_token0_reserve * virtual_token_usd_price # Approximate per-token liquidity (Only 1 side)

        # Calculate amount of LUNA to buy to achieve target_base_price
        delta_luna_base = (price_move / base_usd_price) * virtual_pool_liquidity

        # Raydium (Solana)
        target_sol_price = solana_usd_price + price_move
        sol_pool_liquidity = sol_pool_usd_depth / 2
        delta_luna_sol = (price_move / solana_usd_price) * sol_pool_liquidity  # LUNA to buy on Solana

        price_impact_base = target_base_price/base_usd_price * 100 - 100
        price_impact_sol = target_sol_price/solana_usd_price * 100 - 100

        logger.info(f"\n\n=== Required Moves ===\n"
                    f"Base: Need to BUY {delta_luna_base:.4f} {TARGET_TOKEN} to move price "
                    f"\nPrice Impact: {price_impact_base}"
                    f"\n${base_usd_price:.6f} -> ${target_base_price:.6f}"
                    f"\nSol: Need to SELL {delta_luna_sol:.4f} {TARGET_TOKEN} to move price "
                    f"${solana_usd_price:.6f} -> ${target_sol_price:.6f}"
                    f"\nPrice Impact: {price_impact_sol}")

    else:
        raise ValueError("Invalid trade action. Use 'buy_base_sell_sol' or 'buy_sol_sell_base'.")

    # Take the smaller amount to ensure balanced swap
    #luna_amount = min(delta_luna_base, delta_luna_sol)
    #luna_amount = (delta_luna_base + delta_luna_sol) / 2

    larger_amount = max(delta_luna_base, delta_luna_sol)
    smaller_amount = min(delta_luna_base, delta_luna_sol)

    luna_amount = smaller_amount + (larger_amount - smaller_amount) * SIZE_WEIGHT

    # Calculate other token amounts
    virtual_amount = luna_amount * base_price_luna_virtual
    solana_amount = luna_amount * sol_price_luna_solana

    # Calculate USD amounts and expected profit
    base_usd_amount = luna_amount * base_usd_price  
    sol_usd_amount = luna_amount * solana_usd_price

    if trade_action == "buy_base_sell_sol":
        expected_profit_usd = sol_usd_amount - base_usd_amount # You get same amount but its cheaper on base, 
    elif trade_action == "buy_sol_sell_base":
        expected_profit_usd = base_usd_amount - sol_usd_amount
    else:
        expected_profit_usd = 0
    
    logger.info(f"\n\n=== Arbitrage Calculation ===\n"
                f"Target Price Move: ${price_move:.8f}\n"
                f"{TARGET_TOKEN} Amount: {luna_amount:.6f}\n"
                f"BASE - USD Value: ${base_usd_amount:.2f}\n"
                f"SOL - USD Value: ${sol_usd_amount:.2f}\n"
                f"Expected Profit: ${expected_profit_usd:.18f}")
    
    return luna_amount, virtual_amount, solana_amount, expected_profit_usd

""" Monitoring """
async def price_checker(delay: int = 1, init_amount: float = 1):
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
                base["tokens"][TARGET_TOKEN]["address"],
                base["tokens"]["virtual"]["address"], 
                init_amount,
                base["tokens"][TARGET_TOKEN]["decimals"],
            ),
            quote_jupiter(
                sol["tokens"][TARGET_TOKEN]["address"],
                sol["tokens"]["sol"]["address"], 
                init_amount,  
                sol["tokens"][TARGET_TOKEN]["decimals"]
            )
        )
   
        # Parse prices from both sources
        base_price, base_luna_virtual = parse_price(quote_base, "Odos", base["tokens"]["virtual"]["decimals"])
        sol_price, sol_luna_solana = parse_price(quote_sol, "Jupiter", sol["tokens"]["sol"]["decimals"])

        if base_price and sol_price:

            avg_price = (base_price + sol_price) / 2
            price_diff = abs(base_price - sol_price) / avg_price * 100
            
            logger.info(f"\n--------------------------------------\n"
            f"Base Price: ${base_price:.6f}\n"
            f"Solana Price: ${sol_price:.6f}\n"
            f"Price Difference: {price_diff:.2f}%\n"
            f"--------------------------------------")

            # Determine trading action and calculate balanced amounts
            if base_price < sol_price:
                trade_action = "buy_base_sell_sol"
            else:
                trade_action = "buy_sol_sell_base"
            
            if price_diff >= ARB_PERCENT:
                logger.info(f"Arbitrage opportunity found! Action: {trade_action}")

                # Calculate balanced amounts
                luna_amount, virtual_amount, solana_amount, expected_profit_usd = calc_swap(
                    base_luna_virtual, sol_luna_solana, base_price, sol_price, trade_action
                )
                
                # Can create a minimum profit variable with expected_profit_usd
                if luna_amount > 0 and expected_profit_usd > PROFIT_TRESHOLD:
                    # Return the balanced amounts
                    return True, trade_action, luna_amount, virtual_amount if trade_action == "buy_base_sell_sol" else solana_amount
                
                else:
                    logger.info(f"Expected Profit Lower Than Treshold of '{PROFIT_TRESHOLD} USD': {expected_profit_usd:.8f}")
        
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

    base_luna_dec = base["tokens"][TARGET_TOKEN]["decimals"]
    sol_luna_dec = sol["tokens"][TARGET_TOKEN]["decimals"]

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
        
        # Get Approx Token Prices
        base_luna_price = usdc_base/luna_base
        sol_luna_price = usdc_sol/luna_sol
        usd_main_token_diff = abs((luna_base*base_luna_price)-(luna_sol*sol_luna_price))

        # Calculate profit (in USDC)
        if trade_action == 'buy_base_sell_sol':
            profit = usdc_sol - usdc_base - usd_main_token_diff
        else:
            profit = usdc_base - usdc_sol - usd_main_token_diff
            
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
        f"{TARGET_TOKEN} Sol: {luna_sol:.6f}\n"
        f"{TARGET_TOKEN} Base: {luna_base:.6f}\n"
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
            base_out = base["tokens"][TARGET_TOKEN]["address"]
            base_in_dec = base["tokens"]["virtual"]["decimals"] # changed
            base_amount = amount_buy

            sol_in = sol["tokens"][TARGET_TOKEN]["address"]
            sol_out = sol["tokens"]["sol"]["address"] # changed
            sol_in_dec = sol["tokens"][TARGET_TOKEN]["decimals"]
            sol_amount = amount_sell

        else:  # buy_sol_sell_base
            base_in = base["tokens"][TARGET_TOKEN]["address"]
            base_out = base["tokens"]["virtual"]["address"] # changed
            base_in_dec = base["tokens"][TARGET_TOKEN]["decimals"]
            base_amount = amount_sell

            sol_in = sol["tokens"]["sol"]["address"] # changed
            sol_out = sol["tokens"][TARGET_TOKEN]["address"]
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
    
            # Save trade data - Debug
            save_trade_data(quote_base, 'base.json')
            save_trade_data(quote_sol, 'sol.json')

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
                logger.info(
                    f"\n\n[READY FOR ON-CHAIN]: "
                    f"SOLD = {amount_in} ({TARGET_TOKEN}) -> BUY USING = {amount_out} (Currency)"
                )
                
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