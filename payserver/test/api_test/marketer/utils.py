import uuid

from django.core.cache import cache


class MarketerLoginedMixin:
    """
        must be first e.g.
        class TestStatistics(MerchantLoginedMixin, APITestCase):
    """
    @classmethod
    def setUpTestData(cls):
        cls.token = uuid.uuid4()
        cache.set(cls.token, dict(
            openid=cls.marketer.wechat_openid,
            unionid=cls.marketer.wechat_unionid,
            session_key='session key'),
            300)
