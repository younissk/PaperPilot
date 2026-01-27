#!/usr/bin/env python3
"""Local SQS poller for development.

This script long-polls the LocalStack SQS queue and invokes the worker handler
with SQS-shaped events, simulating the Lambda SQS trigger behavior locally.

Usage:
    python services/worker/local_poller.py

Environment variables:
    AWS_ENDPOINT_URL: LocalStack endpoint (default: http://localhost:4566)
    SQS_QUEUE_URL: Full queue URL (default: http://localhost:4566/000000000000/paperpilot-jobs-prod)
    JOBS_TABLE_NAME: DynamoDB table name (default: paperpilot-jobs-prod)
    RESULTS_BUCKET: S3 bucket for artifacts (default: paperpilot-artifacts-local)
    AWS_DEFAULT_REGION: AWS region (default: eu-central-1)
    LOG_LEVEL: Logging level (default: INFO)
"""

import logging
import os
import signal
import sys
import time
from typing import NoReturn

import boto3
from botocore.exceptions import ClientError

# Add the services/worker directory to the path so we can import the handler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from handler import handler

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration from environment
AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
SQS_QUEUE_URL = os.environ.get(
    "SQS_QUEUE_URL",
    "http://localhost:4566/000000000000/paperpilot-jobs-prod"
)
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-central-1")

# Polling configuration
WAIT_TIME_SECONDS = 20  # Long polling (max 20 seconds)
MAX_MESSAGES = 1  # Process one message at a time (like Lambda)
VISIBILITY_TIMEOUT = 300  # 5 minutes (match Lambda timeout)

# Graceful shutdown flag
shutdown_requested = False


def signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


def create_sqs_event(messages: list[dict]) -> dict:
    """Convert SQS messages to Lambda event format.
    
    Creates an event structure that matches what AWS Lambda receives
    from an SQS trigger.
    """
    records = []
    for msg in messages:
        record = {
            "messageId": msg.get("MessageId", ""),
            "receiptHandle": msg.get("ReceiptHandle", ""),
            "body": msg.get("Body", "{}"),
            "attributes": msg.get("Attributes", {}),
            "messageAttributes": msg.get("MessageAttributes", {}),
            "md5OfBody": msg.get("MD5OfBody", ""),
            "eventSource": "aws:sqs",
            "eventSourceARN": f"arn:aws:sqs:{AWS_REGION}:000000000000:paperpilot-jobs-prod",
            "awsRegion": AWS_REGION,
        }
        records.append(record)

    return {"Records": records}


def poll_and_process() -> None:
    """Poll SQS for messages and process them using the Lambda handler."""
    # Initialize SQS client with LocalStack endpoint
    sqs = boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
    )

    logger.info("Starting SQS poller")
    logger.info(f"  Queue URL: {SQS_QUEUE_URL}")
    logger.info(f"  Endpoint: {AWS_ENDPOINT_URL}")
    logger.info(f"  Region: {AWS_REGION}")
    logger.info("")

    while not shutdown_requested:
        try:
            # Long-poll for messages
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=MAX_MESSAGES,
                WaitTimeSeconds=WAIT_TIME_SECONDS,
                VisibilityTimeout=VISIBILITY_TIMEOUT,
                AttributeNames=["All"],
                MessageAttributeNames=["All"],
            )

            messages = response.get("Messages", [])

            if not messages:
                # No messages, continue polling
                continue

            logger.info(f"Received {len(messages)} message(s)")

            # Create Lambda-style event
            event = create_sqs_event(messages)

            # Invoke the handler (same code path as Lambda)
            try:
                result = handler(event, context=None)

                # Check for batch item failures
                failures = result.get("batchItemFailures", [])
                failed_ids = {f["itemIdentifier"] for f in failures}

                # Delete successfully processed messages
                for msg in messages:
                    msg_id = msg.get("MessageId", "")
                    receipt_handle = msg.get("ReceiptHandle", "")

                    if msg_id not in failed_ids:
                        # Message processed successfully, delete it
                        try:
                            sqs.delete_message(
                                QueueUrl=SQS_QUEUE_URL,
                                ReceiptHandle=receipt_handle,
                            )
                            logger.info(f"Deleted message {msg_id}")
                        except ClientError as e:
                            logger.error(f"Failed to delete message {msg_id}: {e}")
                    else:
                        # Message failed, leave it for retry
                        logger.warning(f"Message {msg_id} failed, will be retried")

            except Exception as e:
                logger.exception(f"Handler raised an exception: {e}")
                # Don't delete messages on handler exception

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AWS.SimpleQueueService.NonExistentQueue":
                logger.error(f"Queue does not exist: {SQS_QUEUE_URL}")
                logger.error("Make sure LocalStack is running and initialized.")
                logger.error("Run: make dev-infra")
                time.sleep(5)
            else:
                logger.error(f"SQS error: {e}")
                time.sleep(2)

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            time.sleep(2)

    logger.info("Poller shutdown complete")


def main() -> NoReturn:
    """Main entry point."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 60)
    print("PaperPilot Local Worker Poller")
    print("=" * 60)
    print("")
    print("This process polls LocalStack SQS and processes jobs locally.")
    print("Press Ctrl+C to stop.")
    print("")

    # Verify environment
    logger.info("Environment configuration:")
    logger.info(f"  JOBS_TABLE_NAME: {os.environ.get('JOBS_TABLE_NAME', 'paperpilot-jobs-prod')}")
    logger.info(f"  RESULTS_BUCKET: {os.environ.get('RESULTS_BUCKET', 'paperpilot-artifacts-local')}")
    logger.info(f"  SQS_QUEUE_URL: {SQS_QUEUE_URL}")
    logger.info(f"  AWS_ENDPOINT_URL: {AWS_ENDPOINT_URL}")
    print("")

    try:
        poll_and_process()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    sys.exit(0)


if __name__ == "__main__":
    main()
