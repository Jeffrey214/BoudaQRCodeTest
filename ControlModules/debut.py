import markdown
from content_parser import parse_md_file

# Parse the markdown file.
data = parse_md_file("ContentFiles/1.Uvod.md")
cs_content = data["content"]["cs"]

# Write a simple HTML file with the extracted content.
html_output = f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <title>Debut Content</title>
</head>
<body>
  {cs_content}
</body>
</html>"""

with open("debut.html", "w", encoding="utf-8") as f:
    f.write(html_output)
