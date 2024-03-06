# noqa: D100

# When installed as a script, Poetry generates a wrapper that calls `sys.exit(main())`.
# Therefore, doing that in this file means the program can be run via `python -m` and
# exhibit the exact same behavior as if it were installed and run as a script. In order
# to maintain this compatibility, do not add or modify any statements in this file, or
# else `python -m` will execute them but the installed script won't.

import sys

from pgloader._main import main

sys.exit(main())
