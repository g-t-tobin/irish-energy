"""
Tests for EventBridge event publishing in ingestion functions
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

from src.ingestion.eirgrid_ingestion import lambda_handler as eirgrid_lambda_handler
from src.ingestion.openmeteo_ingestion import lambda_handler as openmeteo_lambda_handler
from src.common.config import Config


class TestEventPublishingEirGrid:
    """Test EventBridge event publishing for EirGrid ingestion"""

    def test_successful_ingestion_emits_completion_event(self):
        """Test that successful ingestion emits completion event"""
        with patch('src.ingestion.eirgrid_ingestion.boto3.client') as mock_boto3_client, \
             patch('src.ingestion.eirgrid_ingestion.datetime') as mock_datetime, \
             patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:

            # Setup datetime mock correctly
            mock_utcnow = Mock()
            mock_utcnow.return_value = datetime(2023, 1, 1)
            mock_datetime.utcnow = mock_utcnow
            mock_datetime.timedelta = timedelta

            # Setup EventBridge mock
            mock_eventbridge = Mock()
            mock_boto3_client.return_value = mock_eventbridge

            # Mock the ingest_date_range method by patching the client's method
            with patch('src.ingestion.eirgrid_ingestion.EirGridIngestionClient.ingest_date_range', return_value={'total_records': 100, 'successful': 100}):

                # Call the lambda handler directly
                event = {'date': '2023-01-01'}
                context = Mock()

                result = eirgrid_lambda_handler(event, context)

                # Verify event was published
                mock_eventbridge.put_events.assert_called_once()
                call_args = mock_eventbridge.put_events.call_args

                # Verify the event structure
                entries = call_args[1]['Entries']
                assert len(entries) == 1
                entry = entries[0]
                assert entry['Source'] == 'irish-energy.ingestion'
                assert entry['DetailType'] == 'EirGrid Ingestion Complete'
                detail = json.loads(entry['Detail'])
                assert detail['data_type'] == 'eirgrid'
                assert detail['date_range'] == '2023-01-01 to 2023-01-01'
                assert detail['stats']['total_records'] == 100
                assert detail['stats']['successful'] == 100

                # Verify success response
                assert result['statusCode'] == 200

    def test_failed_ingestion_emits_failure_event(self):
        """Test that failed ingestion emits failure event"""
        with patch('src.ingestion.eirgrid_ingestion.boto3.client') as mock_boto3_client, \
             patch('src.ingestion.eirgrid_ingestion.datetime') as mock_datetime, \
             patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:

            # Setup datetime mock correctly
            mock_utcnow = Mock()
            mock_utcnow.return_value = datetime(2023, 1, 1)
            mock_datetime.utcnow = mock_utcnow
            mock_datetime.timedelta = timedelta

            # Setup EventBridge mock
            mock_eventbridge = Mock()
            mock_boto3_client.return_value = mock_eventbridge

            # Mock the ingest_date_range method to raise an exception
            with patch('src.ingestion.eirgrid_ingestion.EirGridIngestionClient.ingest_date_range', side_effect=Exception("Network error")):

                # Call the lambda handler directly
                event = {'date': '2023-01-01'}
                context = Mock()

                result = eirgrid_lambda_handler(event, context)

                # Verify failure event was published
                mock_eventbridge.put_events.assert_called_once()
                call_args = mock_eventbridge.put_events.call_args

                # Verify the event structure
                entries = call_args[1]['Entries']
                assert len(entries) == 1
                entry = entries[0]
                assert entry['Source'] == 'irish-energy.ingestion'
                assert entry['DetailType'] == 'EirGrid Ingestion Failed'
                detail = json.loads(entry['Detail'])
                assert detail['data_type'] == 'eirgrid'
                assert detail['date_range'] == '2023-01-01 to 2023-01-01'
                assert 'error' in detail

                # Verify error response
                assert result['statusCode'] == 500


class TestEventPublishingOpenMeteo:
    """Test EventBridge event publishing for Open-Meteo ingestion"""

    def test_successful_ingestion_emits_completion_event(self):
        """Test that successful ingestion emits completion event"""
        with patch('src.ingestion.openmeteo_ingestion.boto3.client') as mock_boto3_client, \
             patch('src.ingestion.openmeteo_ingestion.datetime') as mock_datetime, \
             patch('src.ingestion.openmeteo_ingestion.logger') as mock_logger:

            # Setup datetime mock correctly
            mock_utcnow = Mock()
            mock_utcnow.return_value = datetime(2023, 1, 1)
            mock_datetime.utcnow = mock_utcnow
            mock_datetime.timedelta = timedelta

            # Setup EventBridge mock
            mock_eventbridge = Mock()
            mock_boto3_client.return_value = mock_eventbridge

            # Mock the ingest_date_range method by patching the client's method
            with patch('src.ingestion.openmeteo_ingestion.OpenMeteoIngestionClient.ingest_date_range', return_value={'successful_days': 50, 'failed_days': 0, 'total_days': 50}):

                # Call the lambda handler directly
                event = {'location': 'dublin', 'date': '2023-01-01'}
                context = Mock()

                result = openmeteo_lambda_handler(event, context)

                # Verify event was published
                mock_eventbridge.put_events.assert_called_once()
                call_args = mock_eventbridge.put_events.call_args

                # Verify the event structure
                entries = call_args[1]['Entries']
                assert len(entries) == 1
                entry = entries[0]
                assert entry['Source'] == 'irish-energy.ingestion'
                assert entry['DetailType'] == 'OpenMeteo Ingestion Complete'
                detail = json.loads(entry['Detail'])
                assert detail['data_type'] == 'openmeteo'
                assert detail['location'] == 'dublin'
                assert detail['date_range'] == '2023-01-01 to 2023-01-01'
                assert detail['stats']['successful_days'] == 50
                assert detail['stats']['failed_days'] == 0
                assert detail['stats']['total_days'] == 50

                # Verify success response
                assert result['statusCode'] == 200

    def test_successful_ingestion_emits_completion_event_with_zero_success(self):
        """Test that ingestion with zero successful days emits failure event"""
        with patch('src.ingestion.openmeteo_ingestion.boto3.client') as mock_boto3_client, \
             patch('src.ingestion.openmeteo_ingestion.datetime') as mock_datetime, \
             patch('src.ingestion.openmeteo_ingestion.logger') as mock_logger:

            # Setup datetime mock correctly
            mock_utcnow = Mock()
            mock_utcnow.return_value = datetime(2023, 1, 1)
            mock_datetime.utcnow = mock_utcnow
            mock_datetime.timedelta = timedelta

            # Setup EventBridge mock
            mock_eventbridge = Mock()
            mock_boto3_client.return_value = mock_eventbridge

            # Mock the ingest_date_range method to return stats with zero successful days
            with patch('src.ingestion.openmeteo_ingestion.OpenMeteoIngestionClient.ingest_date_range', return_value={'successful_days': 0, 'failed_days': 10, 'total_days': 10}):

                # Call the lambda handler directly
                event = {'location': 'dublin', 'date': '2023-01-01'}
                context = Mock()

                result = openmeteo_lambda_handler(event, context)

                # Verify failure event was published (since successful_days = 0)
                mock_eventbridge.put_events.assert_called_once()
                call_args = mock_eventbridge.put_events.call_args

                # Verify the event structure - should be failure event
                entries = call_args[1]['Entries']
                assert len(entries) == 1
                entry = entries[0]
                assert entry['Source'] == 'irish-energy.ingestion'
                assert entry['DetailType'] == 'OpenMeteo Ingestion Failed'
                detail = json.loads(entry['Detail'])
                assert detail['data_type'] == 'openmeteo'
                assert detail['location'] == 'dublin'
                assert detail['date_range'] == '2023-01-01 to 2023-01-01'
                assert 'error' in detail

                # Verify error response
                assert result['statusCode'] == 500

    def test_failed_ingestion_emits_failure_event(self):
        """Test that failed ingestion emits failure event"""
        with patch('src.ingestion.openmeteo_ingestion.boto3.client') as mock_boto3_client, \
             patch('src.ingestion.openmeteo_ingestion.datetime') as mock_datetime, \
             patch('src.ingestion.openmeteo_ingestion.logger') as mock_logger:

            # Setup datetime mock correctly
            mock_utcnow = Mock()
            mock_utcnow.return_value = datetime(2023, 1, 1)
            mock_datetime.utcnow = mock_utcnow
            mock_datetime.timedelta = timedelta

            # Setup EventBridge mock
            mock_eventbridge = Mock()
            mock_boto3_client.return_value = mock_eventbridge

            # Mock the ingest_date_range method to raise an exception
            with patch('src.ingestion.openmeteo_ingestion.OpenMeteoIngestionClient.ingest_date_range', side_effect=Exception("Network error")):

                # Call the lambda handler directly
                event = {'location': 'dublin', 'date': '2023-01-01'}
                context = Mock()

                result = openmeteo_lambda_handler(event, context)

                # Verify failure event was published
                mock_eventbridge.put_events.assert_called_once()
                call_args = mock_eventbridge.put_events.call_args

                # Verify the event structure
                entries = call_args[1]['Entries']
                assert len(entries) == 1
                entry = entries[0]
                assert entry['Source'] == 'irish-energy.ingestion'
                assert entry['DetailType'] == 'OpenMeteo Ingestion Failed'
                detail = json.loads(entry['Detail'])
                assert detail['data_type'] == 'openmeteo'
                assert detail['location'] == 'dublin'
                assert detail['date_range'] == '2023-01-01 to 2023-01-01'
                assert 'error' in detail

                # Verify error response
                assert result['statusCode'] == 500