"""Setting up the ingest client."""
from __future__ import annotations

from collections.abc import Mapping
import io
import logging
from typing import Any

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.data_format import DataFormat
from azure.kusto.ingest import (
    IngestionProperties,
    ManagedStreamingIngestClient,
    QueuedIngestClient,
    StreamDescriptor,
)

from .const import (
    CONF_ADX_CLUSTER_INGEST_URI,
    CONF_ADX_DATABASE_NAME,
    CONF_ADX_TABLE_NAME,
    CONF_APP_REG_ID,
    CONF_APP_REG_SECRET,
    CONF_AUTHORITY_ID,
    CONF_USE_FREE,
)

_LOGGER = logging.getLogger(__name__)

# Suppress very verbose logging from client
logger = logging.getLogger("azure")
logger.setLevel(logging.WARNING)


class AzureDataExplorerClient:
    """Class for Azure Data Explorer Client."""

    def __init__(self, data: Mapping[str, Any]) -> None:
        """Create the right class."""

        self._cluster_ingest_uri = data[CONF_ADX_CLUSTER_INGEST_URI]
        self._database = data[CONF_ADX_DATABASE_NAME]
        self._table = data[CONF_ADX_TABLE_NAME]
        self._client_id = data[CONF_APP_REG_ID]
        self._client_secret = data[CONF_APP_REG_SECRET]
        self._authority_id = data[CONF_AUTHORITY_ID]
        self._use_queued_ingestion = data[CONF_USE_FREE]

        self._cluster_query_uri = self._cluster_ingest_uri.replace(
            "https://ingest-", "https://"
        )

        self._ingestion_properties = IngestionProperties(
            database=self._database,
            table=self._table,
            data_format=DataFormat.MULTIJSON,
            ingestion_mapping_reference="ha_json_mapping",
        )

        # Create cLients for ingesting and querying data
        kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
            self._cluster_ingest_uri,
            self._client_id,
            self._client_secret,
            self._authority_id,
        )

        if self._use_queued_ingestion is True:
            # Queded is the only option supported on free tear of ADX
            self.write_client = QueuedIngestClient(kcsb)
        else:
            self.write_client = ManagedStreamingIngestClient.from_dm_kcsb(kcsb)

        self.query_client = KustoClient(kcsb)

    def test_connection(self) -> None:
        """Test connection, will throw Exception when it cannot connect."""

        query = f"{self._table} | take 1"

        self.query_client.execute_query(self._database, query)

    def ingest_data(self, adx_events: str) -> None:
        """Send data to Axure Data Explorer."""

        bytes_stream = io.StringIO(adx_events)
        stream_descriptor = StreamDescriptor(bytes_stream)

        self.write_client.ingest_from_stream(
            stream_descriptor, ingestion_properties=self._ingestion_properties
        )
