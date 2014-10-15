#!/usr/bin/env python
import os
import sys

# append current dir's parent to sys.path or the stupid settings won't be found
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webpos.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
