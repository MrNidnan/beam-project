"""Pure text fitting helpers shared by the native display renderer.

All functions take measurement callbacks instead of a wx DC so the logic can
be exercised headlessly by the smoke tests:
  measure(text) -> (width, height)               measured at one fixed font size
  measure_at_size(size, text) -> (width, height) measured at an arbitrary size
"""

ELLIPSIS = '...'


def wrap_long_token(measure, token, max_width):
    if not token:
        return ['']

    wrapped_parts = []
    remaining = token
    while remaining:
        # Binary search for the longest prefix that still fits (prefix width
        # grows monotonically with its length). Always take at least one char
        # so a too-narrow box cannot loop forever.
        low, high = 1, len(remaining)
        split_index = 0
        while low <= high:
            mid = (low + high) // 2
            candidate_width, _ = measure(remaining[:mid])
            if candidate_width <= max_width:
                split_index = mid
                low = mid + 1
            else:
                high = mid - 1
        if split_index <= 0:
            split_index = 1

        wrapped_parts.append(remaining[:split_index])
        remaining = remaining[split_index:]

    return wrapped_parts


def wrap_text_lines(measure, text, max_width):
    if max_width <= 0:
        return [text]

    wrapped_lines = []
    for paragraph in str(text).splitlines() or ['']:
        words = paragraph.split()
        if not words:
            wrapped_lines.append('')
            continue

        current_line = ''
        for word in words:
            candidate = word if not current_line else current_line + ' ' + word
            candidate_width, _ = measure(candidate)
            if candidate_width <= max_width:
                current_line = candidate
                continue

            if current_line:
                wrapped_lines.append(current_line)
                current_line = ''

            word_width, _ = measure(word)
            if word_width <= max_width:
                current_line = word
                continue

            wrapped_word_parts = wrap_long_token(measure, word, max_width)
            wrapped_lines.extend(wrapped_word_parts[:-1])
            current_line = wrapped_word_parts[-1]

        if current_line or not wrapped_lines:
            wrapped_lines.append(current_line)

    return wrapped_lines or ['']


def ellipsize_line(measure, text, max_width):
    text_width, _ = measure(text)
    if text_width <= max_width:
        return text

    while text and text_width > max_width:
        text = text[:-1]
        text_width, _ = measure(text + ELLIPSIS)

    return text + ELLIPSIS


def next_size_step(size, min_size):
    return max(min_size, size - max(1, int(round(size * 0.08))))


def fit_text(measure_at_size, text, max_width, base_size, min_size,
             max_lines=0, single_line=False):
    """Fit text into a box, shrinking the font before ellipsizing.

    Returns {'lines': [str], 'size': int, 'ellipsized': bool}.
    """
    min_size = max(1, min(min_size, base_size))
    size = base_size

    while True:
        measure = lambda t, s=size: measure_at_size(s, t)

        if single_line:
            text_width, _ = measure(text)
            if text_width <= max_width:
                return {'lines': [text], 'size': size, 'ellipsized': False}
        else:
            lines = wrap_text_lines(measure, text, max_width)
            if max_lines <= 0 or len(lines) <= max_lines:
                return {'lines': lines, 'size': size, 'ellipsized': False}

        if size <= min_size:
            break
        size = next_size_step(size, min_size)

    # Last resort at min size: ellipsize.
    measure = lambda t, s=min_size: measure_at_size(s, t)

    if single_line:
        return {
            'lines': [ellipsize_line(measure, text, max_width)],
            'size': min_size,
            'ellipsized': True,
        }

    lines = wrap_text_lines(measure, text, max_width)
    keep = max(1, max_lines)
    last_line = ' '.join(line for line in lines[keep - 1:] if line)
    kept_lines = lines[:keep - 1] + [ellipsize_line(measure, last_line, max_width)]
    return {'lines': kept_lines, 'size': min_size, 'ellipsized': True}


def compute_row_offsets(sorted_layouts):
    """Cumulative vertical offsets replicating the display reflow rules.

    Items sharing the same vertical Position row reserve the tallest extra
    height in that row; later rows are pushed down by the accumulated total.
    """
    offsets = []
    cumulative_vertical_offset = 0
    current_row_position = None
    current_row_extra_height = 0

    for layout in sorted_layouts:
        row_position = layout['settings']['Position'][0]
        if current_row_position is None:
            current_row_position = row_position
        elif row_position > current_row_position:
            cumulative_vertical_offset += current_row_extra_height
            current_row_extra_height = 0
            current_row_position = row_position

        offsets.append(cumulative_vertical_offset)
        current_row_extra_height = max(current_row_extra_height, layout['extra_height'])

    return offsets


def block_overflow_px(sorted_layouts, safe_bottom):
    """How far the lowest visible item extends past the vertical safe area."""
    offsets = compute_row_offsets(sorted_layouts)
    worst = 0
    for layout, offset in zip(sorted_layouts, offsets):
        if not any(line.strip() for line in layout['text_lines']):
            continue
        bottom = layout['top_px'] + offset + layout['total_height']
        worst = max(worst, bottom - safe_bottom)
    return worst
