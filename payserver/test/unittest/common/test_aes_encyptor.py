# -*- coding: utf-8 -*-
#
#   Project: payunion
#    Author: Xie Wangyi
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
from unittest import TestCase

from common.aes import AesCrypter


class AesCrypterTestCase(TestCase):
    def test_encrypt(self):
        encrypt = AesCrypter('mixadx').encrypt('ABCDEF')
        self.assertEqual(encrypt, 'xC+1feTKJOARgWxwGim7LQ==')

    def test_decrypt(self):
        decrypt = AesCrypter('mixadx').decrypt('xC+1feTKJOARgWxwGim7LQ==')
        self.assertEqual(decrypt, 'ABCDEF')
