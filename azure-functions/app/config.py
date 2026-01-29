"""Configuration and logging for PaperPilot Azure Functions."""

from __future__ import annotations

import logging
import os

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("paperpilot.azure")

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
