# SPDX-License-Identifier: GPL-2.0-or-later
"""Processing algorithms that drive an external engine.

``specs/07-engine-dynadjust.md``. These are thin: the pipeline, the parsers and
the comparison all live in :mod:`geocomp.engines`, QGIS-free and tested
wherever Python runs. What is here is the Processing face of them -- parameters,
progress, and the failure messages a user acts on.
"""
