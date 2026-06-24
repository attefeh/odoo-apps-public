# -*- coding: utf-8 -*-
from . import models
from . import wizard


def post_init_hook(env):
    """Trigger the first term sync once the module (and its cron) is installed,
    in case the registry-load hook ran before our data was loaded."""
    env['translation.term']._auto_sync_on_schema_change()
