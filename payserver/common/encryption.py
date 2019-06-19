import string
import random
from Crypto.Cipher import AES
import base64


def generate_key(k):
    seed = string.digits + string.ascii_letters
    key = ''.join(random.choices(population=seed, k=k))
    with open('KEY.txt', 'w', encoding='utf8') as f:
        f.write(key)
    return key


class AESCipher:
    def __init__(self, key):
        self.key = key.encode('utf8')
        self.mode = AES.MODE_CBC
        self.BS = 16

    def _pad(self, s):
        s = s.encode('utf8')
        length = len(s)
        add = self.BS - length % self.BS
        return s + ('\0' * add).encode('utf8')

    def encrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.key)
        text = self._pad(text)
        return base64.b64encode(cryptor.encrypt(text)).decode()

    def decrypt(self, text):
        text = base64.b64decode(text)
        cryptor = AES.new(self.key, self.mode, self.key)
        try:
            return str(cryptor.decrypt(text), 'utf-8').rstrip('\0')
        except UnicodeDecodeError:
            return cryptor.decrypt(text)




