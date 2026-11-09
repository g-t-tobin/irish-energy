from io import BytesIO

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from botocore.exceptions import ClientError


def parquet_bytes(df: pd.DataFrame) -> bytes:
    table = pa.Table.from_pandas(df, preserve_index=False)
    buffer = BytesIO()
    pq.write_table(table, buffer)
    return buffer.getvalue()


class FakePaginator:
    def __init__(self, client):
        self.client = client

    def paginate(self, Bucket, Prefix):
        if self.client.list_error is not None:
            raise self.client.list_error
        keys = sorted(
            key for key in self.client.objects if key.startswith(Prefix)
        )
        yield {"Contents": [{"Key": key} for key in keys]} if keys else {}


class FakeS3Client:
    def __init__(self, objects=None, list_error=None, get_errors=None):
        self.objects = objects or {}
        self.list_error = list_error
        self.get_errors = get_errors or {}

    def get_paginator(self, name):
        return FakePaginator(self)

    def get_object(self, Bucket, Key):
        if Key in self.get_errors:
            raise self.get_errors[Key]
        if Key not in self.objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey"}},
                "GetObject",
            )
        return {"Body": BytesIO(self.objects[Key])}


def access_denied_error(operation="ListObjectsV2"):
    return ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "denied"}},
        operation,
    )
