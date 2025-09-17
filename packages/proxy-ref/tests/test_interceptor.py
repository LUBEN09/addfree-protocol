import asyncio
from adfree_proxy.policy import PolicyEvaluator
from adfree_proxy.interceptor import RequestInterceptor


class DummyRequest:
    def __init__(self):
        self.rel_url = '/'  
        self.method = 'GET'


def test_intercept_runs():
    evaluator = PolicyEvaluator({})
    interceptor = RequestInterceptor(evaluator)
    req = DummyRequest()
    decision = asyncio.get_event_loop().run_until_complete(interceptor.intercept(req))
    assert 'action' in decision
