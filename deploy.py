import os
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# Folder paths
TEMPLATE_FOLDER = "template"
CONTENT_FOLDER = "ContentFiles"
DEPLOY_FOLDER = "DeploymentFiles"

# Manifest file named "manifest.txt"
MANIFEST_FILE = os.path.join(DEPLOY_FOLDER, "manifest.txt")

# Template file path
TEMPLATE_FILE = os.path.join(TEMPLATE_FOLDER, "template.html")

def strip_quotes(s):
    return s.strip('"')

def js_escape(s):
    # Escape any single quotes inside the string for safe JS single-quote usage.
    return s.replace("'", "\\'")

class ProcessorUI:
    def __init__(self, master):
        self.master = master
        master.title("Deployment Processor")

        self.progress_label = tk.Label(master, text="Progress:")
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(master, orient=tk.HORIZONTAL, length=400, mode="determinate")
        self.progress_bar.pack(pady=5)

        self.error_label = tk.Label(master, text="Errors:")
        self.error_label.pack(pady=5)

        self.error_text = scrolledtext.ScrolledText(master, width=60, height=10)
        self.error_text.pack(pady=5)

        self.start_button = tk.Button(master, text="Start Processing", command=self.process_files)
        self.start_button.pack(pady=10)

        self.status_label = tk.Label(master, text="")
        self.status_label.pack(pady=5)

        self.errors = []

    def log_error(self, message):
        self.errors.append(message)
        self.error_text.insert(tk.END, message + "\n")
        self.error_text.see(tk.END)

    def process_files(self):
        """
        1) For each .txt file in ContentFiles, capture the three sections:
           Header, Title, and Content. Each section is expected to contain four lines,
           one for each language (cs, en, de, pl) in the format:
           
             cs: "Some text"
             
           and may include image placeholders of the form <PictureDeps/...>.
        2) If any section is missing a language line, abort processing.
        3) For each valid file:
           - Replace the <title>, <div id="header-title">, and <p id="content-text">
             in the template with the Czech (cs) version.
           - Replace the JavaScript objects for titles and contents with all four languages.
           - Replace any image placeholder (e.g. <PictureDeps/Content/Article1/testimage.png>)
             with an <img> tag that prepends "../" (so the image is loaded from root) and
             includes an onerror handler to remove it if it fails to load.
        4) Write the output HTML files to DeploymentFiles and produce a manifest.txt.
        """
        self.start_button.config(state=tk.DISABLED)
        self.error_text.delete("1.0", tk.END)
        self.errors.clear()
        self.status_label.config(text="Starting processing...")
        self.master.update_idletasks()

        # Ensure folders exist
        for folder in [TEMPLATE_FOLDER, CONTENT_FOLDER, DEPLOY_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)

        # Load template
        try:
            with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
                template_content = f.read()
        except Exception as e:
            self.log_error("Error reading template file: " + str(e))
            messagebox.showerror("Error", "Cannot read template file.")
            self.start_button.config(state=tk.NORMAL)
            return

        # List .txt files in ContentFiles
        raw_files = [f for f in os.listdir(CONTENT_FOLDER) if f.lower().endswith(".txt")]
        if not raw_files:
            self.log_error("No .txt files found in ContentFiles.")
            self.start_button.config(state=tk.NORMAL)
            return

        # Sort files by numeric prefix (e.g., "1.Uvod.txt", "2.Svaznice.txt", etc.)
        def sort_key(filename):
            match = re.match(r"(\d+)\.", filename)
            return int(match.group(1)) if match else 9999
        raw_files.sort(key=sort_key)
        self.progress_bar["maximum"] = len(raw_files)

        # Pattern to capture an entire section block:
        section_block_pattern = re.compile(
            r'^(Header|Title|Content):\s*(.*?)(?=^(?:Header|Title|Content):|\Z)', 
            re.MULTILINE | re.DOTALL
        )
        # Pattern for a language line (e.g., cs: "Text")
        lang_line_pattern = re.compile(r'^\s*(cs|en|de|pl)\s*:\s*(".*?")\s*$', re.MULTILINE)
        # Pattern for image placeholders
        image_pattern = re.compile(r'<(PictureDeps/[^>]+)>', re.IGNORECASE)

        parsed_data = {}
        any_error = False

        # Process each .txt file
        for idx, raw_filename in enumerate(raw_files, start=1):
            self.status_label.config(text=f"Checking {raw_filename} ({idx} of {len(raw_files)})")
            self.master.update_idletasks()
            raw_path = os.path.join(CONTENT_FOLDER, raw_filename)
            try:
                with open(raw_path, "r", encoding="utf-8") as rf:
                    raw_data = rf.read()
            except Exception as e:
                self.log_error(f"Error reading {raw_filename}: {e}")
                any_error = True
                break

            # Initialize a dictionary for the three sections.
            data_dict = {
                "header": {"cs": None, "en": None, "de": None, "pl": None},
                "title":  {"cs": None, "en": None, "de": None, "pl": None},
                "content": {"cs": None, "en": None, "de": None, "pl": None},
                "images": []  # Collect all image placeholders from all sections.
            }

            # Find all section blocks.
            sections = section_block_pattern.findall(raw_data)
            for sec_name, sec_content in sections:
                sec_key = sec_name.lower()
                # Extract language lines for this section.
                matches = lang_line_pattern.findall(sec_content)
                for lang, text in matches:
                    lang = lang.lower()
                    data_dict[sec_key][lang] = text  # text includes quotes
                # Check for image placeholders.
                for img_match in image_pattern.findall(sec_content):
                    data_dict["images"].append(img_match)

            # Verify every section has all four languages.
            missing = []
            for sec in ["header", "title", "content"]:
                for lang in ["cs", "en", "de", "pl"]:
                    if data_dict[sec][lang] is None:
                        missing.append(f"{sec}.{lang}")
            if missing:
                self.log_error(f"{raw_filename} is missing lines: {', '.join(missing)}.")
                any_error = True
                break

            parsed_data[raw_filename] = data_dict
            self.progress_bar["value"] = idx
            self.master.update_idletasks()

        if any_error:
            self.status_label.config(text="Error encountered. No files generated.")
            messagebox.showwarning("Deployment Aborted", "One or more files were invalid. No HTML files have been generated.")
            self.start_button.config(state=tk.NORMAL)
            return

        self.status_label.config(text="All files valid. Generating HTML...")
        self.master.update_idletasks()

        # Patterns for replacing template placeholders.
        title_re   = re.compile(r'(<title>)(.*?)(</title>)', re.DOTALL | re.IGNORECASE)
        header_re  = re.compile(r'(<div\s+[^>]*id=["\']header-title["\'][^>]*>)(.*?)(</div>)', re.DOTALL)
        content_re = re.compile(r'(<p\s+[^>]*id=["\']content-text["\'][^>]*>)(.*?)(</p>)', re.DOTALL)
        js_titles_re   = re.compile(r'const\s+titles\s*=\s*\{[^}]*\};', re.DOTALL)
        js_contents_re = re.compile(r'const\s+contents\s*=\s*\{[^}]*\};', re.DOTALL)

        manifest_lines = []
        self.progress_bar["value"] = 0

        # Process each configuration file and generate HTML.
        for idx, raw_filename in enumerate(raw_files, start=1):
            self.status_label.config(text=f"Generating for {raw_filename} ({idx} of {len(raw_files)})")
            self.master.update_idletasks()

            data_dict = parsed_data[raw_filename]
            mod_content = template_content

            # Use the Czech (cs) version for fixed positions.
            cs_title = strip_quotes(data_dict["title"]["cs"])
            cs_header = strip_quotes(data_dict["header"]["cs"])
            cs_content = strip_quotes(data_dict["content"]["cs"])

            mod_content = title_re.sub(lambda m: m.group(1) + cs_title + m.group(3), mod_content)
            mod_content = header_re.sub(lambda m: m.group(1) + cs_header + m.group(3), mod_content)
            mod_content = content_re.sub(lambda m: m.group(1) + cs_content + m.group(3), mod_content)

            # Build new JavaScript objects for all languages.
            h_cs = js_escape(strip_quotes(data_dict["header"]["cs"]))
            h_en = js_escape(strip_quotes(data_dict["header"]["en"]))
            h_de = js_escape(strip_quotes(data_dict["header"]["de"]))
            h_pl = js_escape(strip_quotes(data_dict["header"]["pl"]))
            new_titles_js = (
                f"const titles = {{'cs': '{h_cs}', 'en': '{h_en}', 'de': '{h_de}', 'pl': '{h_pl}'}};"
            )
            c_cs = js_escape(strip_quotes(data_dict["content"]["cs"]))
            c_en = js_escape(strip_quotes(data_dict["content"]["en"]))
            c_de = js_escape(strip_quotes(data_dict["content"]["de"]))
            c_pl = js_escape(strip_quotes(data_dict["content"]["pl"]))
            new_contents_js = (
                f"const contents = {{'cs': '{c_cs}', 'en': '{c_en}', 'de': '{c_de}', 'pl': '{c_pl}'}};"
            )
            mod_content = js_titles_re.sub(new_titles_js, mod_content)
            mod_content = js_contents_re.sub(new_contents_js, mod_content)

            # Replace image placeholders.
            for img_path in data_dict["images"]:
                placeholder = f"<{img_path}>"
                adjusted_path = f"../{img_path}"
                img_tag = f'<img src="{adjusted_path}" class="content-image" onerror="this.remove()" />'
                mod_content = mod_content.replace(placeholder, img_tag)

            # Determine output file name.
            base_name = os.path.splitext(raw_filename)[0]
            output_filename = base_name + ".html"
            output_path = os.path.join(DEPLOY_FOLDER, output_filename)
            try:
                with open(output_path, "w", encoding="utf-8") as outf:
                    outf.write(mod_content)
            except Exception as e:
                self.log_error(f"Error writing {output_filename}: {e}")
                any_error = True
                break

            # Extract numeric order from filename for manifest.
            order_match = re.match(r"(\d+)\.", raw_filename)
            order_str = order_match.group(1) if order_match else str(idx)
            manifest_lines.append(f"{order_str}. {output_filename}")
            self.progress_bar["value"] = idx
            self.master.update_idletasks()

        if any_error:
            self.status_label.config(text="Error encountered while writing files. No manifest created.")
            messagebox.showwarning("Deployment Aborted", "Error while writing files. Partial files may exist, but no manifest was created.")
            self.start_button.config(state=tk.NORMAL)
            return

        # Write the manifest file.
        try:
            with open(MANIFEST_FILE, "w", encoding="utf-8") as mf:
                mf.write("#Manifest\n")
                mf.write("\n".join(manifest_lines))
        except Exception as e:
            self.log_error(f"Error writing manifest.txt: {e}")
            self.status_label.config(text="Error encountered. Manifest not created.")
            messagebox.showwarning("Deployment Partial", "All HTML files were generated, but manifest.txt could not be written.")
            self.start_button.config(state=tk.NORMAL)
            return

        self.status_label.config(text="Processing complete.")
        messagebox.showinfo("Done", "Processing complete. All files have been generated.")
        self.start_button.config(state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = ProcessorUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
