# coding=utf-8
#
# This file is part of Hypothesis, which may be found at
# https://github.com/HypothesisWorks/hypothesis/
#
# Most of this work is copyright (C) 2013-2019 David R. MacIver
# (david@drmaciver.com), but it contains contributions by others. See
# CONTRIBUTING.rst for a full list of people who may hold copyright, and
# consult the git log if you need to determine who owns an individual
# contribution.
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at https://mozilla.org/MPL/2.0/.
#
# END HEADER

from __future__ import absolute_import, division, print_function

from hypothesis import HealthCheck, Phase, settings
from hypothesis.database import InMemoryExampleDatabase
from hypothesis.internal.compat import hbytes, hrange
from hypothesis.internal.conjecture.data import Status
from hypothesis.internal.conjecture.engine import (
    ConjectureRunner,
)
from hypothesis.internal.entropy import deterministic_PRNG


def test_pareto_front_contains_different_interesting_reasons():
    with deterministic_PRNG():

        def test(data):
            data.mark_interesting(data.draw_bits(4))

        runner = ConjectureRunner(
            test,
            settings=settings(
                max_examples=5000,
                database=InMemoryExampleDatabase(),
                suppress_health_check=HealthCheck.all(),
            ),
            database_key=b"stuff",
        )

        runner.run()

        assert len(runner.pareto_front) == 2 ** 4


def test_database_contains_only_pareto_front():
    with deterministic_PRNG():

        def test(data):
            data.target_observations["1"] = data.draw_bits(4)
            data.draw_bits(64)
            data.target_observations["2"] = data.draw_bits(8)

        db = InMemoryExampleDatabase()

        runner = ConjectureRunner(
            test,
            settings=settings(
                max_examples=500, database=db, suppress_health_check=HealthCheck.all(),
            ),
            database_key=b"stuff",
        )

        runner.run()

        assert len(runner.pareto_front) <= 500

        for v in runner.pareto_front:
            assert v.status >= Status.VALID

        assert len(db.data) == 1

        (values,) = db.data.values()
        values = set(values)

        assert len(values) == len(runner.pareto_front)

        for data in runner.pareto_front:
            assert data.buffer in values
            assert data in runner.pareto_front

        for k in values:
            assert runner.cached_test_function(k) in runner.pareto_front


def test_clears_defunct_pareto_front():
    with deterministic_PRNG():

        def test(data):
            data.draw_bits(8)
            data.draw_bits(8)

        db = InMemoryExampleDatabase()

        runner = ConjectureRunner(
            test,
            settings=settings(
                max_examples=10000,
                database=db,
                suppress_health_check=HealthCheck.all(),
                phases=[Phase.reuse],
            ),
            database_key=b"stuff",
        )

        for i in hrange(256):
            db.save(runner.pareto_key, hbytes([i, 0]))

        runner.run()

        assert len(list(db.fetch(runner.pareto_key))) == 1
