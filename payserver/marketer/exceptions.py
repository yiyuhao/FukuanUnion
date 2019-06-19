import logging

logger = logging.getLogger(__name__)


class CreateErrorException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class RequestFailException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class AliyunMarketApiParamsException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class InvalidParamsException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

