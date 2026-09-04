import re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from QuoteGeneration import generate_quote


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
    
    # Regular quote format - sentence-aware wrapping.
    # Split into sentences and wrap each sentence on its own block, with a
    # blank line between sentences so one sentence never shares a line with
    # the next one.
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    formatted_lines = []

    for p_idx, paragraph in enumerate(paragraphs):
        sentences = split_into_sentences(paragraph)
        para_lines = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Wrap this sentence's words into character-limited lines
            sentence_lines = _wrap_lines(sentence.split(), max_chars)
            # Anti-orphan: never let the last line of a sentence hold a single word
            sentence_lines = _rebalance_final_line(sentence_lines, max_chars)

            # Start every new sentence on a fresh line, separated from the
            # previous sentence by a blank line.
            if para_lines:
                para_lines.append("")

            para_lines.extend(sentence_lines)

        formatted_lines.extend(para_lines)

        # Add empty line spacing between double-spaced paragraphs
        if p_idx < len(paragraphs) - 1 and formatted_lines:
            formatted_lines.append("")

    return formatted_lines, False


def _normalized_blur(mask, radius):
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
    FONT_PATH = (
        BASE_DIR
        / "Fonts"
        / "Montserrat"
        / "static"
        / "Montserrat-Light.ttf"
    )

    def load_font(size):
        try:
            return ImageFont.truetype(str(FONT_PATH), size)
        except Exception:
            print("Montserrat-Light.ttf not found. Falling back to default font.")
            return ImageFont.load_default()

    # ============================================================
    # FORMAT TEXT
    # ============================================================
    lines, is_conversation = format_quote_lines(
        raw_text,
        max_chars=28
    )

    # ============================================================
    # AVAILABLE TEXT AREA
    # ============================================================
    logo_margin_bottom = 180
    top_margin = 120

    available_height = (
        height
        - logo_margin_bottom
        - top_margin
    )

    # ============================================================
    # FONT SIZE
    # ============================================================
    font_size = 32
    font = load_font(font_size)

    line_spacing = round(font_size * 1.8)

    total_text_height = (
        len(lines) * line_spacing
    )

    while (
        total_text_height > available_height
        and font_size > 18
    ):
        font_size -= 2

        font = load_font(font_size)

        line_spacing = round(
            font_size * 1.8
        )

        total_text_height = (
            len(lines) * line_spacing
        )

    # ============================================================
    # CENTER TEXT VERTICALLY
    # ============================================================
    start_y = (
        top_margin
        + (
            available_height
            - total_text_height
        ) // 2
    )

    # ============================================================
    # CREATE BASE TEXT MASK
    # ============================================================
    base_mask = Image.new(
        "L",
        (width, height),
        0
    )

    draw_mask = ImageDraw.Draw(
        base_mask
    )

    left_margin = 80

    for i, line in enumerate(lines):

        # Blank line between sentences
        if not line:
            continue

        y_pos = (
            start_y
            + (i * line_spacing)
        )

        text_w = draw_mask.textlength(
            line,
            font=font
        )

        if is_conversation:

            # Left aligned
            x_pos = left_margin

        else:

            # Center aligned
            x_pos = (
                width - text_w
            ) // 2

        draw_spaced_text(
            draw_mask,
            (x_pos, y_pos),
            line,
            font,
            fill=255,
            spacing=1
        )

    # ============================================================
    # NEON GLOW
    #
    # Small + soft glow.
    # The reference image has sharp text with
    # a relatively tight halo around it.
    # ============================================================

    glow_stack = [

        # Tight glow
        (0.65, _normalized_blur(
            base_mask,
            5
        )),

        # Medium soft halo
        (0.30, _normalized_blur(
            base_mask,
            18
        )),

        # Very subtle outer glow
        (0.10, _normalized_blur(
            base_mask,
            40
        )),
    ]

    # ============================================================
    # BUILD AMBIENT GLOW
    # ============================================================
    acc = np.zeros(
        (height, width),
        dtype=np.float32
    )

    for weight, blurred in glow_stack:

        acc += (
            weight
            * blurred
        )

    ambient_acc = np.clip(
        acc,
        0.0,
        1.0
    )

    ambient_mask = Image.fromarray(
        (
            ambient_acc * 255
        ).astype(np.uint8),
        mode="L"
    )

    # ============================================================
    # SHARP CORE
    #
    # IMPORTANT:
    # Do NOT blur the core.
    # This keeps the actual letters crisp.
    # ============================================================

    core_mask = base_mask

    # ============================================================
    # CREATE COLOR LAYERS
    # ============================================================
    ambient_layer = Image.new(
        "RGB",
        (width, height),
        color=ambient_glow_color
    )

    core_layer = Image.new(
        "RGB",
        (width, height),
        color=core_glow_color
    )

    bulb_layer = Image.new(
        "RGB",
        (width, height),
        color=inner_bulb_color
    )

    # ============================================================
    # APPLY GLOW
    # ============================================================
    img.paste(
        ambient_layer,
        (0, 0),
        mask=ambient_mask
    )

    img.paste(
        core_layer,
        (0, 0),
        mask=core_mask
    )

    # ============================================================
    # APPLY SHARP TEXT ON TOP
    # ============================================================
    img.paste(
        bulb_layer,
        (0, 0),
        mask=base_mask
    )

    # ============================================================
    # SAVE
    # ============================================================
    img.save(
        output_path
    )

    print(
        f"Saved as {output_path}"
    )
   
if __name__ == "__main__":
    quote_input = "It's strange how someone can mean everything to you once.\n\nAnd later become someone you wouldn't even know how to talk to."
    print(quote_input)
    create_neon_quote_image(
        raw_text=quote_input,
        template_path="template.jpg",
        output_path="image.jpg",
    )