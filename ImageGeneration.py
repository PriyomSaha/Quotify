from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from QuoteGeneration import generate_quote

def format_quote_lines(text, max_chars=28):
    """Formats raw text into lines restricted by character count.
    
    Handles two formats:
    1. Conversations (Name: dialogue format) - preserves each line as-is
    2. Regular quotes - wraps text with anti-orphan logic
    
    Returns: (formatted_lines, is_conversation)
    """
    
    # Check if this is a conversation format (has "Name: text" pattern)
    lines_raw = text.strip().split('\n')
    is_conversation = any(':' in line and len(line.split(':', 1)) == 2 for line in lines_raw if line.strip())
    
    if is_conversation:
        # Conversation format - preserve each line exactly as-is
        formatted_lines = []
        for line in lines_raw:
            line = line.strip()
            if line:  # Skip empty lines
                # Each conversation line stays on its own line
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

    try:
        BASE_DIR = Path(__file__).resolve().parent
        FONT_PATH = BASE_DIR / "Montserrat" / "static" / "Montserrat-Light.ttf"
        font = ImageFont.truetype(str(FONT_PATH), 32)
    except Exception:
        print("Montserrat-Light.ttf not found. Falling back to default font.")
        font = ImageFont.load_default()

    # Format lines - returns (lines, is_conversation)
    lines, is_conversation = format_quote_lines(raw_text, max_chars=28)
    line_spacing = 58

    # Calculate available space (leave room for logo at bottom)
    # Assume logo is at bottom 150px, leave 200px margin from bottom
    logo_margin_bottom = 200
    available_height = height - logo_margin_bottom
    
    total_text_height = len(lines) * line_spacing
    
    # If text is too tall, reduce font size for conversations
    if total_text_height > available_height:
        if is_conversation or len(lines) > 6:
            # Reduce font size for long conversations
            font = ImageFont.truetype(str(FONT_PATH), 28)
            line_spacing = 52
            total_text_height = len(lines) * line_spacing
            
            # If still too tall, reduce further
            if total_text_height > available_height:
                font = ImageFont.truetype(str(FONT_PATH), 24)
                line_spacing = 46
                total_text_height = len(lines) * line_spacing
        else:
            # For regular quotes, this shouldn't happen, but handle it
            line_spacing = 50
            total_text_height = len(lines) * line_spacing
    
    # Center text in available space (above logo)
    start_y = (available_height - total_text_height) // 2
    
    # Ensure minimum top margin
    min_top_margin = 100
    if start_y < min_top_margin:
        start_y = min_top_margin

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