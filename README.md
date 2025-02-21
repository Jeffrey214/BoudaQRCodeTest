# BoudaQRCodeTest  
**Version 0.3.0-alpha**

---

## Program Description

BoudaQRCodeTest is a simple program designed for integration with physical QR Codes within the Artillery Fortress Bouda. It utilizes an HTML template enriched with various graphical elements. A Python script processes content files and injects them into the HTML environment as separate display files.

> **Note:** This is a development build where all basic functions are working, but the project is far from complete.

---

## Instructions

### 1. Create Content Files

Place your content files in the `ContentFiles` folder located at the root. Files can be either in `.txt` or `.md` format, with different formatting rules:

#### For `.txt` Files
- **Template Location:** `template/ContentFilesTemplate/txtFileTemplate.txt`
- **Content:** Use standard text.
- **Pictures:** Use the following format for pictures:  
  `<pathfromroot/./picturefile.ext|formatcode>`  
  **Supported Extensions:** `.png`, `.jpg`, `.obj`, and `.gif`  
  **Supported Format Codes:**  
  - **Size:** `|s` (Small), `|m` (Medium), `|l` (Large)  
  - **Alignment:** `|-l` (Left), `|-c` (Center), `|-r` (Right)

#### For `.md` Files
- **Template Location:** `template/ContentFilesTemplate/mdFileTemplate.md`
- **Content:** Use standard Markdown syntax (refer to the [Markdown Guide](https://www.markdownguide.org/basic-syntax/)).
- **Pictures:** Use the same picture format as `.txt` files:  
  `<pathfromroot/./picturefile.ext|formatcode>`  
  **Supported Extensions & Format Codes:** As specified above.

---

### 2. Deployment

- **Script:** `deploy.py`  
  Use this script to convert content files into HTML and inject them into the website template.  
- **Template Location:** `template/template.html`  
  The script creates `.html` files from the content files and prepares them for deployment.

---

### 3. QR Code Generation

- **Script:** `qrcode_create.py`  
  This script generates custom QR Codes for each page, currently optimized for GitHub-hosted pages.
- **Configuration:** Options can be found at the top of the `qrcode_create.py` script.

---

## Support

For support, please contact me via:
- **Discord:** `Jeffrey_214`
- **Email:** [jeffreyrdotson@gmail.com](mailto:jeffreyrdotson@gmail.com)
