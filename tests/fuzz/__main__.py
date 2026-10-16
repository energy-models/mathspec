# SPDX-FileCopyrightText: mathspec Contributors
#
# SPDX-License-Identifier: MIT

"""``python -m tests.fuzz``: the campaign in :mod:`tests.fuzz.run`."""

import sys

from tests.fuzz.run import main

if __name__ == '__main__':
    sys.exit(main())
