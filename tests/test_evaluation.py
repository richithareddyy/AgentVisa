from pathlib import Path
from agentvisa.demo import run as demo
from agentvisa.evaluation import run


def test_labeled_regression_dataset():
    result = run(str(Path(__file__).parents[1] / "evaluation" / "cases.json"))
    assert result["dangerous_false_allow_rate"] == 0
    assert result["exact_decision_accuracy"] == 1
    assert result["prompt_injection_containment_rate"] == 1
    assert result["delegation_escalation_prevention_rate"] == 1


def test_six_demo_scenarios():
    assert [r["decision"] for r in demo()] == ["ALLOW", "DENY", "ASK_HUMAN", "ALLOW", "DENY", "DENY", "DENY"]
