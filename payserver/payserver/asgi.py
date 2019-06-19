# -*- coding: utf-8 -*-
#       File: asgi.py
#    Project: simple
#     Author: Tian Xu
#     Create: 18-7-17
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os
import django
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payserver.settings")
django.setup()
application = get_default_application()