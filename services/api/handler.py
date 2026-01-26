"""AWS Lambda handler for PaperPilot API.

Uses Mangum to adapt FastAPI/ASGI to Lambda's event format.
"""

import os
import logging

from mangum import Mangum

# Configure logging before importing the app
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import the FastAPI app from the existing codebase
from paperpilot.api.main import app

# Create the Mangum adapter
# - lifespan="off" because Lambda doesn't support ASGI lifespan events well
# - api_gateway_base_path="" handles API Gateway stage prefix if needed
handler = Mangum(app, lifespan="off")


def lambda_handler(event: dict, context) -> dict:
    """Lambda entry point.
    
    This wrapper allows for pre/post processing if needed.
    For most cases, you can use `handler` directly.
    """
    logger.debug(f"Received event: {event}")
    
    try:
        response = handler(event, context)
        logger.debug(f"Response status: {response.get('statusCode', 'unknown')}")
        return response
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        return {
            "statusCode": 500,
            "body": '{"error": "Internal server error"}',
            "headers": {"Content-Type": "application/json"},
        }
