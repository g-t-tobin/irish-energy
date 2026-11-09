"""Resolve writable runtime directories for local and AWS Lambda execution."""

import os
from pathlib import Path


def writable_runtime_dir(local_default: str) -> str:
    """Use /tmp in Lambda; preserve the configured local path elsewhere.

    Lambda deployment code is mounted read-only. /tmp is the supported writable
    filesystem and is intentionally ephemeral between execution environments.
    """
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return str(Path("/tmp") / Path(local_default).name)
    return local_default
