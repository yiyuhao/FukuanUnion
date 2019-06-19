# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import base64
import hashlib

from Crypto.Cipher import AES


class AesCrypter(object):

    def __init__(self, key):
        self.key = hashlib.md5(key.encode('utf-8')).hexdigest().encode(encoding='utf-8')
        self.cipher = AES.new(self.key, AES.MODE_ECB)

    def decrypt(self, data):
        data = base64.b64decode(data)
        decrypted = self.cipher.decrypt(data)
        decrypted = self._pkcs7unpadding(decrypted)
        return decrypted.decode('utf-8')

    def encrypt(self, string):
        data = string.encode('utf-8')
        data = self._pkcs7padding(data)
        encrypted = self.cipher.encrypt(data)
        return base64.b64encode(encrypted).decode()

    def _pkcs7unpadding(self, data):
        unpadding = data[-1]
        return data[0:-unpadding]

    def _pkcs7padding(self, data):
        block_size = 16
        padding = block_size - len(data) % block_size
        padding_data = bytes([padding] * padding)
        return data + padding_data
