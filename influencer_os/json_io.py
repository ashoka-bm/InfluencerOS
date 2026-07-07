"""JSON file writing helpers for the file-first store."""

import json
import os
import tempfile
from pathlib import Path


def write_json_atomic(path, data, *, indent=2, replace=os.replace):
    """Write JSON by replacing a same-directory temp file.

    The existing destination remains intact if serialization, flushing, or the
    final replace fails. ``allow_nan=False`` keeps persisted files valid JSON.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=indent, allow_nan=False) + "\n"
    descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
