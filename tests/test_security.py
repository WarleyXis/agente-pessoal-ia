from backend.core.security import requires_approval
from backend.tools.base import RiskLevel


def test_low_risk_does_not_require_approval():
    assert requires_approval(RiskLevel.LOW) is False


def test_high_risk_requires_approval():
    assert requires_approval(RiskLevel.HIGH) is True