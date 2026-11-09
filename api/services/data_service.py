"""S3 Gold layer data access for the analytics API."""

import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional

import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError
from loguru import logger

from src.common.config import Config


class GoldDataError(Exception):
    """Base error for Gold data retrieval."""


class GoldDataNotFoundError(GoldDataError):
    """Raised when a required Gold dataset has no objects."""


class GoldDataAccessError(GoldDataError):
    """Raised when S3 cannot be accessed."""


class GoldDataParseError(GoldDataError):
    """Raised when a Gold Parquet object cannot be parsed."""


class GoldDataValidationError(GoldDataError):
    """Raised when request parameters are invalid."""


class S3GoldDataRetriever:
    # Updated schemas to match actual Gold data structure
    DATASET_COLUMNS = {
        "demand": [
            "date",
            "total_demand",
            "avg_demand",
            "min_demand",
            "max_demand",
        ],
        "weather": [
            "date",
            "avg_temperature",
            "min_temperature",
            "max_temperature",
            "avg_humidity",
        ],
        "generation": ["date", "total_generation", "avg_generation"],
    }
    OPTIONAL_COLUMNS = {"generation": ["fuel_type"]}
    DATASET_NAMES = ("demand", "weather", "generation")

    def __init__(self, s3_client=None, bucket_name: Optional[str] = None):
        self.s3_client = s3_client or boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION", "eu-west-1"),
        )
        self.bucket_name = bucket_name or os.getenv(
            "S3_BUCKET_NAME", Config.GOLD_BUCKET
        )

    def _list_gold_keys(self, data_type: str) -> List[str]:
        prefix = f"{data_type}/gold/"
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            keys = []
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.lower().endswith(".parquet"):
                        keys.append(key)
            return sorted(keys)
        except (ClientError, BotoCoreError) as exc:
            logger.error(f"Error listing s3://{self.bucket_name}/{prefix}: {exc}")
            raise GoldDataAccessError(
                f"Unable to list Gold data for {data_type}: {exc}"
            ) from exc

    def _read_parquet_from_s3(self, key: str) -> pd.DataFrame:
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=key
            )
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404", "NotFound"):
                raise GoldDataNotFoundError(
                    f"Gold object not found: s3://{self.bucket_name}/{key}"
                ) from exc
            logger.error(f"Error reading {key} from S3: {exc}")
            raise GoldDataAccessError(
                f"Unable to read Gold object {key}: {exc}"
            ) from exc
        except BotoCoreError as exc:
            logger.error(f"Error reading {key} from S3: {exc}")
            raise GoldDataAccessError(
                f"Unable to read Gold object {key}: {exc}"
            ) from exc

        try:
            return pd.read_parquet(BytesIO(response["Body"].read()))
        except Exception as exc:
            logger.error(f"Error parsing Parquet object {key}: {exc}")
            raise GoldDataParseError(
                f"Unable to parse Gold Parquet object {key}: {exc}"
            ) from exc

    def _parse_request_date(self, value: Optional[str], name: str) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise GoldDataValidationError(
                f"Invalid {name} '{value}'. Expected YYYY-MM-DD."
            ) from exc

    def _load_dataset(
        self,
        data_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        required: bool = True,
    ) -> Optional[pd.DataFrame]:
        start = self._parse_request_date(start_date, "start_date")
        end = self._parse_request_date(end_date, "end_date")

        keys = self._list_gold_keys(data_type)
        if not keys:
            if required:
                raise GoldDataNotFoundError(
                    f"No Gold parquet objects found for {data_type}"
                )
            return None

        expected_columns = self.DATASET_COLUMNS[data_type]
        optional_columns = self.OPTIONAL_COLUMNS.get(data_type, [])

        frames = []
        for key in keys:
            df = self._read_parquet_from_s3(key)
            missing = [col for col in expected_columns if col not in df.columns]
            if missing:
                raise GoldDataParseError(
                    f"{key} is missing required columns: {', '.join(missing)}"
                )
            columns = expected_columns + [
                col for col in optional_columns if col in df.columns
            ]
            frames.append(df[columns])

        combined = pd.concat(frames, ignore_index=True)
        if combined.empty:
            combined = combined.reindex(
                columns=expected_columns + optional_columns
            )

        combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
        if combined["date"].notna().any() and combined["date"].isna().any():
            raise GoldDataParseError(
                f"{data_type} data contains invalid date values"
            )
        if combined["date"].isna().all() and not combined.empty:
            raise GoldDataParseError(
                f"{data_type} data contains no valid date values"
            )

        if start is not None:
            combined = combined[combined["date"] >= start]
        if end is not None:
            combined = combined[combined["date"] <= end]

        dedupe_columns = ["date"]
        if "fuel_type" in combined.columns:
            combined["fuel_type"] = combined["fuel_type"].fillna("total")
            dedupe_columns.append("fuel_type")

        if not combined.empty:
            # Remove duplicates and sort by date first, then fuel_type if present
            combined = (
                combined.drop_duplicates(subset=dedupe_columns, keep="last")
                .sort_values(by=dedupe_columns)
                .reset_index(drop=True)
            )
        return combined

    @staticmethod
    def _records(df: pd.DataFrame, data_type: str) -> List[Dict[str, Any]]:
        if df.empty:
            return []
        records_df = df.copy()
        records_df["date"] = records_df["date"].dt.strftime("%Y-%m-%d")
        if data_type == "generation":
            if "fuel_type" not in records_df.columns:
                records_df["fuel_type"] = "total"
            records_df["fuel_type"] = records_df["fuel_type"].fillna("total")
        return records_df.to_dict("records")

    def _load_available_datasets(self) -> Dict[str, pd.DataFrame]:
        datasets = {}
        for data_type in self.DATASET_NAMES:
            df = self._load_dataset(data_type, required=False)
            if df is not None:
                datasets[data_type] = df
        return datasets

    @staticmethod
    def _metrics(data_type: str, df: pd.DataFrame) -> Dict[str, Any]:
        total_records = int(len(df))
        total_cells = int(df.shape[0] * df.shape[1])
        if total_records:
            missing_values = int(df.isna().sum().sum())
            score = round(100 * (1 - (missing_values / total_cells)), 2)
            last_updated = df["date"].max().to_pydatetime()
        else:
            missing_values = 0
            score = 0.0
            last_updated = datetime.now(timezone.utc)

        return {
            "dataset_name": data_type,
            "total_records": total_records,
            "missing_values": missing_values,
            "data_quality_score": score,
            "last_updated": last_updated,
            "_total_cells": total_cells,
        }

    def get_demand_data(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self._load_dataset("demand", start_date, end_date)
        return self._records(df, "demand")

    def get_weather_data(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self._load_dataset("weather", start_date, end_date)
        return self._records(df, "weather")

    def get_generation_data(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self._load_dataset("generation", start_date, end_date)
        return self._records(df, "generation")

    def get_quality_metrics(self) -> List[Dict[str, Any]]:
        datasets = self._load_available_datasets()
        return [
            {
                key: value
                for key, value in self._metrics(
                    data_type, datasets[data_type]
                ).items()
                if not key.startswith("_")
            }
            for data_type in self.DATASET_NAMES
            if data_type in datasets
        ]

    def get_summary_data(self) -> Dict[str, Any]:
        datasets = self._load_available_datasets()
        metrics = {
            data_type: self._metrics(data_type, datasets[data_type])
            for data_type in self.DATASET_NAMES
            if data_type in datasets
        }

        total_records = sum(item["total_records"] for item in metrics.values())
        total_missing = sum(item["missing_values"] for item in metrics.values())
        total_cells = sum(item["_total_cells"] for item in metrics.values())
        overall_score = (
            round(100 * (1 - (total_missing / total_cells)), 2)
            if total_cells
            else 0.0
        )

        if metrics:
            last_updated = max(
                item["last_updated"] for item in metrics.values()
            )
        else:
            last_updated = datetime.now(timezone.utc)

        return {
            "total_datasets": len(metrics),
            "total_records": int(total_records),
            "last_updated": last_updated,
            "data_quality_summary": {
                "overall_quality_score": overall_score,
                "total_missing_values": int(total_missing),
                "datasets": {
                    data_type: {
                        "total_records": item["total_records"],
                        "missing_values": item["missing_values"],
                        "data_quality_score": item["data_quality_score"],
                        "last_updated": item["last_updated"].isoformat(),
                    }
                    for data_type, item in metrics.items()
                },
                "missing_datasets": [
                    data_type
                    for data_type in self.DATASET_NAMES
                    if data_type not in metrics
                ],
            },
        }
