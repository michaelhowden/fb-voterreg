#!/usr/bin/env python
import os
import sys

import sys;sys.path.append(r'/code/eclipse/plugins/org.python.pydev.debug_2.2.1.2011071313/pysrc')

#import pydevd
#pydevd.patch_django_autoreload(
#patch_remote_debugger=True, #Connect to the remote debugger.
#patch_show_console=True
#)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "voterreg.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
