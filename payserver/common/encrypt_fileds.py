# -*- coding: utf-8 -*-
#  
#       File ：  encrypt_fileds
#    Project ：  payunion
#     Author ：  Tian Xu
#     Create ：  18-8-31
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import os
import binascii

import django
from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property

from .encryption import AESCipher


class EncryptedCharField(models.CharField):
   
    def __init__(self, *args, **kwargs):
        """
        * key: The name of the keyczar key. It's necessary if you want to work normal.
        * crypter_class: A custom class that is extended from AESCipher. Not necessary.
        """
        # The encrypt class, Default is AESCipher
        self._crypter_class = kwargs.pop('crypter_class', AESCipher)

        # The encrypt key
        self.key = kwargs.pop('key', '')

        self._load_crypter()

        super().__init__(*args, **kwargs)

    def _decrypt(self, value):
        return self._crypter.decrypt(value)

    def _encrypt(self, value):
        return self._crypter.encrypt(value)

    def _load_crypter(self):
        self._crypter = self._crypter_class(self.key)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        value = super().to_python(value)
        if value is None or value == '':
            return value
        return self._decrypt(value)

    def get_prep_value(self, value):
        super_class = self.__class__.mro()[2]
        value = super_class().get_prep_value(value)
        if value is None or value == '':
            return value
        value = self._encrypt(value)
        return value
