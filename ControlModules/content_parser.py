import re
import os
import markdown

def parse_txt_file(filepath):
    """
    Parse a plain text file with the following structure:
    
    Header:
        cs: "Header text in Czech"
        en: "Header text in English"
        de: "Header text in German"
        pl: "Header text in Polish"

    Title:
        cs: "Title text in Czech"
        ...

    Content:
        cs: "<PictureDeps/path/to/image.png|mr> Content text in Czech..."
        ...
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    data = {
        "header": {"cs": None, "en": None, "de": None, "pl": None},
        "title":  {"cs": None, "en": None, "de": None, "pl": None},
        "content": {"cs": None, "en": None, "de": None, "pl": None},
        "images": []  # Each entry is a tuple: (img_path, code)
    }
    section_block_pattern = re.compile(
        r'^(Header|Title|Content):\s*(.*?)(?=^(?:Header|Title|Content):|\Z)',
        re.MULTILINE | re.DOTALL
    )
    lang_line_pattern = re.compile(r'^\s*(cs|en|de|pl)\s*:\s*(".*?")\s*$', re.MULTILINE)
    image_pattern = re.compile(r'<(PictureDeps/[^>|]+)(?:\|([sml][crl]|w))?>', re.IGNORECASE)
    
    for sec_name, sec_content in section_block_pattern.findall(content):
        key = sec_name.lower()
        for lang, text in lang_line_pattern.findall(sec_content):
            data[key][lang.lower()] = text  # Retain quotes for later processing.
        for match in image_pattern.findall(sec_content):
            data["images"].append(match)
    return data

def parse_md_file(filepath):
    """
    Parse a Markdown file with sections structured as follows:

    # Header

    **cs:**  
    <img src="../PictureDeps/Content/Article1/testimage.png|sl" alt="Test Image" />  
    Header text in Czech...

    **en:** Header text in English  
    **de:** Header text in German  
    **pl:** Header text in Polish  

    # Title

    **cs:** 1Title in Czech  
    **en:** 1Title in English  
    **de:** 1Title in German  
    **pl:** 1Title in Polish  

    # Content

    **cs:**  
    # Vítejte na prohlídce
    ## Úvod
    Text with *italic*, **bold**, and `inline code`.

    - Unordered list item
    - Another item

    1. First ordered item
    2. Second ordered item

    > A blockquote.

    <PictureDeps/Content/Article1/testimage.png|s>
    <PictureDeps/Content/Article1/testimage.png|mc>

    **en:**  
    # Welcome to the Tour
    ...
    
    (and similarly for de, pl)
    """
    import re
    import os
    import markdown

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Preprocess: Replace any <img> tag with a src containing a pipe into a simpler placeholder.
    def img_repl(m):
        src = m.group(1)
        # Remove any leading "../" from the src.
        src = re.sub(r'^\.\.\/', '', src)
        code = m.group(2) or ""
        if code:
            return f"<{src}|{code}>"
        else:
            return f"<{src}>"

    content = re.sub(
        r'<img\s+[^>]*src="([^"]*PictureDeps\/[^"|]+)(?:\|([sml][crl]|w))?"[^>]*>',
        img_repl,
        content,
        flags=re.IGNORECASE
    )

    data = {
        "header": {"cs": None, "en": None, "de": None, "pl": None},
        "title":  {"cs": None, "en": None, "de": None, "pl": None},
        "content": {"cs": None, "en": None, "de": None, "pl": None},
        "images": []
    }
    # Updated section pattern: require a newline after the section header.
    section_pattern = re.compile(
        r'^#\s*(Header|Title|Content)\s*(?:\r?\n)([\s\S]*?)(?=^\s*#\s*(?:Header|Title|Content)\s*(?:\r?\n)|\Z)',
        re.MULTILINE
    )
    # Updated language block pattern: allow optional whitespace before the "**" marker.
    lang_block_pattern = re.compile(
        r'^\s*\*\*(cs|en|de|pl):\*\*\s*([\s\S]*?)(?=^\s*\*\*(?:cs|en|de|pl):\*\*|\Z)',
        re.MULTILINE
    )

    image_pattern = re.compile(r'<(PictureDeps/[^>|]+)(?:\|([sml][crl]|w))?>', re.IGNORECASE)

    sections_found = section_pattern.findall(content)
    for sec_name, sec_text in sections_found:
        key = sec_name.lower()
        blocks = lang_block_pattern.findall(sec_text)
        for lang, text_block in blocks:
            text_block = text_block.strip()
            # Convert Markdown text to HTML.
            html_text = markdown.markdown(text_block)
            # Extract any image placeholders from the raw text.
            for match in image_pattern.findall(text_block):
                data["images"].append(match)
            data[key][lang.lower()] = html_text
    return data



def parse_content_file(filepath):
    """
    Determine the file type (.md or .txt) and parse accordingly.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".md":
        return parse_md_file(filepath)
    else:
        return parse_txt_file(filepath)
