# -*- coding: utf-8 -*-
import base64
import hashlib

from django.utils.crypto import (
    constant_time_compare, get_random_string, pbkdf2,
)


class PBKDF2PasswordHasher(object):
    """
    Secure password hashing using the PBKDF2 algorithm

    Configured to use PBKDF2 + HMAC + SHA256.
    The result is a 64 byte binary string.  Iterations may be changed
    safely but you must rename the algorithm if you change SHA256.
    """
    iterations = 300000
    digest = hashlib.sha256

    def salt(self):
        """
        Generates a cryptographically secure nonce salt in ASCII
        """
        return get_random_string()

    def encode(self, password, salt):
        assert password is not None
        assert salt and '$' not in salt

        hash = pbkdf2(password, salt, self.iterations, digest=self.digest)
        hash = base64.b64encode(hash).decode('ascii').strip()
        return "%d$%s$%s" % (self.iterations, salt, hash)

    def verify(self, password, encoded):
        _, salt, hash = encoded.split('$', 2)
        encoded_2 = self.encode(password, salt)
        return constant_time_compare(encoded, encoded_2)


def check_password(password, encoded, hasher_cls=PBKDF2PasswordHasher):
    """
    Returns a boolean of whether the raw password matches the three
    part encoded digest.
    """
    hasher = hasher_cls()
    is_correct = hasher.verify(password, encoded)

    return is_correct


def make_password(password, hasher_cls=PBKDF2PasswordHasher):
    """
    Turn a plain-text password into a hash for database storage
    """
    hasher = hasher_cls()
    salt = hasher.salt()

    return hasher.encode(password, salt)
