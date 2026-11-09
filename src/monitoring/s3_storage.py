"""
S3-based monitoring storage adapter for Irish Energy Analytics Platform
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from src.monitoring.storage_interface import MonitoringStorageInterface
from src.common.config import Config

class S3MonitoringStorage(MonitoringStorageInterface):
    """
    S3-based storage adapter for monitoring data
    Implements the MonitoringStorageInterface for production deployments
    """

    def __init__(self, bucket_name: str = None, prefix: str = "monitoring/", region: str = None):
        self.config = Config()
        # Use BRONZE_BUCKET as the authoritative bucket for monitoring data
        # This ensures consistency with the deployment architecture
        self.bucket_name = bucket_name or self.config.BRONZE_BUCKET
        self.prefix = prefix or self.config.S3_MONITORING_PREFIX or "monitoring/"
        self.region = region or self.config.AWS_REGION

        # Validate that we have the required configuration for S3
        if not self.bucket_name:
            raise ValueError("S3 bucket name is required for S3 monitoring storage")

        # Initialize S3 client
        try:
            if self.region:
                self.s3_client = boto3.client('s3', region_name=self.region)
            else:
                self.s3_client = boto3.client('s3')
        except NoCredentialsError:
            logger.error("AWS credentials not found. S3 storage will not work.")
            raise
        except Exception as e:
            logger.error(f"Error initializing S3 client: {str(e)}")
            raise

    def _build_key(self, prefix: str, item_id: str) -> str:
        """Build S3 object key with proper prefixing"""
        return f"{self.prefix}{prefix}{item_id}.json"

    def save_execution_summary(self, execution_id: str, summary: Dict[str, Any]) -> bool:
        """
        Save execution summary to S3 storage

        Args:
            execution_id: Unique identifier for the execution
            summary: Execution summary data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp to summary
            summary_with_timestamp = {
                **summary,
                'timestamp': datetime.now().isoformat()
            }

            # Build S3 key
            key = self._build_key("execution_", execution_id)

            # Convert to JSON and upload to S3
            json_data = json.dumps(summary_with_timestamp, indent=2)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_data,
                ContentType='application/json'
            )

            logger.info(f"Saved execution summary for {execution_id} to S3")
            return True

        except ClientError as e:
            logger.error(f"AWS Client error saving execution summary for {execution_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error saving execution summary for {execution_id}: {str(e)}")
            return False

    def save_quality_report(self, report_id: str, report: Dict[str, Any]) -> bool:
        """
        Save quality report to S3 storage

        Args:
            report_id: Unique identifier for the report
            report: Quality report data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp to report
            report_with_timestamp = {
                **report,
                'timestamp': datetime.now().isoformat()
            }

            # Build S3 key
            key = self._build_key("quality_", report_id)

            # Convert to JSON and upload to S3
            json_data = json.dumps(report_with_timestamp, indent=2)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_data,
                ContentType='application/json'
            )

            logger.info(f"Saved quality report for {report_id} to S3")
            return True

        except ClientError as e:
            logger.error(f"AWS Client error saving quality report for {report_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error saving quality report for {report_id}: {str(e)}")
            return False

    def get_execution_summary(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve execution summary from S3 storage

        Args:
            execution_id: Unique identifier for the execution

        Returns:
            Execution summary data or None if not found
        """
        try:
            # Build S3 key
            key = self._build_key("execution_", execution_id)

            # Get object from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )

            # Parse JSON content
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            logger.error(f"AWS Client error retrieving execution summary for {execution_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving execution summary for {execution_id}: {str(e)}")
            return None

    def get_quality_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve quality report from S3 storage

        Args:
            report_id: Unique identifier for the report

        Returns:
            Quality report data or None if not found
        """
        try:
            # Build S3 key
            key = self._build_key("quality_", report_id)

            # Get object from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )

            # Parse JSON content
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            logger.error(f"AWS Client error retrieving quality report for {report_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving quality report for {report_id}: {str(e)}")
            return None

    def list_execution_summaries(
        self,
        limit: int = 100,
        source_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        List execution summaries with optional filtering from S3 storage

        Args:
            limit: Maximum number of summaries to return
            source_filter: Filter by source (pipeline, manual, etc.)
            status_filter: Filter by status (started, completed, failed)
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of execution summaries
        """
        try:
            # List objects with prefix
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix + "execution_")

            summaries = []
            for page in pages:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    # Skip if not a JSON file
                    if not obj['Key'].endswith('.json'):
                        continue

                    # Get object content
                    response = self.s3_client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
                    content = response['Body'].read().decode('utf-8')
                    summary = json.loads(content)

                    # Apply filters
                    if source_filter and summary.get('source') != source_filter:
                        continue
                    if status_filter and summary.get('status') != status_filter:
                        continue

                    # Apply date filters
                    timestamp = summary.get('timestamp')
                    if timestamp:
                        summary_dt = datetime.fromisoformat(timestamp)
                        if start_date and summary_dt < start_date:
                            continue
                        if end_date and summary_dt > end_date:
                            continue

                    summaries.append(summary)

            # Sort by timestamp descending (most recent first)
            summaries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            return summaries[:limit]

        except ClientError as e:
            logger.error(f"AWS Client error listing execution summaries: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error listing execution summaries: {str(e)}")
            return []

    def list_quality_reports(
        self,
        limit: int = 100,
        source_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        List quality reports with optional filtering from S3 storage

        Args:
            limit: Maximum number of reports to return
            source_filter: Filter by source
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of quality reports
        """
        try:
            # List objects with prefix
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix + "quality_")

            reports = []
            for page in pages:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    # Skip if not a JSON file
                    if not obj['Key'].endswith('.json'):
                        continue

                    # Get object content
                    response = self.s3_client.get_object(Bucket=self.bucket_name, Key=obj['Key'])
                    content = response['Body'].read().decode('utf-8')
                    report = json.loads(content)

                    # Apply filters
                    if source_filter and report.get('source') != source_filter:
                        continue

                    # Apply date filters
                    timestamp = report.get('timestamp')
                    if timestamp:
                        report_dt = datetime.fromisoformat(timestamp)
                        if start_date and report_dt < start_date:
                            continue
                        if end_date and report_dt > end_date:
                            continue

                    reports.append(report)

            # Sort by timestamp descending (most recent first)
            reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            return reports[:limit]

        except ClientError as e:
            logger.error(f"AWS Client error listing quality reports: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error listing quality reports: {str(e)}")
            return []