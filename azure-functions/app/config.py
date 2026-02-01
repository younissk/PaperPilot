"""Configuration and logging for PaperNavigator Azure Functions."""

from __future__ import annotations

import logging
import os

from papernavigator.logging import configure_logging

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("papernavigator.azure")

# Ensure structlog-backed modules emit consistent logs in Azure Functions.
configure_logging(cli_mode=False, log_level=LOG_LEVEL)

COSMOS_ENDPOINT = os.environ.get("AZURE_COSMOS_ENDPOINT", "")
COSMOS_KEY = os.environ.get("AZURE_COSMOS_KEY", "")
COSMOS_DATABASE = os.environ.get("AZURE_COSMOS_DATABASE", "paperpilot")
COSMOS_CONTAINER = os.environ.get("AZURE_COSMOS_CONTAINER", "jobs")

SERVICE_BUS_CONNECTION = os.environ.get("AZURE_SERVICE_BUS_CONNECTION_STRING", "")
QUEUE_NAME = os.environ.get("AZURE_SERVICE_BUS_QUEUE_NAME", "paperpilot-jobs")

RESULTS_CONNECTION_STRING = (
    os.environ.get("AZURE_RESULTS_CONNECTION_STRING")
    or os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    or os.environ.get("AzureWebJobsStorage", "")
)
RESULTS_ACCOUNT_URL = os.environ.get("AZURE_STORAGE_ACCOUNT_URL", "")
RESULTS_CONTAINER = os.environ.get("AZURE_RESULTS_CONTAINER", "results")
RESULTS_PREFIX = os.environ.get("AZURE_RESULTS_PREFIX", "results").strip("/")

OPENAI_API_KEY_SECRET_NAME = os.environ.get("OPENAI_API_KEY_SECRET_NAME", "")
AZURE_KEY_VAULT_URL = os.environ.get("AZURE_KEY_VAULT_URL", "")

TTL_DAYS = int(os.environ.get("JOB_TTL_DAYS", "7"))
MAX_EVENTS = int(os.environ.get("MAX_JOB_EVENTS", "100"))

DEBUG = os.environ.get("DEBUG", "").lower() == "true"

# Report generation timeout (seconds) to avoid hanging jobs.
REPORT_TIMEOUT_SECONDS = int(os.environ.get("REPORT_TIMEOUT_SECONDS", "1200"))

# Azure Communication Services (Email)
ACS_CONNECTION_STRING = os.environ.get("AZURE_ACS_CONNECTION_STRING", "")
ACS_SENDER_ADDRESS = os.environ.get("AZURE_ACS_SENDER_ADDRESS", "noreply@papernavigator.com")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "https://papernavigator.com")
