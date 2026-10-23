"""Human operator CLI. Calls only authenticated control APIs; never executes tools."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .models import Contract
from .transport import gateway_origin


class OperatorError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ControlClient:
    def __init__(self, origin: str, token: str):
        self.origin = gateway_origin(origin)
        if len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
            raise ValueError("invalid administrator credential")
        self._token = token
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(self, method: str, path: str, body=None):
        payload = None if body is None else json.dumps(body, allow_nan=False).encode()
        if payload is not None and len(payload) > 65536:
            raise OperatorError("Request too large; nothing sent")
        req = Request(self.origin + path, data=payload, method=method,
                      headers={"Authorization": "Bearer " + self._token, "Content-Type": "application/json"})
        try:
            with self.opener.open(req, timeout=5) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise OperatorError("Control snapshot too large; use a smaller deployment or paginated API")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError("unexpected response")
            return result
        except HTTPError as exc:
            raise OperatorError(f"Gateway returned HTTP {exc.code}; inspect current state before retrying a mutation") from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise OperatorError("Gateway response unavailable or invalid; outcome unknown. Inspect state before retrying a mutation") from None


def review_view(snapshot: dict, agent: str, request_id: str) -> dict:
    match = next((r for r in snapshot["approvals"] if r["principal"] == agent and r["id"] == request_id), None)
    if match is None:
        raise OperatorError("No outstanding request for that exact agent and request ID")
    visa_id = match["action"]["visa_id"]
    visa = next((v for v in snapshot["visas"] if v["id"] == visa_id), None)
    if visa is None:
        raise OperatorError("Request visa is unavailable")
    response = match["response"]
    return {"agent": agent, "request_id": request_id, "fingerprint": match["fingerprint"],
            "visa_id": visa_id, "mission": visa["contract"]["mission"], "visa_status": visa["status"],
            "approval_status": match["approval"], "deadline": match["deadline"],
            "expired": int(time.time()) >= match["deadline"], "action": match["action"],
            "cost_cents": response.get("cost_cents"), "impact": response.get("estimated_impact"),
            "reason": response["reason"], "intent": response.get("intent"),
            "policy_checks": response.get("policy_checks", [])}


def parser():
    root = argparse.ArgumentParser(prog="python -m agentvisa.operator")
    root.add_argument("--url", default="http://127.0.0.1:8000", help="Trusted gateway origin")
    root.add_argument("--config", help="Private JSON containing admin_token; otherwise use AGENTVISA_ADMIN_TOKEN")
    commands = root.add_subparsers(dest="command", required=True)
    draft = commands.add_parser("draft")
    draft.add_argument("--mission", required=True)
    draft.add_argument("--agent", required=True)
    draft.add_argument("--output", required=True, help="New contract file; never overwrites")
    for name in ("issue", "modify"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--contract", required=True)
        if name == "modify":
            cmd.add_argument("--visa", required=True)
    commands.add_parser("visas")
    commands.add_parser("approvals")
    commands.add_parser("delegations")
    commands.add_parser("integrity")
    for name in ("inspect", "approve", "reject"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--agent", required=True)
        cmd.add_argument("--request-id", required=True)
        if name != "inspect":
            cmd.add_argument("--fingerprint", required=True, help="Exact hash shown by inspect")
    revoke = commands.add_parser("revoke")
    revoke.add_argument("--visa", required=True)
    audit = commands.add_parser("audit")
    audit.add_argument("--limit", type=int, default=25)
    audit.add_argument("--blocked", action="store_true")
    return root


def run(args, client: ControlClient):
    command = args.command
    if command == "draft":
        destination = Path(args.output)
        if destination.exists():
            raise OperatorError("Draft output already exists; choose a new path")
        result = client.request("POST", "/drafts", {"mission": args.mission, "agent_id": args.agent})
        contract = Contract(**result["contract"]).dictionary()
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as file:
            json.dump(contract, file, indent=2)
            file.write("\n")
        return {"contract_file": str(destination), "next_step": "Inspect/edit the contract, then run issue --contract with that path"}
    if command in ("issue", "modify"):
        path = Path(args.contract)
        if path.stat().st_size > 65536:
            raise OperatorError("Contract file too large")
        contract = Contract(**json.loads(path.read_text())).dictionary()
        return client.request("POST" if command == "issue" else "PUT",
                              "/visas" if command == "issue" else "/visas/" + quote(args.visa, safe=""), contract)
    if command == "revoke":
        return client.request("POST", "/visas/" + quote(args.visa, safe="") + "/revoke")
    if command == "integrity":
        result = client.request("GET", "/audit/integrity")
        if result.get("valid") is not True:
            raise OperatorError("Audit integrity verification failed")
        return result
    if command == "audit" and not 1 <= args.limit <= 1000:
        raise OperatorError("Audit limit must be between 1 and 1000")
    if command in ("approve", "reject") and not re.fullmatch(r"[a-f0-9]{64}", args.fingerprint):
        raise OperatorError("Fingerprint must be the 64-character lowercase hash from inspect")
    snapshot = client.request("GET", "/control")
    if command == "visas":
        return {"visas": snapshot["visas"]}
    if command == "delegations":
        return {"delegations": [{"visa_id": v["id"], "parent": v["parent"], "agent": v["contract"]["agent_id"],
                                  "status": v["status"], "spent_cents": v["spent"]} for v in snapshot["visas"]]}
    if command == "approvals":
        return {"approvals": [review_view(snapshot, r["principal"], r["id"]) for r in snapshot["approvals"]]}
    if command in ("inspect", "approve", "reject"):
        review = review_view(snapshot, args.agent, args.request_id)
        if command == "inspect":
            return review
        if review["fingerprint"] != args.fingerprint or review["approval_status"] != "pending" or review["expired"]:
            raise OperatorError("Review is stale, expired, not pending, or fingerprint mismatches; inspect again")
        result = client.request("POST", "/approvals", {"agent_id": args.agent, "request_id": args.request_id,
                                                       "approve": command == "approve", "expected_fingerprint": args.fingerprint})
        return {"review": review, "result": result, "execution": "No tool executed by this command; the agent must retry its exact action"}
    if command == "audit":
        rows = snapshot["audit"]
        if args.blocked:
            rows = [r for r in rows if r["event"].get("decision") == "DENY" or r["event"].get("event") == "delegation_denied"]
        return {"audit": rows[-args.limit:]}
    raise OperatorError("Unsupported operator command")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        token = json.loads(Path(args.config).read_text())["admin_token"] if args.config else os.environ["AGENTVISA_ADMIN_TOKEN"]
        result = run(args, ControlClient(args.url, token))
        # Escaping control characters keeps untrusted agent text inert in terminals.
        print(json.dumps(result, indent=2, ensure_ascii=True))
    except OperatorError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
    except (ValueError, TypeError, KeyError, OSError):
        print("Operator command failed. Check credentials, gateway state, file paths and review fingerprint; no automatic retry was attempted.", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
