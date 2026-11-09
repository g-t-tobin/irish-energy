from datetime import datetime

import pandas as pd
import pytest
from botocore.exceptions import ClientError

from api.services.data_service import (
    GoldDataAccessError,
    GoldDataNotFoundError,
    GoldDataParseError,
    GoldDataValidationError,
    S3GoldDataRetriever,
)
from tests.api.helpers import (
    FakeS3Client,
    access_denied_error,
    parquet_bytes,
)


def demand_df(rows):
    return pd.DataFrame(
        rows,
        columns=[
            "date",
            "total_demand",
            "avg_demand",
            "min_demand",
            "max_demand",
        ],
    )


def weather_df(rows):
    return pd.DataFrame(
        rows,
        columns=[
            "date",
            "avg_temperature",
            "min_temperature",
            "max_temperature",
            "avg_humidity",
        ],
    )


def generation_df(rows):
    return pd.DataFrame(
        rows,
        columns=["date", "total_generation", "avg_generation"],
    )


def retriever_for(objects, **kwargs):
    return S3GoldDataRetriever(
        s3_client=FakeS3Client(objects, **kwargs),
        bucket_name="test-gold",
    )


def test_demand_multiple_partitions_are_combined_and_deduplicated():
    objects = {
        "demand/gold/2026-11-05.parquet": parquet_bytes(
            demand_df(
                [
                    ["2026-11-05", 100, 10, 5, 20],
                    ["2026-11-06", 200, 20, 10, 30],
                ]
            )
        ),
        "demand/gold/2026-11-06.parquet": parquet_bytes(
            demand_df([["2026-11-06", 300, 30, 15, 45]])
        ),
    }

    records = retriever_for(objects).get_demand_data()

    assert [row["date"] for row in records] == ["2026-11-05", "2026-11-06"]
    assert records[1]["total_demand"] == 300


def test_weather_multiple_partitions_preserve_dates():
    objects = {
        "weather/gold/2026-11-04.parquet": parquet_bytes(
            weather_df([["2026-11-04", 11.0, 10.0, 12.0, 80.0]])
        ),
        "weather/gold/2026-11-06.parquet": parquet_bytes(
            weather_df([["2026-11-06", 9.0, 8.0, 10.0, 70.0]])
        ),
    }

    records = retriever_for(objects).get_weather_data()

    assert records == [
        {
            "date": "2026-11-04",
            "avg_temperature": 11.0,
            "min_temperature": 10.0,
            "max_temperature": 12.0,
            "avg_humidity": 80.0,
        },
        {
            "date": "2026-11-06",
            "avg_temperature": 9.0,
            "min_temperature": 8.0,
            "max_temperature": 10.0,
            "avg_humidity": 70.0,
        },
    ]


def test_generation_without_fuel_type_uses_total_label():
    objects = {
        "generation/gold/2026-11-06.parquet": parquet_bytes(
            generation_df([["2026-11-06", 355691, 3666.9]])
        )
    }

    records = retriever_for(objects).get_generation_data()

    assert records == [
        {
            "date": "2026-11-06",
            "total_generation": 355691,
            "avg_generation": 3666.9,
            "fuel_type": "total",
        }
    ]


def test_generation_with_fuel_type_is_preserved():
    df = generation_df([["2026-11-06", 100, 50]]).assign(fuel_type="wind")
    objects = {"generation/gold/2026-11-06.parquet": parquet_bytes(df)}

    records = retriever_for(objects).get_generation_data()

    assert records[0]["fuel_type"] == "wind"


def test_empty_dataset_returns_empty_list():
    objects = {
        "demand/gold/2026-11-06.parquet": parquet_bytes(
            demand_df([])
        )
    }

    assert retriever_for(objects).get_demand_data() == []


def test_missing_required_dataset_raises_not_found():
    retriever = retriever_for({})

    with pytest.raises(GoldDataNotFoundError):
        retriever.get_demand_data()


def test_missing_optional_datasets_are_reported_without_error():
    objects = {
        "demand/gold/2026-11-06.parquet": parquet_bytes(
            demand_df([["2026-11-06", 100, 10, 5, 20]])
        )
    }
    retriever = retriever_for(objects)

    quality = retriever.get_quality_metrics()
    summary = retriever.get_summary_data()

    assert [item["dataset_name"] for item in quality] == ["demand"]
    assert summary["total_datasets"] == 1
    assert summary["total_records"] == 1
    assert summary["data_quality_summary"]["missing_datasets"] == [
        "weather",
        "generation",
    ]


def test_malformed_parquet_raises_parse_error():
    objects = {"demand/gold/2026-11-06.parquet": b"not a parquet file"}

    with pytest.raises(GoldDataParseError):
        retriever_for(objects).get_demand_data()


def test_missing_required_columns_raise_parse_error():
    df = pd.DataFrame(
        [["2026-11-06", 100]],
        columns=["date", "total_demand"],
    )
    objects = {"demand/gold/2026-11-06.parquet": parquet_bytes(df)}

    with pytest.raises(GoldDataParseError):
        retriever_for(objects).get_demand_data()


def test_listing_access_error_raises_access_error():
    retriever = retriever_for({}, list_error=access_denied_error())

    with pytest.raises(GoldDataAccessError):
        retriever.get_demand_data()


def test_get_object_access_error_raises_access_error():
    key = "demand/gold/2026-11-06.parquet"
    retriever = retriever_for(
        {key: b"unused"},
        get_errors={key: access_denied_error("GetObject")},
    )

    with pytest.raises(GoldDataAccessError):
        retriever.get_demand_data()


def test_get_object_no_such_key_raises_not_found():
    key = "demand/gold/2026-11-06.parquet"
    error = ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
    retriever = retriever_for({key: b"unused"}, get_errors={key: error})

    with pytest.raises(GoldDataNotFoundError):
        retriever.get_demand_data()


def test_date_range_filters_records_inclusively():
    objects = {
        "demand/gold/2026-11-05.parquet": parquet_bytes(
            demand_df([["2026-11-05", 100, 10, 5, 20]])
        ),
        "demand/gold/2026-11-06.parquet": parquet_bytes(
            demand_df([["2026-11-06", 200, 20, 10, 30]])
        ),
        "demand/gold/2026-11-07.parquet": parquet_bytes(
            demand_df([["2026-11-07", 300, 30, 15, 45]])
        ),
    }
    retriever = retriever_for(objects)

    records = retriever.get_demand_data("2026-11-06", "2026-11-07")

    assert [row["date"] for row in records] == ["2026-11-06", "2026-11-07"]


def test_invalid_date_range_raises_validation_error():
    objects = {
        "demand/gold/2026-11-06.parquet": parquet_bytes(
            demand_df([["2026-11-06", 100, 10, 5, 20]])
        )
    }

    with pytest.raises(GoldDataValidationError):
        retriever_for(objects).get_demand_data("06-11-2026", None)


def test_quality_metrics_calculate_missing_values_and_scores():
    objects = {
        "demand/gold/2026-11-06.parquet": parquet_bytes(
            demand_df(
                [
                    ["2026-11-06", 100, 10, 5, 20],
                    ["2026-11-07", 200, 20, 10, 30],
                ]
            )
        ),
        "weather/gold/2026-11-06.parquet": parquet_bytes(
            weather_df(
                [
                    ["2026-11-06", 10.0, 9.0, 11.0, None],
                    ["2026-11-07", 12.0, 11.0, 13.0, 80.0],
                ]
            )
        ),
    }

    metrics = retriever_for(objects).get_quality_metrics()

    assert [item["dataset_name"] for item in metrics] == ["demand", "weather"]
    assert metrics[0]["total_records"] == 2
    assert metrics[0]["missing_values"] == 0
    assert metrics[0]["data_quality_score"] == 100.0
    assert metrics[1]["missing_values"] == 1
    assert metrics[1]["data_quality_score"] == 90.0
    assert metrics[1]["last_updated"] == datetime(2026, 11, 7)


def test_summary_calculates_totals_quality_and_last_updated():
    objects = {
        "demand/gold/2026-11-06.parquet": parquet_bytes(
            demand_df(
                [
                    ["2026-11-06", 100, 10, 5, 20],
                    ["2026-11-07", 200, 20, 10, 30],
                ]
            )
        ),
        "weather/gold/2026-11-06.parquet": parquet_bytes(
            weather_df(
                [
                    ["2026-11-06", 10.0, 9.0, 11.0, None],
                    ["2026-11-07", 12.0, 11.0, 13.0, 80.0],
                ]
            )
        ),
        "generation/gold/2026-11-06.parquet": parquet_bytes(
            generation_df([["2026-11-06", 1000, 500]])
        ),
    }

    summary = retriever_for(objects).get_summary_data()

    assert summary["total_datasets"] == 3
    assert summary["total_records"] == 5
    assert summary["last_updated"] == datetime(2026, 11, 7)
    quality = summary["data_quality_summary"]
    assert quality["total_missing_values"] == 1
    assert quality["overall_quality_score"] == 95.65
    assert quality["missing_datasets"] == []
    assert quality["datasets"]["generation"]["total_records"] == 1


def test_summary_with_no_datasets_returns_valid_zero_summary():
    summary = retriever_for({}).get_summary_data()

    assert summary["total_datasets"] == 0
    assert summary["total_records"] == 0
    assert summary["data_quality_summary"]["missing_datasets"] == [
        "demand",
        "weather",
        "generation",
    ]
