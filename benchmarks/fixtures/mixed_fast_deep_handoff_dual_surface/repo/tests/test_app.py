from src.app import evaluate_expression


def test_rejects_eval() -> None:
    assert evaluate_expression("1 + 1") == 2
