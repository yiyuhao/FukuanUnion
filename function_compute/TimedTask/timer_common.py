"""
定时任务共用
"""
import hashlib
import time


class TokenGenerate(object):
    def __init__(self, token, key_type):
        self.token = token
        self.key_type = key_type

    def get_token_params(self):
        import string
        import random

        time_stamp = int(time.time())
        random_key = ''.join(random.sample(string.ascii_letters + string.digits, 32))
        key_type = self.key_type
        token = self.token

        param_list = [token, str(time_stamp), random_key, key_type]
        param_list.sort()
        sha1 = hashlib.sha1()
        sha1.update("".join(param_list).encode('utf-8'))
        signature = sha1.hexdigest()

        data = {
            'timestamp': time_stamp,
            'key': random_key,
            'signature': signature,
            'key_type': key_type
        }
        return data