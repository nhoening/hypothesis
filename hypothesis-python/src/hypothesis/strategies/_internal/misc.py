# This file is part of Hypothesis, which may be found at
# https://github.com/HypothesisWorks/hypothesis/
#
# Most of this work is copyright (C) 2013-2021 David R. MacIver
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

from hypothesis.strategies._internal.strategies import (
    FilteredStrategy,
    SampledFromStrategy,
    SearchStrategy,
    T,
    filter_not_satisfied,
    is_simple_data,
)
from hypothesis.strategies._internal.utils import cacheable, defines_strategy


class JustStrategy(SampledFromStrategy):
    """A strategy which always returns a single fixed value.

    It's implemented as a length-one SampledFromStrategy so that all our
    special-case logic for filtering and sets applies also to just(x).

    The important difference from a SampledFromStrategy with only one
    element to choose is that JustStrategy *never* touches the underlying
    choice sequence, i.e. drawing neither reads from nor writes to `data`.
    This is a reasonably important optimisation (or semantic distinction!)
    for both JustStrategy and SampledFromStrategy.
    """

    @property
    def value(self):
        return self.elements[0]

    def __repr__(self):
        if self.value is None:
            return "none()"
        return f"just({self.value!r})"

    def calc_has_reusable_values(self, recur):
        return True

    def calc_is_cacheable(self, recur):
        return is_simple_data(self.value)

    def do_draw(self, data):
        result = self._transform(self.value)
        if result is filter_not_satisfied:
            data.note_event(f"Aborted test because unable to satisfy {self!r}")
            data.mark_invalid()
        return result

    def do_filtered_draw(self, data, filter_strategy):
        if isinstance(filter_strategy, FilteredStrategy):
            return self._transform(self.value, filter_strategy.flat_conditions)
        return self._transform(self.value)


def just(value: T) -> SearchStrategy[T]:
    """Return a strategy which only generates ``value``.

    Note: ``value`` is not copied. Be wary of using mutable values.

    If ``value`` is the result of a callable, you can use
    :func:`builds(callable) <hypothesis.strategies.builds>` instead
    of ``just(callable())`` to get a fresh value each time.

    Examples from this strategy do not shrink (because there is only one).
    """
    return JustStrategy([value])


@defines_strategy(force_reusable_values=True)
def none() -> SearchStrategy[None]:
    """Return a strategy which only generates None.

    Examples from this strategy do not shrink (because there is only
    one).
    """
    return just(None)


class Nothing(SearchStrategy):
    def calc_is_empty(self, recur):
        return True

    def do_draw(self, data):
        # This method should never be called because draw() will mark the
        # data as invalid immediately because is_empty is True.
        raise NotImplementedError("This should never happen")

    def calc_has_reusable_values(self, recur):
        return True

    def __repr__(self):
        return "nothing()"

    def map(self, f):
        return self

    def filter(self, f):
        return self

    def flatmap(self, f):
        return self


NOTHING = Nothing()


@cacheable
def nothing() -> SearchStrategy:
    """This strategy never successfully draws a value and will always reject on
    an attempt to draw.

    Examples from this strategy do not shrink (because there are none).
    """
    return NOTHING
