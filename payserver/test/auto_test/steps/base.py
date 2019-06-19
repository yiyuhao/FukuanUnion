from rest_framework.test import APIClient


class BaseStep:
    client = APIClient()
