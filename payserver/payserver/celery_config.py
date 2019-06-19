#
#      File: celery_config.py
#   Project: payunion
#    Author: Yi Yuhao
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from __future__ import absolute_import

from dynaconf import settings as dynasettings

BROKER_URL = f"redis://" \
             f"{':%s@' % dynasettings.REDIS_PASSWORD if dynasettings.REDIS_PASSWORD else ''}" \
             f"{dynasettings.REDIS_HOST}:{dynasettings.as_int('REDIS_PORT')}" \
             f"/5"

CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_ALWAYS_EAGER = False
CELERYD_REDIRECT_STDOUTS_LEVEL = 'INFO'
CELERYD_CONCURRENCY = 4
CELERY_ACKS_LATE = True
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_DEFAULT_QUEUE = 'payunion'
CELERY_INCLUDE = ['common.tasks']
