import re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


# ---------------------------------------------------------------------------
# Sentence-aware text helpers
# ---------------------------------------------------------------------------

# Common abbreviations that end with a '.' but do NOT mark a sentence boundary.
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "mt",
    "vs", "etc", "e.g", "i.e", "approx", "inc", "ltd", "co", "dept",
    "a.m", "p.m", "u.s", "u.k", "u.n", "u.s.a",
}

_SENTENCE_END_RE = re.compile(r"[.!?]+[\"'\u2019\u201d)]*$")


def split_into_sentences(text):
    """Split plain text into sentences on '.', '!' or '?' boundaries.

    Defensive against things that are NOT sentence ends:
    * decimal numbers (e.g. "3.5")
    * ellipses ("...")
    * common abbreviations (e.g. "Dr.", "U.S.", "e.g.")
    """
    text = text.strip()
    if not text:
        return []

    # Protect decimal points so "3.5" is not treated as two sentences.
    text = re.sub(
        r"(\d)\.(\d)",
        lambda m: m.group(1) + "\ufdd0" + m.group(2),
        text,
    )
    # Collapse ellipses into a single token that is never treated as a
    # sentence end, restored as "..." afterwards.
    text = text.replace("...", "\u2026").replace("..", "\u2026")

    words = text.split()
    sentences = []
    buffer = []

    for i, word in enumerate(words):
        buffer.append(word)

        match = _SENTENCE_END_RE.search(word)
        if not match:
            continue

        core = word[: match.start()].strip("\"'“\u201c\u2018")
        if core.lower() in _ABBREVIATIONS:
            continue

        # A new sentence starts when the next token is capitalized, is a
        # digit, or opens with a quote character.
        if i + 1 < len(words):
            nxt = words[i + 1]
            if nxt[0].isupper() or nxt[0].isdigit() or nxt[0] in "\"'“\u201c(":
                sentences.append(" ".join(buffer))
                buffer = []

    if buffer:
        sentences.append(" ".join(buffer))

    # Restore protected characters.
    return [
        s.replace("\ufdd0", ".").replace("\u2026", "...")
        for s in sentences
    ]


def _wrap_lines(words, max_chars):
    """Greedily wrap words into lines whose length does not exceed max_chars."""
    lines = []
    current = []

    for word in words:
        test_line = " ".join(current + [word]) if current else word
        if len(test_line) <= max_chars:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]

    if current:
        lines.append(" ".join(current))

    return lines


def _rebalance_final_line(lines, max_chars):
    """Prevent a single lonely word on the final line (an orphan).

    When the last line holds only one word, the previous line's final word is
    pulled down so the last line carries two words - the standard typographic
    fix that makes line breaks look intentional instead of accidental.
    """
    if len(lines) < 2:
        return lines

    last_words = lines[-1].split()
    if len(last_words) != 1:
        return lines

    prev_words = lines[-2].split()

    if len(prev_words) >= 2:
        lines[-2] = " ".join(prev_words[:-1])
        lines[-1] = " ".join([prev_words[-1], last_words[0]])
    elif len(prev_words) == 1:
        # Both lines are single words; merge them when it still fits.
        merged = " ".join([prev_words[0], last_words[0]])
        if len(merged) <= max_chars + 10:
            lines = lines[:-1]
            lines[-1] = merged

    return lines


def format_quote_lines(text, max_chars=28):
    """Formats raw text into lines restricted by character count.

    Handles two formats:
    1. Conversations (Name: dialogue per line) - preserves each line, wraps if needed
    2. Regular quotes - splits into sentences and wraps each sentence on its own
       block, never sharing a line between sentences, with a blank line between
       sentences and anti-orphan balancing.

    Returns: (formatted_lines, is_conversation)
    """

    # Check if this is a true multi-line conversation format (Name: dialogue per line).
    # Do NOT treat single-line quote formats like "Childhood: ... / Adulthood: ..."
    # as conversations, otherwise wrapped lines repeat "Childhood:" on every line.
    lines_raw = text.strip().split('\n')
    speaker_line_pattern = re.compile(r"^[A-Z][A-Za-z .'-]{1,20}:\s+\S+")
    speaker_lines = [
        line for line in lines_raw
        if speaker_line_pattern.match(line.strip())
    ]
    is_comparison_quote = "/" in text and len(speaker_lines) <= 2
    is_conversation = len(speaker_lines) >= 2 and not is_comparison_quote
    
    if is_conversation:
        # Conversation format - check each line and wrap if too long
        formatted_lines = []
        for line in lines_raw:
            line = line.strip()
            if not line:  # Skip empty lines
                continue

            # Check if line is too long (max_chars limit)
            if len(line) <= max_chars:
                formatted_lines.append(line)
            elif ':' in line:
                # Line too long - wrap the dialogue while keeping the name prefix
                name, dialogue = line.split(':', 1)
                name = name.strip()
                dialogue = dialogue.strip()

                # Wrap dialogue leaving room for the "Name: " prefix
                budget = max_chars - len(name) - 2
                dialogue_lines = _wrap_lines(dialogue.split(), budget)
                # Never leave a single-word orphan at the end of a dialogue
                dialogue_lines = _rebalance_final_line(dialogue_lines, budget)

                formatted_lines.extend(
                    f"{name}: {piece}" for piece in dialogue_lines
                )
            else:
                # No colon found, just add as-is (shouldn't happen)
                formatted_lines.append(line)

        return formatted_lines, True
    
    # Regular quote format - respects explicit line breaks.
    # \n\n = paragraph break (blank line between), \n = simple newline (no blank line).
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    formatted_lines = []

    for p_idx, paragraph in enumerate(paragraphs):
        # Split paragraph on single \n to preserve explicit line breaks
        explicit_lines = [l.strip() for l in paragraph.split("\n") if l.strip()]
        para_lines = []

        for line in explicit_lines:
            # Wrap this line's words into character-limited lines
            line_wrap = _wrap_lines(line.split(), max_chars)
            # Anti-orphan: never let the last line hold a single word
            line_wrap = _rebalance_final_line(line_wrap, max_chars)

            para_lines.extend(line_wrap)

        formatted_lines.extend(para_lines)

        # Add blank line between paragraphs (\n\n)
        if p_idx < len(paragraphs) - 1 and formatted_lines:
            formatted_lines.append("")

    return formatted_lines, False


def _normalized_blur(mask, radius) -> np.ndarray:
    """Blur a grayscale mask, then re-scale it so its peak is 1.0.

    A plain GaussianBlur conserves brightness, so a larger radius only spreads
    the same faint tail wider — the visible glow never actually spreads. By
    normalizing each blurred layer back to full brightness and then stacking
    several of them, the glow both widens and stays clearly visible.
    """
    blurred = np.asarray(mask.filter(ImageFilter.GaussianBlur(radius=radius)), dtype=np.float32)
    peak = blurred.max()
    if peak > 0:
        blurred = blurred / peak
    return blurred

def draw_spaced_text(draw, position, text, font, fill, spacing=1):
    x, y = position

    for char in text:
        draw.text(
            (x, y),
            char,
            fill=fill,
            font=font
        )

        char_width = draw.textlength(
            char,
            font=font
        )

        x += char_width + spacing


def _spaced_text_width(draw, text, font, spacing=1):
    return sum(draw.textlength(char, font=font) for char in text) + (
        len(text) * spacing
    )


def _wrap_text_by_width(text, max_width, measure):
    """Wrap words to a pixel width, splitting unusually long tokens if needed."""
    lines = []
    current = ""

    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if measure(candidate) <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
            current = ""

        if measure(word) <= max_width:
            current = word
            continue

        piece = ""
        for char in word:
            if piece and measure(piece + char) > max_width:
                lines.append(piece)
                piece = char
            else:
                piece += char
        current = piece

    if current:
        lines.append(current)

    return lines


def _format_quote_lines_by_width(text, max_width, measure):
    """Preserve quote structure while wrapping each line to its measured width."""
    raw_lines = text.strip().split("\n")
    speaker_pattern = re.compile(r"^[A-Z][A-Za-z .'-]{1,20}:\s+\S+")
    speaker_lines = [line for line in raw_lines if speaker_pattern.match(line.strip())]
    is_comparison_quote = "/" in text and len(speaker_lines) <= 2
    is_conversation = len(speaker_lines) >= 2 and not is_comparison_quote

    if is_conversation:
        formatted_lines = []
        for raw_line in raw_lines:
            line = raw_line.strip()
            if not line:
                continue

            if ":" not in line:
                formatted_lines.extend(_wrap_text_by_width(line, max_width, measure))
                continue

            name, dialogue = line.split(":", 1)
            prefix = f"{name.strip()}: "
            current = prefix
            for word in dialogue.strip().split():
                candidate = current + word if current.endswith(" ") else f"{current} {word}"
                if measure(candidate) <= max_width:
                    current = candidate
                else:
                    if current.strip() != prefix.strip():
                        formatted_lines.append(current.rstrip())
                    current = prefix + word

                    if measure(current) > max_width:
                        wrapped = _wrap_text_by_width(
                            current, max_width, measure
                        )
                        formatted_lines.extend(wrapped[:-1])
                        current = wrapped[-1]

            if current.strip() != prefix.strip():
                formatted_lines.append(current.rstrip())

        return formatted_lines, True

    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    formatted_lines = []

    for paragraph_index, paragraph in enumerate(paragraphs):
        for explicit_line in paragraph.split("\n"):
            formatted_lines.extend(
                _wrap_text_by_width(explicit_line.strip(), max_width, measure)
            )

        if paragraph_index < len(paragraphs) - 1 and formatted_lines:
            formatted_lines.append("")

    return formatted_lines, False


def _paginate_lines(lines, lines_per_page):
    """Split overflow into pages without leaving blank lines at page edges."""
    pages = []
    remaining = list(lines)

    while remaining:
        page = remaining[:lines_per_page]
        remaining = remaining[lines_per_page:]

        while page and not page[0]:
            page.pop(0)
        while page and not page[-1]:
            page.pop()

        if page:
            pages.append(page)

    return pages


def _page_output_path(output_path, page_number):
    path = Path(output_path)
    if page_number == 1:
        return str(path)
    return str(path.with_name(f"{path.stem}_{page_number}{path.suffix}"))

def create_neon_quote_image(
    raw_text, template_path="template.jpg", output_path="image.jpg"
):
    try:
        img = Image.open(template_path).convert("RGB")
    except FileNotFoundError:
        print(f"Error: '{template_path}' not found. Check the file name/path.")
        return

    width, height = img.size

    # ============================================================
    # NEON COLORS
    # ============================================================
    # inner_bulb_color = (255, 205, 215)   # Soft pink/white text
    # core_glow_color = (255, 42, 85)    # Bright pink neon
    # ambient_glow_color = (98, 6, 27)    # Dark red/pink outer glow

    # inner_bulb_color = (255, 210, 220)
    # core_glow_color = (255, 7, 58)        # #FF073A
    # ambient_glow_color = (120, 5, 30)

    inner_bulb_color = (255, 205, 215)
    core_glow_color = (255, 0, 74)        # #FF004A
    ambient_glow_color = (100, 0, 35)

    # ============================================================
    # FONT
    # ============================================================
    BASE_DIR = Path(__file__).resolve().parent
    FONT_DIR = (
        BASE_DIR
        / "Fonts"
        / "Montserrat"
        / "static"
    )

    def load_font(size, weight="Light"):
        try:
            font_path = FONT_DIR / f"Montserrat-{weight}.ttf"
            return ImageFont.truetype(str(font_path), size)
        except Exception:
            print(f"Montserrat-{weight}.ttf not found. Falling back to default font.")
            return ImageFont.load_default()

    # ============================================================
    # ADAPTIVE LAYOUT
    # ============================================================
    logo_margin_bottom = 180
    preferred_side_margin = 80
    normal_side_margin = 32
    preferred_top_margin = 60
    font_sizes = range(36, 16, -2)
    layout = None

    measure_draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    normal_font = load_font(30, weight="Light")
    normal_measure = lambda text: _spaced_text_width(
        measure_draw, text, normal_font
    )
    normal_lines, _ = _format_quote_lines_by_width(
        raw_text,
        max(1, width - (2 * normal_side_margin)),
        normal_measure,
    )
    normal_line_spacing = max(34, round(30 * 1.5))
    normal_available_height = height - logo_margin_bottom - preferred_top_margin
    is_big_quote = (
        len(normal_lines) * normal_line_spacing > normal_available_height
    )
    font_weight = "Medium" if is_big_quote else "Light"
    side_margin = preferred_side_margin if is_big_quote else normal_side_margin

    for side_margin in (side_margin,):
        for top_margin in (preferred_top_margin, 36):
            available_height = height - logo_margin_bottom - top_margin
            max_text_width = max(1, width - (2 * side_margin))

            for candidate_size in font_sizes:
                candidate_font = load_font(candidate_size, weight=font_weight)
                candidate_line_spacing = max(
                    candidate_size + 4,
                    round(candidate_size * 1.5),
                )
                measure = lambda text, f=candidate_font: _spaced_text_width(
                    measure_draw, text, f
                )
                candidate_lines, is_conversation = _format_quote_lines_by_width(
                    raw_text, max_text_width, measure
                )

                if len(candidate_lines) * candidate_line_spacing <= available_height:
                    layout = (
                        candidate_lines,
                        is_conversation,
                        candidate_font,
                        candidate_size,
                        candidate_line_spacing,
                        side_margin,
                        top_margin,
                        available_height,
                    )
                    break

            if layout:
                break
        if layout:
            break

    if layout:
        (
            lines,
            is_conversation,
            font,
            font_size,
            line_spacing,
            side_margin,
            top_margin,
            available_height,
        ) = layout
        pages = [lines or [""]]
    else:
        # Extremely long quotes become several readable, consistently aligned
        # images instead of being clipped or reduced below a legible font size.
        side_margin = preferred_side_margin if is_big_quote else normal_side_margin
        top_margin = 36
        available_height = height - logo_margin_bottom - top_margin
        font_size = 18
        font = load_font(font_size, weight=font_weight)
        line_spacing = max(font_size + 4, round(font_size * 1.5))
        max_text_width = max(1, width - (2 * side_margin))
        measure = lambda text: _spaced_text_width(measure_draw, text, font)
        lines, is_conversation = _format_quote_lines_by_width(
            raw_text, max_text_width, measure
        )
        lines_per_page = max(1, available_height // line_spacing)
        pages = _paginate_lines(lines or [""], lines_per_page)

    saved_paths = []

    for page_number, page_lines in enumerate(pages, start=1):
        total_text_height = len(page_lines) * line_spacing
        start_y = top_margin + (available_height - total_text_height) // 2

        img = Image.open(template_path).convert("RGB")
        base_mask = Image.new("L", (width, height), 0)
        draw_mask = ImageDraw.Draw(base_mask)

        for line_index, line in enumerate(page_lines):
            if not line:
                continue

            y_pos = start_y + (line_index * line_spacing)
            text_width = _spaced_text_width(draw_mask, line, font)
            x_pos = (
                side_margin
                if is_conversation
                else (width - text_width) // 2
            )

            draw_spaced_text(
                draw_mask,
                (x_pos, y_pos),
                line,
                font,
                fill=255,
                spacing=1,
            )

        glow_stack = [
            (0.65, _normalized_blur(base_mask, 5)),
            (0.30, _normalized_blur(base_mask, 18)),
            (0.10, _normalized_blur(base_mask, 40)),
        ]

        acc = np.zeros((height, width), dtype=np.float32)
        for weight, blurred in glow_stack:
            acc += weight * blurred

        ambient_mask = Image.fromarray(
            (np.clip(acc, 0.0, 1.0) * 255).astype(np.uint8),
            mode="L",
        )
        ambient_layer = Image.new("RGB", (width, height), color=ambient_glow_color)
        core_layer = Image.new("RGB", (width, height), color=core_glow_color)
        bulb_layer = Image.new("RGB", (width, height), color=inner_bulb_color)

        img.paste(ambient_layer, (0, 0), mask=ambient_mask)
        img.paste(core_layer, (0, 0), mask=base_mask)
        img.paste(bulb_layer, (0, 0), mask=base_mask)

        page_path = _page_output_path(output_path, page_number)
        img.save(page_path)
        saved_paths.append(page_path)
        print(f"Saved as {page_path}")

    return saved_paths
   
if __name__ == "__main__":
    quote_input = "The last beats of the dhaak before,\nMaa's return feel Heavier,\nleaving our hearts a little emptier\nas we prepare to wait another whole year.\n\nThe sindoor-khela, the mishti,\nthe tearful hugs, and every\n“Bhalo theko, abar dekha hobe”.\n\nBijoya Dashami breaks our hearts a little, but we still smile, touch Maa's feet, and whisper,\n“Abar Esho, Maa!!”\nWith tears in our eyes and hope in our hearts, we raise our voices \n”Asche Bochor Abar Hobe!!”\n\nBecause that's how Bengalis say goodbye — with tears in their eyes, mishti in their hands,\nand a heart already waiting for next Pujo."

    print(quote_input)
    create_neon_quote_image(
        raw_text=quote_input,
        template_path="template.jpg",
        output_path="image.jpg",
    )