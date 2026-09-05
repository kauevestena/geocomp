# SPDX-License-Identifier: GPL-2.0-or-later
"""Processing algorithms.

One file per algorithm, grouped as in the menu. Every algorithm is declared in
:mod:`geocomp.registry`; adding a class here without registering it is caught by
``tests/structural/test_menu_algorithm_parity.py``.
"""

from __future__ import annotations
