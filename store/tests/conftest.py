'''
a special file for pytest, fixures or reusable function defined here,
pytest will automatically load them without us have to explicitly import this module
'''

from django.contrib.auth.models import User
from rest_framework.test import APIClient
import pytest


# this fixture return an obj
@pytest.fixture
def api_client():
    return APIClient()
