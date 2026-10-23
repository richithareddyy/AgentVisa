"""Authenticated HTTP boundary. Protected adapters are never exposed as routes."""
import hmac
import json
import os
import sqlite3
from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from .gateway import Gateway
from .models import Action, Contract, draft


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class MissionDraft(StrictModel):
    mission: str = Field(min_length=1, max_length=2000)
    agent_id: str = Field(min_length=1, max_length=100)


class Review(StrictModel):
    agent_id: str
    request_id: str
    approve: bool
    expected_fingerprint: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class ActionBody(StrictModel):
    request_id: str
    visa_id: str
    tool: str
    resource: str
    arguments: dict
    context: str = Field(default="", max_length=4000)


class BodyLimit:
    """Buffer a bounded body before parsing; also covers chunked requests."""
    def __init__(self, app, limit=65536):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.limit:
                response = JSONResponse({"detail": "request body too large"}, status_code=413)
                return await response(scope, receive, send)
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        sent = False
        async def bounded_receive():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()
        await self.app(scope, bounded_receive, send)


def create_app(gateway: Gateway, admin_token: str, agent_tokens: dict[str, str]) -> FastAPI:
    """Tokens map to identities on the server, never from request agent_id fields."""
    if len(admin_token) < 32 or not agent_tokens or any(type(k) is not str or len(k) < 32 or type(v) is not str or not v for k, v in agent_tokens.items()) or admin_token in agent_tokens:
        raise ValueError("distinct admin/agent credentials of at least 32 characters required")
    app = FastAPI(title="AgentVisa", version="0.1.0", description="Mission-scoped authorization and simulated protected execution.")
    app.add_middleware(BodyLimit)
    bearer = HTTPBearer(auto_error=False)

    def token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(401, "bearer credential required")
        return credentials.credentials

    def admin(value: str = Depends(token)):
        if not hmac.compare_digest(value.encode(), admin_token.encode()):
            raise HTTPException(403, "human administrator credential required")

    def agent(value: str = Depends(token)) -> str:
        for secret, identity in agent_tokens.items():
            if hmac.compare_digest(value.encode(), secret.encode()):
                return identity
        raise HTTPException(403, "unknown agent credential")

    @app.exception_handler(ValueError)
    @app.exception_handler(TypeError)
    async def invalid(_request: Request, exc: Exception):
        return JSONResponse({"detail": str(exc)}, status_code=422)

    @app.exception_handler(sqlite3.Error)
    async def unavailable(_request: Request, _exc: Exception):
        return JSONResponse({"detail": "authorization store unavailable; execution not confirmed"}, status_code=503)

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "simulation"}

    @app.post("/drafts", dependencies=[Depends(admin)])
    def draft_contract(body: MissionDraft):
        return {"requires_human_review": True, "contract": draft(body.mission, body.agent_id).dictionary()}

    @app.post("/visas", dependencies=[Depends(admin)])
    def issue(body: dict = Body(...)):
        return gateway.issue(Contract(**body))

    @app.put("/visas/{visa_id}", dependencies=[Depends(admin)])
    def modify(visa_id: str, body: dict = Body(...)):
        gateway.modify(visa_id, Contract(**body))
        return {"updated": True}

    @app.post("/visas/{visa_id}/revoke", dependencies=[Depends(admin)])
    def revoke(visa_id: str):
        gateway.revoke(visa_id)
        return {"revoked": True}

    @app.post("/visas/{visa_id}/delegate")
    def delegate(visa_id: str, body: dict = Body(...), principal: str = Depends(agent)):
        return gateway.delegate(principal, visa_id, Contract(**body))

    @app.post("/execute")
    def execute(body: ActionBody, principal: str = Depends(agent)):
        return gateway.execute(principal, Action(**body.model_dump()))

    @app.post("/approvals", dependencies=[Depends(admin)])
    def approval(body: Review):
        return gateway.approve(body.agent_id, body.request_id, body.approve, body.expected_fingerprint)

    @app.get("/control", dependencies=[Depends(admin)])
    def control():
        return gateway.snapshot()

    @app.get("/audit/integrity", dependencies=[Depends(admin)])
    def integrity():
        return {"valid": gateway.verify_audit(), "scope": "local hash chain; not an external tamper-proof log"}

    return app


def from_environment() -> FastAPI:
    try:
        admin_token = os.environ["AGENTVISA_ADMIN_TOKEN"]
        agents = json.loads(os.environ["AGENTVISA_AGENT_TOKENS"])
        if not isinstance(agents, dict):
            raise ValueError("agent credentials must be a JSON object")
    except (KeyError, ValueError) as exc:
        raise RuntimeError("Set AGENTVISA_ADMIN_TOKEN and AGENTVISA_AGENT_TOKENS before startup") from exc
    return create_app(Gateway(os.environ.get("AGENTVISA_DB", "agentvisa.db")), admin_token, agents)
