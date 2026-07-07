#!/usr/bin/env python
"""Smoke test for bin/textfit.py - headless text fitting logic.

Uses a fake measurer (width = len(text) * size * 0.6) so no wx is needed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bin import textfit


CHAR_FACTOR = 0.6


def make_measure(size):
    def measure(text):
        return (len(text) * size * CHAR_FACTOR, size)
    return measure


def measure_at_size(size, text):
    return make_measure(size)(text)


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print('ok - {0}'.format(message))


def test_wrap_parity():
    # Short text stays on one line, long text wraps by words.
    measure = make_measure(10)
    lines = textfit.wrap_text_lines(measure, 'short', 1000)
    check(lines == ['short'], 'wrap keeps short text on one line')

    lines = textfit.wrap_text_lines(measure, 'alpha beta gamma delta', 80)
    check(len(lines) > 1, 'wrap splits long text into multiple lines')
    check(' '.join(lines).split() == ['alpha', 'beta', 'gamma', 'delta'],
          'wrap preserves all words in order')

    # Unbreakable token is hard-split instead of overflowing.
    lines = textfit.wrap_text_lines(measure, 'x' * 100, 60)
    check(all(make_measure(10)(line)[0] <= 60 for line in lines),
          'long token hard-split lines all fit')


def test_fit_no_shrink_when_it_fits():
    fitted = textfit.fit_text(measure_at_size, 'hello', 10000, 20, 10,
                              single_line=True)
    check(fitted['size'] == 20 and not fitted['ellipsized'],
          'text that fits keeps its configured size')


def test_fit_shrinks_before_ellipsizing():
    text = 'a' * 50  # width at size 20: 600
    fitted = textfit.fit_text(measure_at_size, text, 400, 20, 15,
                              single_line=True)
    check(fitted['size'] < 20, 'overflowing text shrinks')
    check(fitted['size'] >= 15, 'shrink never goes below min size')
    if fitted['ellipsized']:
        check(fitted['lines'][0].endswith(textfit.ELLIPSIS),
              'ellipsized line ends with ellipsis')
    # Width 400 at size 15 fits 44 chars -> still too long, must ellipsize.
    fitted = textfit.fit_text(measure_at_size, text, 300, 20, 15,
                              single_line=True)
    check(fitted['ellipsized'] and fitted['size'] == 15,
          'still-too-long text ellipsizes at min size')
    check(make_measure(15)(fitted['lines'][0])[0] <= 300,
          'ellipsized line fits the box')


def test_fit_never_grows():
    fitted = textfit.fit_text(measure_at_size, 'hi', 10000, 12, 9,
                              single_line=True)
    check(fitted['size'] == 12, 'font size never grows above configured size')


def test_max_lines_with_last_line_ellipsis():
    text = ' '.join(['word'] * 30)
    fitted = textfit.fit_text(measure_at_size, text, 200, 20, 18, max_lines=2)
    check(len(fitted['lines']) <= 2, 'wrapped text respects max lines')
    if fitted['ellipsized']:
        check(fitted['lines'][-1].endswith(textfit.ELLIPSIS),
              'last kept line is ellipsized')


def test_row_offsets_and_overflow():
    def layout(top, extra, total, position, lines=('x',)):
        return {
            'settings': {'Position': [position, 50]},
            'text_lines': list(lines),
            'top_px': top,
            'extra_height': extra,
            'total_height': total,
        }

    layouts = [
        layout(100, 40, 60, 10),
        layout(200, 0, 20, 20),
        layout(300, 0, 20, 30),
    ]
    offsets = textfit.compute_row_offsets(layouts)
    check(offsets == [0, 40, 40],
          'later rows are pushed down by earlier extra height')

    check(textfit.block_overflow_px(layouts, 400) == 0,
          'no overflow reported inside the safe area')
    check(textfit.block_overflow_px(layouts, 320) == 40,
          'overflow reports how far the block extends past the safe area')

    # Empty rows are ignored for overflow purposes.
    layouts.append(layout(900, 0, 50, 90, lines=('',)))
    check(textfit.block_overflow_px(layouts, 400) == 0,
          'empty rows do not count as overflow')


def main():
    test_wrap_parity()
    test_fit_no_shrink_when_it_fits()
    test_fit_shrinks_before_ellipsizing()
    test_fit_never_grows()
    test_max_lines_with_last_line_ellipsis()
    test_row_offsets_and_overflow()
    print('smoke_text_fitting: all checks passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
