# -*- coding: utf-8 -*-
# Install the code-translation override as soon as the module is imported.
from . import code_translations_patch

code_translations_patch.install_patch()

from . import translation_term
