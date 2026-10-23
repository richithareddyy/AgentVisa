"""Interchangeable intent evaluator; default is a conservative domain baseline."""
from dataclasses import asdict, dataclass
import re
import math
from typing import Protocol
from .models import Action, Contract, Decision
from .tools import Prepared


@dataclass(frozen=True)
class Intent:
    mission_alignment_score: float
    risk_score: float
    reason: str
    evidence: list[str]
    recommended_decision: Decision

    def validate(self, *, reason_limit=4096, evidence_limit=40) -> None:
        if type(self.recommended_decision) is not str or self.recommended_decision not in ("ALLOW", "DENY", "ASK_HUMAN"):
            raise ValueError("invalid intent decision")
        for score in (self.mission_alignment_score, self.risk_score):
            if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError("invalid intent score")
        if type(self.reason) is not str or not self.reason.strip() or len(self.reason) > reason_limit:
            raise ValueError("invalid intent reason")
        if type(self.evidence) is not list or len(self.evidence) > evidence_limit or any(
            type(item) is not str or not item.strip() or len(item) > 500 for item in self.evidence
        ):
            raise ValueError("invalid intent evidence")

    def dictionary(self) -> dict:
        return asdict(self)


class Evaluator(Protocol):
    def evaluate(self, contract: Contract, action: Action, prepared: Prepared) -> Intent: ...


class ProcurementEvaluator:
    """Domain semantics from trusted catalog plus a deliberately narrow text grammar.

    Scores are diagnostic heuristics, not calibrated probabilities. A future model
    evaluator must keep this structured interface and cannot override hard policy.
    """
    def evaluate(self, contract: Contract, action: Action, prepared: Prepared) -> Intent:
        if prepared.category != "monitor":
            return Intent(.02, .95, "Product category is outside the authorized mission", [prepared.category], "DENY")
        if action.tool == "upload_file" or "file:employees.csv" in prepared.resources:
            return Intent(.01, .99, "Data transfer is unrelated to monitor procurement", sorted(prepared.resources), "DENY")
        if action.tool == "search_products":
            query = action.arguments["query"].lower().strip()
            if re.fullmatch(r"(?:(?:buy|compare|affordable|office|27 inch|24 inch) )?monitors?", query):
                return Intent(.95, .05, "Bounded monitor catalog search", [query], "ALLOW")
            if any(word in query for word in ("employees", "password", "upload", "ignore previous", "headphones")):
                return Intent(.03, .95, "Search asks for unrelated data or instruction override", ["unrelated search content"], "DENY")
            return Intent(.5, .5, "Search meaning is outside the reviewed query grammar", ["unrecognized query"], "ASK_HUMAN")
        if action.tool == "send_email":
            body = action.arguments["body"].lower().strip()
            if body in ("please send a quote for a monitor.", "please confirm monitor availability."):
                return Intent(.95, .25, "Reviewed vendor inquiry", ["approved vendor", "bounded message template"], "ALLOW")
            if any(word in body for word in ("employees", "payroll", "password", "vacation", "ignore previous")):
                return Intent(.04, .95, "Message content is unrelated to procurement", ["off-mission message"], "DENY")
            return Intent(.5, .6, "Free-form external communication requires review", ["unreviewed message"], "ASK_HUMAN")
        return Intent(.98, .3 if prepared.cost else .05, "Trusted catalog items match the mission", ["category:monitor"], "ALLOW")
