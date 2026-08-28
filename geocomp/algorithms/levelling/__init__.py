# SPDX-License-Identifier: GPL-2.0-or-later
"""Processing algorithms for geometric levelling (FR-500 to FR-505).

``specs/10-module-levelling.md``. Six algorithms, in the order of the work: get
the book in, reduce it by whichever scheme was used, check the closures, adjust
the network.

The three schemes are three algorithms even though equal and extreme sights
share an implementation, because they answer different questions and produce
different things. Equal sights reduces a **line** to one height difference
between two marks. Extreme sights reduces a **setup** to several height
differences that are correlated with each other -- which is the whole point of
the scheme, and is invisible in a line reduction.
"""
