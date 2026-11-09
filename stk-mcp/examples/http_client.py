"""Call the REST kernel with the standard library only.

Start the kernel first:

    python -m spaceone_stk_mcp.cli serve-http --port 8080
"""

from __future__ import annotations

import json
import urllib.request

BASE = "http://127.0.0.1:8080"


def call(operation: str, arguments: dict | None = None) -> dict:
    body = json.dumps({"arguments": arguments or {}}).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE}/api/v1/tools/{operation}",
        data=body,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    print(json.dumps(call("stk_status"), indent=2, ensure_ascii=False))
    print(json.dumps(call("scenario_info"), indent=2, ensure_ascii=False))
