from adfree_proxy.policy import PolicyEvaluator


def test_evaluate_default_allows():
    evaluator = PolicyEvaluator(rules={})
    decision = evaluator.evaluate({'path': '/'})
    assert 'action' in decision
