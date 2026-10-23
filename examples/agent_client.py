"""After human issuance, set AGENTVISA_AGENT_TOKEN and AGENTVISA_VISA_ID."""
import json
import os
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    payload = {"request_id": uuid4().hex, "visa_id": os.environ["AGENTVISA_VISA_ID"],
               "tool": "search_products", "resource": "catalog:monitors", "arguments": {"query": "monitor"}}
    request = Request("http://127.0.0.1:8000/execute", data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["AGENTVISA_AGENT_TOKEN"]}, method="POST")
    with urlopen(request, timeout=10) as response:
        print(json.dumps(json.load(response), indent=2))


if __name__ == "__main__":
    main()
