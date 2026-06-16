"""PyInstaller entry point for the frozen citetab desktop app.

Delegates to :func:`citetab.app.main`, which opens the file picker when launched
with no argument (double-click) or processes a given brief headlessly when a path
is passed (drag-onto-icon / command line). The process exit code is the
generation outcome's.
"""

import sys

from citetab.app import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
