import pytest
from fastapi.testclient import TestClient
from agentvisa.api import create_app
from agentvisa.gateway import Gateway

ADMIN, AGENT, OTHER = "admin-" + "x" * 40, "agent-" + "y" * 40, "other-" + "z" * 40


def auth(token):
    return {"Authorization": "Bearer " + token}


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(Gateway(str(tmp_path / "api.db")), ADMIN, {AGENT: "a", OTHER: "b"}))


def issue(client):
    response = client.post("/drafts", json={"mission": "Buy a monitor under $300.", "agent_id": "a"}, headers=auth(ADMIN))
    return client.post("/visas", json=response.json()["contract"], headers=auth(ADMIN)).json()["visa_id"]


def test_admin_agent_separation(client):
    assert client.get("/control").status_code == 401
    assert client.get("/control", headers=auth(AGENT)).status_code == 403
    assert client.post("/visas", json={}, headers=auth(AGENT)).status_code == 403
    assert client.post("/approvals", json={}, headers=auth(AGENT)).status_code == 403
    assert client.get("/tools/purchase").status_code == 404


def test_end_to_end_approval(client):
    v = issue(client)
    body = {"request_id": "one", "visa_id": v, "tool": "purchase", "resource": "vendor:approved", "arguments": {"product_id": "monitor-pro", "quantity": 1}}
    assert client.post("/execute", json=body, headers=auth(OTHER)).json()["decision"] == "DENY"
    assert client.post("/execute", json=body, headers=auth(ADMIN)).status_code == 403
    assert client.post("/execute", json=body, headers=auth(AGENT)).json()["decision"] == "ASK_HUMAN"
    review = {"agent_id": "a", "request_id": "one", "approve": True}
    assert client.post("/approvals", json=review, headers=auth(ADMIN)).status_code == 200
    assert client.post("/execute", json=body, headers=auth(AGENT)).json()["executed"]
    assert len(client.get("/control", headers=auth(ADMIN)).json()["effects"]) == 1


def test_extra_fields_and_body_limit(client):
    v = issue(client)
    body = {"request_id": "one", "visa_id": v, "tool": "purchase", "resource": "vendor:approved", "arguments": {"product_id": "monitor-pro", "quantity": 1}, "agent_id": "a"}
    assert client.post("/execute", json=body, headers=auth(AGENT)).status_code == 422
    assert client.post("/execute", content=b"x" * 70000, headers=auth(AGENT)).status_code == 413


def test_no_insecure_defaults(tmp_path):
    with pytest.raises(ValueError):
        create_app(Gateway(str(tmp_path / "bad.db")), "short", {AGENT: "a"})


def test_invalid_contract(client):
    assert client.post("/visas", json={"agent_id": "a", "mission": "Buy monitor", "spending_limit": True}, headers=auth(ADMIN)).status_code == 422


def test_approval_fingerprint_checked_by_api(client):
    visa = issue(client)
    action = {"request_id": "review", "visa_id": visa, "tool": "purchase", "resource": "vendor:approved", "arguments": {"product_id": "monitor-pro", "quantity": 1}}
    assert client.post("/execute", json=action, headers=auth(AGENT)).json()["decision"] == "ASK_HUMAN"
    request = client.get("/control", headers=auth(ADMIN)).json()["approvals"][0]
    body = {"agent_id": "a", "request_id": "review", "approve": True, "expected_fingerprint": "0" * 64}
    assert client.post("/approvals", json=body, headers=auth(ADMIN)).status_code == 422
    body["expected_fingerprint"] = request["fingerprint"]
    assert client.post("/approvals", json=body, headers=auth(AGENT)).status_code == 403
    assert client.post("/approvals", json=body, headers=auth(ADMIN)).status_code == 200
