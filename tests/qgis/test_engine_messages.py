# SPDX-License-Identifier: GPL-2.0-or-later
"""An engine's failure, as the user reads it (FR-305, NFR-006; P12c-7).

Until P12c-7 none of the engine package's 81 codes had a template. *GNSS
processing* rendered an ``rnx2rtkp`` failure as "GeoComp could not complete the
operation (engine.rtklib_run_failed)" -- the engine's own message, which
``specs/08`` section 9 requires, was on the error and nowhere on the screen --
and *Adjust network (DynAdjust)* showed the code with its context.

Each error here carries the context its raise site builds;
``tests/structural/test_message_templates.py`` holds the two to each other.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.qgis

#: (error class, code, context as the raise site builds it, the engine's own words)
FAILURES = [
    (
        "EngineError",
        "rtklib_run_failed",
        {
            "engine": "rnx2rtkp",
            "exit_code": 1,
            "timed_out": False,
            "command": "rnx2rtkp -k rnx2rtkp.conf -o 0759.pos 0759.obs",
            "message": "error : no obs data",
            "work_dir": "/work/relative-static-0759",
        },
        "error : no obs data",
    ),
    (
        "EngineError",
        "rtklib_wrote_no_output",
        {
            "engine": "rnx2rtkp",
            "command": "rnx2rtkp -k rnx2rtkp.conf -o 0759.pos 0759.obs",
            "message": "file open error: 0759.pos",
            "work_dir": "/work/relative-static-0759",
            "expected": "a solution file at 0759.pos",
        },
        "file open error: 0759.pos",
    ),
    (
        "EngineError",
        "rtklib_produced_no_solution",
        {
            "engine": "rnx2rtkp",
            "rover": "0759",
            "base": "3040",
            "message": "no common epoch with base",
            "work_dir": "/work/relative-static-0759",
            "expected": "at least one solution epoch",
        },
        "no common epoch with base",
    ),
    (
        "ComputationError",
        "dynadjust_stage_failed",
        {
            "program": "dnaimport",
            "exit_code": 1,
            "diagnostic": "- Error: station BM12 has no coordinates (line 14)",
            "completed": [],
        },
        "station BM12 has no coordinates",
    ),
    (
        "ComputationError",
        "dynadjust_import_incomplete",
        {
            "expected": {"stations": 5, "measurements": 12},
            "received": {"stations": 5, "measurements": 11},
            "diagnostic": "+ Warning: measurement 7 ignored",
            "hint": "dnaimport reported success but did not take in everything",
        },
        "measurement 7 ignored",
    ),
]


@pytest.fixture(scope="module", autouse=True)
def _registered(geocomp_provider):
    """The templates register when the algorithm packages are imported."""
    return geocomp_provider


@pytest.mark.parametrize(("kind", "code", "context", "own_words"), FAILURES, ids=[f[1] for f in FAILURES])
def test_a_failed_run_shows_the_engines_own_message(kind, code, context, own_words):
    from geocomp.algorithms.gnss.common import translate_error
    from geocomp.core import errors

    text = translate_error(getattr(errors, kind)(code, **context))
    assert own_words in text
    assert "could not complete the operation" not in text
    assert "(not set)" not in text


def test_a_failed_batch_session_is_said_in_words(tmp_path):
    """*Batch GNSS processing* reports each failed session; now with its template."""
    from geocomp.algorithms.gnss.common import translate_error
    from geocomp.core.errors import EngineError
    from geocomp.core.techniques.gnss.batch import run_batch

    _kind, code, context, own_words = FAILURES[0]
    report = run_batch(["0759"], lambda key: (_ for _ in ()).throw(EngineError(code, **context)))
    (failed,) = report.failed
    assert own_words in translate_error(failed.error)


def test_every_engine_template_renders_from_its_own_keys():
    """A template given exactly the keys it names says no '(not set)' and no '%n'."""
    from geocomp.algorithms.engines.messages import TEMPLATES as ENGINES
    from geocomp.algorithms.gnss.messages import TEMPLATES as GNSS

    for code, template in {**ENGINES, **GNSS}.items():
        text = template.render({key: f"<{key}>" for key in template.keys})
        assert "(not set)" not in text, code
        assert "%" not in text.replace("% ref pos", ""), code
        for key in template.keys:
            assert f"<{key}>" in text, (code, key)
