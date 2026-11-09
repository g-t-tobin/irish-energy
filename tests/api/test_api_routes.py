import asyncio
import sys
from pathlib import Path

import httpx
import pandas as pd
import pytest

API_DIR = Path(__file__).resolve().parents[2] / "api"
sys.path.insert(0, str(API_DIR))

import main as api_main  # noqa: E402
from services.data_service import S3GoldDataRetriever  # noqa: E402
from tests.api.helpers import (  # noqa: E402
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


class ASGIClient:
    def get(self, url):
        async def request():
            transport = httpx.ASGITransport(app=api_main.app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                return await client.get(url)

        return asyncio.run(request())


@pytest.fixture
def client():
    return ASGIClient()


def use_objects(objects, **kwargs):
    api_main.data_retriever = S3GoldDataRetriever(
        s3_client=FakeS3Client(objects, **kwargs),
        bucket_name="test-gold",
    )


def test_demand_route_returns_frontend_contract(client):
    use_objects(
        {
            "demand/gold/2026-11-06.parquet": parquet_bytes(
                demand_df([["2026-11-06", 451544, 4655.09, 3736, 5463]])
            )
        }
    )

    response = client.get("/demand")

    assert response.status_code == 200
    assert response.json() == [
        {
            "date": "2026-11-06",
            "total_demand": 451544,
            "avg_demand": 4655.09,
            "min_demand": 3736,
            "max_demand": 5463,
        }
    ]


def test_quality_route_returns_derived_metrics(client):
    use_objects(
        {
            "demand/gold/2026-11-06.parquet": parquet_bytes(
                demand_df([["2026-11-06", 100, 10, 5, 20]])
            )
        }
    )

    response = client.get("/quality")

    assert response.status_code == 200
    assert response.json() == [
        {
            "data_type": "demand",
            "date": "2026-11-06",
            "bronze_processed": True,
            "silver_processed": True,
            "gold_processed": True,
            "processing_timestamp": "2026-11-06T00:00:00",
        }
    ]


def test_summary_route_returns_valid_response_without_summary_objects(client):
    use_objects(
        {
            "demand/gold/2026-11-06.parquet": parquet_bytes(
                demand_df([["2026-11-06", 100, 10, 5, 20]])
            )
        }
    )

    response = client.get("/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_datasets"] == 1
    assert body["total_records"] == 1
    assert body["last_updated"] == "2026-11-06"
    assert body["data_quality_summary"]["missing_datasets"] == [
        "weather",
        "generation",
    ]


def test_summary_route_with_no_data_returns_zero_summary(client):
    use_objects({})

    response = client.get("/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_datasets"] == 0
    assert body["total_records"] == 0


def test_missing_required_dataset_returns_404(client):
    use_objects({})

    response = client.get("/demand")

    assert response.status_code == 404
    assert "No Gold parquet objects found for demand" in response.json()["detail"]


def test_s3_access_error_returns_503(client):
    use_objects({}, list_error=access_denied_error())

    response = client.get("/demand")

    assert response.status_code == 503


def test_malformed_parquet_returns_500(client):
    use_objects({"demand/gold/2026-11-06.parquet": b"bad parquet"})

    response = client.get("/demand")

    assert response.status_code == 500


def test_invalid_date_returns_400(client):
    use_objects(
        {
            "demand/gold/2026-11-06.parquet": parquet_bytes(
                demand_df([["2026-11-06", 100, 10, 5, 20]])
            )
        }
    )

    response = client.get("/demand?start_date=06-11-2026")

    assert response.status_code == 400
