import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from QuoteGeneration import generate_quote

def format_quote_lines(text, max_chars=28):
    """Formats raw text into lines restricted by character count.
    
    Handles two formats:
    1. Conversations (Name: dialogue format) - preserves each line, wraps if needed
    2. Regular quotes - wraps text with anti-orphan logic
    
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
            else:
                # Line too long - need to wrap dialogue text
                # Split at colon to get name and dialogue
                if ':' in line:
                    name, dialogue = line.split(':', 1)
                    dialogue = dialogue.strip()
                    
                    # Wrap dialogue text into multiple lines
                    words = dialogue.split()
                    current_words = []
                    
                    for word in words:
                        # Test if adding this word exceeds limit
                        test_line = f"{name}: {' '.join(current_words + [word])}"
                        
                        if len(test_line) <= max_chars:
                            current_words.append(word)
                        else:
                            # Current line full, save it
                            if current_words:
                                formatted_lines.append(f"{name}: {' '.join(current_words)}")
                            current_words = [word]
                    
                    # Add remaining words
                    if current_words:
                        formatted_lines.append(f"{name}: {' '.join(current_words)}")
                else:
                    # No colon found, just add as-is (shouldn't happen)
                    formatted_lines.append(line)
        
        return formatted_lines, True
    
    # Regular quote format - existing logic
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    formatted_lines = []

    for p_idx, paragraph in enumerate(paragraphs):
        words = " ".join(paragraph.split()).split()
        current_line = []
        para_lines = []

        for word in words:
            # Check length if we were to add this word (plus a space if current_line isn't empty)
            test_line = (
                " ".join(current_line + [word]) if current_line else word
            )

            if len(test_line) <= max_chars:
                current_line.append(word)
            else:
                # Line full, store current line and start a new one
                if current_line:
                    para_lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            para_lines.append(" ".join(current_line))

        # --- Anti-Orphan Check ---
        # If the last line contains only 1 word, re-balance with the line before it
        if len(para_lines) > 1 and len(para_lines[-1].split()) == 1:
            last_word = para_lines.pop()
            prev_words = para_lines.pop().split()

            # Move one word down from the previous line to pair with the orphan
            new_last_line = f"{prev_words[-1]} {last_word}"
            new_prev_line = " ".join(prev_words[:-1])

            if new_prev_line:
                para_lines.append(new_prev_line)
            para_lines.append(new_last_line)

        formatted_lines.extend(para_lines)

        # Add empty line spacing between double-spaced paragraphs
        if p_idx < len(paragraphs) - 1:
            formatted_lines.append("")

    return formatted_lines, False


def create_neon_quote_image(
    raw_text, template_path="template.jpg", output_path="image.jpg"
):
    try:
        img = Image.open(template_path).convert("RGB")
    except FileNotFoundError:
        print(f"Error: '{template_path}' not found. Check the file name/path.")
        return

    width, height = img.size

    inner_bulb_color = (255, 220, 236)  # #FFDCEC
    core_glow_color = (255, 32, 117)  # #FF2075
    ambient_glow_color = (97, 11, 45)  # #610B2D

    # Set up font path
    BASE_DIR = Path(__file__).resolve().parent
    FONT_PATH = BASE_DIR / "Fonts" / "Montserrat" / "static" / "Montserrat-Light.ttf"
    
    try:
        font = ImageFont.truetype(str(FONT_PATH), 32)
    except Exception:
        print("Montserrat-Light.ttf not found. Falling back to default font.")
        font = ImageFont.load_default()

    # Format lines - returns (lines, is_conversation)
    lines, is_conversation = format_quote_lines(raw_text, max_chars=28)
    line_spacing = 58

    # Calculate available space (leave room for logo at bottom)
    # Logo area: reserve 180px from bottom
    logo_margin_bottom = 180
    # Also add top margin for breathing room
    top_margin = 120
    
    available_height = height - logo_margin_bottom - top_margin
    
    total_text_height = len(lines) * line_spacing
    
    # If text is too tall, reduce font size for conversations
    if total_text_height > available_height:
        if is_conversation or len(lines) > 6:
            # Reduce font size for long conversations
            try:
                font = ImageFont.truetype(str(FONT_PATH), 28)
            except:
                font = ImageFont.load_default()
            line_spacing = 50
            total_text_height = len(lines) * line_spacing
            
            # If still too tall, reduce further
            if total_text_height > available_height:
                try:
                    font = ImageFont.truetype(str(FONT_PATH), 24)
                except:
                    font = ImageFont.load_default()
                line_spacing = 44
                total_text_height = len(lines) * line_spacing
        else:
            # For regular quotes, this shouldn't happen, but handle it
            line_spacing = 50
            total_text_height = len(lines) * line_spacing
    
    # Center text in available space (between top margin and logo)
    start_y = top_margin + (available_height - total_text_height) // 2

    base_mask = Image.new("L", (width, height), 0)
    draw_mask = ImageDraw.Draw(base_mask)

    # Set left margin for conversations (left-aligned with padding)
    left_margin = 80  # px from left edge for conversations

    for i, line in enumerate(lines):
        y_pos = start_y + (i * line_spacing)
        text_w = draw_mask.textlength(line, font=font)
        
        if is_conversation:
            # Left-aligned for conversations (like chat messages)
            x_pos = left_margin
        else:
            # Center-aligned for regular quotes
            x_pos = (width - text_w) // 2
        
        draw_mask.text((x_pos, y_pos), line, fill=255, font=font)

    ambient_mask = base_mask.filter(ImageFilter.GaussianBlur(radius=20))
    core_mask = base_mask.filter(ImageFilter.GaussianBlur(radius=5))

    ambient_layer = Image.new("RGB", (width, height), color=ambient_glow_color)
    core_layer = Image.new("RGB", (width, height), color=core_glow_color)
    bulb_layer = Image.new("RGB", (width, height), color=inner_bulb_color)

    img.paste(ambient_layer, (0, 0), mask=ambient_mask)
    img.paste(core_layer, (0, 0), mask=core_mask)
    img.paste(bulb_layer, (0, 0), mask=base_mask)

    img.save(output_path)
    print(f"Saved as {output_path}")

   
if __name__ == "__main__":
    quote_input = generate_quote()
    print(quote_input)
    create_neon_quote_image(
        raw_text=quote_input,
        template_path="template.jpg",
        output_path="image.jpg",
    )