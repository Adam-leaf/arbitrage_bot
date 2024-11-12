import logging
from datetime import datetime
import os

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Generate log filename with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = f'logs/arbitrage_bot_{timestamp}.log'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Create logger
logger = logging.getLogger('arbitrage_bot')