"""Azure client helpers (Cosmos, Blob, Service Bus)."""

from __future__ import annotations

from .config import (
    COSMOS_CONTAINER,
    COSMOS_DATABASE,
    COSMOS_ENDPOINT,
    COSMOS_KEY,
    QUEUE_NAME,
    RESULTS_ACCOUNT_URL,
    RESULTS_CONNECTION_STRING,
    RESULTS_CONTAINER,
    SERVICE_BUS_CONNECTION,
    logger,
)

_cosmos_client = None
_blob_service_client = None


def get_cosmos_client():
    global _cosmos_client
    if _cosmos_client is None:
        if not COSMOS_ENDPOINT or not COSMOS_KEY:
            raise RuntimeError("Cosmos DB configuration missing")
        from azure.cosmos import CosmosClient

        _cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    return _cosmos_client


def get_jobs_container():
    client = get_cosmos_client()
    database = client.get_database_client(COSMOS_DATABASE)
    return database.get_container_client(COSMOS_CONTAINER)


def get_blob_service_client():
    global _blob_service_client
    if _blob_service_client is None:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        if RESULTS_CONNECTION_STRING:
            _blob_service_client = BlobServiceClient.from_connection_string(
                RESULTS_CONNECTION_STRING
            )
        elif RESULTS_ACCOUNT_URL:
            _blob_service_client = BlobServiceClient(
                account_url=RESULTS_ACCOUNT_URL,
                credential=DefaultAzureCredential(),
            )
        else:
            raise RuntimeError("Blob storage configuration missing")
    return _blob_service_client


def get_results_container_client():
    from azure.core.exceptions import ResourceExistsError

    client = get_blob_service_client()
    container = client.get_container_client(RESULTS_CONTAINER)
    try:
        container.create_container()
    except ResourceExistsError:
        pass
    return container


def get_service_bus_client():
    from azure.servicebus import ServiceBusClient

    if not SERVICE_BUS_CONNECTION:
        raise RuntimeError("Service Bus connection string missing")
    logger.debug("Using Service Bus queue: %s", QUEUE_NAME)
    return ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION)
