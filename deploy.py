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

# Template file
TEMPLATE_FILE = os.path.join(TEMPLATE_FOLDER, "template.html")

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
        1) Parse each .txt in ContentFiles to extract four languages (cs, en, de, pl)
           for each section: Header, Title, Content.
        2) If any file is missing any language line, abort everything (no HTML or manifest).
        3) For each valid file:
           - Insert the "cs" versions into <title>, <div id="header-title">, <p id="content-text">.
           - Insert all four languages for the 'header' into the JS object "titles"
             and all four for the 'content' into the JS object "contents".
        4) Write the output .html files to DeploymentFiles and a manifest.txt in numeric order.
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
            self.log_error(f"Error reading template file: {e}")
            messagebox.showerror("Error", "Cannot read template file.")
            self.start_button.config(state=tk.NORMAL)
            return

        # List of .txt files
        raw_files = [f for f in os.listdir(CONTENT_FOLDER) if f.lower().endswith(".txt")]
        if not raw_files:
            self.log_error("No .txt files found in ContentFiles.")
            self.start_button.config(state=tk.NORMAL)
            return

        # Sort by numeric prefix
        def sort_key(filename):
            match = re.match(r"(\d+)\.", filename)
            return int(match.group(1)) if match else 9999
        raw_files.sort(key=sort_key)

        # Regex to capture each language line in each section
        section_pattern = re.compile(
            r'(Header|Title|Content)\s*:\s*(?:.*?\n){0,4}',  # up to 4 lines, non-greedy
            re.IGNORECASE
        )
        line_pattern = re.compile(r'^\s*(cs|en|de|pl)\s*:\s*(".*?")\s*$', re.MULTILINE)

        # UPDATED: Pattern for image placeholders like <PictureDeps/Content/Article1/testimage.png>
        image_pattern = re.compile(r'<(PictureDeps/[^>]+)>', re.IGNORECASE)

        parsed_data = {}
        any_error = False
        total_files = len(raw_files)
        self.progress_bar["maximum"] = total_files

        for idx, raw_filename in enumerate(raw_files, start=1):
            self.status_label.config(text=f"Checking {raw_filename} ({idx} of {total_files})")
            self.master.update_idletasks()

            raw_path = os.path.join(CONTENT_FOLDER, raw_filename)
            try:
                with open(raw_path, "r", encoding="utf-8") as rf:
                    raw_data = rf.read()
            except Exception as e:
                self.log_error(f"Error reading {raw_filename}: {e}")
                any_error = True
                break

            data_dict = {
                "header": {"cs": None, "en": None, "de": None, "pl": None},
                "title":  {"cs": None, "en": None, "de": None, "pl": None},
                "content":{"cs": None, "en": None, "de": None, "pl": None},
                "images": []
            }

            for section_match in section_pattern.finditer(raw_data):
                section_name = section_match.group(1).lower()
                block_start = section_match.start()
                block_end = section_match.end()

                next_block = section_pattern.search(raw_data, block_end)
                this_block_end = next_block.start() if next_block else len(raw_data)

                block_text = raw_data[block_start:this_block_end]

                # Find all language lines (cs, en, de, pl)
                for m in line_pattern.finditer(block_text):
                    lang = m.group(1).lower()
                    val = m.group(2).strip()
                    if section_name in data_dict and lang in data_dict[section_name]:
                        data_dict[section_name][lang] = val

                # Find all image placeholders in this block
                for img_match in image_pattern.finditer(block_text):
                    img_path = img_match.group(1).strip()
                    data_dict["images"].append(img_path)

            # Check for missing lines
            missing = []
            for section_name in ["header", "title", "content"]:
                for lang_code in ["cs", "en", "de", "pl"]:
                    if data_dict[section_name][lang_code] is None:
                        missing.append(f"{section_name}.{lang_code}")

            if missing:
                self.log_error(f"{raw_filename} is missing lines: {', '.join(missing)}.")
                any_error = True
                break

            parsed_data[raw_filename] = data_dict
            self.progress_bar["value"] = idx
            self.master.update_idletasks()

        if any_error:
            self.status_label.config(text="Error encountered. No files generated.")
            messagebox.showwarning("Deployment Aborted",
                                   "One or more files were invalid. No HTML files have been generated.")
            self.start_button.config(state=tk.NORMAL)
            return

        self.status_label.config(text="All files valid. Generating HTML...")
        self.master.update_idletasks()

        title_re   = re.compile(r'(<title>)(.*?)(</title>)', re.DOTALL | re.IGNORECASE)
        header_re  = re.compile(r'(<div\s+[^>]*id=["\']header-title["\'][^>]*>)(.*?)(</div>)', re.DOTALL)
        content_re = re.compile(r'(<p\s+[^>]*id=["\']content-text["\'][^>]*>)(.*?)(</p>)', re.DOTALL)
        js_titles_re   = re.compile(r'const\s+titles\s*=\s*\{[^}]*\};', re.DOTALL)
        js_contents_re = re.compile(r'const\s+contents\s*=\s*\{[^}]*\};', re.DOTALL)

        manifest_lines = []
        self.progress_bar["value"] = 0

        for idx, raw_filename in enumerate(raw_files, start=1):
            self.status_label.config(text=f"Generating for {raw_filename} ({idx} of {total_files})")
            self.master.update_idletasks()

            data_dict = parsed_data[raw_filename]

            mod_content = template_content

            cs_title   = data_dict["title"]["cs"]
            cs_header  = data_dict["header"]["cs"]
            cs_content = data_dict["content"]["cs"]

            # Replace <title>
            mod_content = title_re.sub(lambda m: m.group(1) + cs_title + m.group(3), mod_content)
            # Replace header div
            mod_content = header_re.sub(lambda m: m.group(1) + cs_header + m.group(3), mod_content)
            # Replace content paragraph
            mod_content = content_re.sub(lambda m: m.group(1) + cs_content + m.group(3), mod_content)

            # Prepare new JS objects
            def strip_q(s):
                return s.strip('"')

            h_cs = strip_q(data_dict["header"]["cs"])
            h_en = strip_q(data_dict["header"]["en"])
            h_de = strip_q(data_dict["header"]["de"])
            h_pl = strip_q(data_dict["header"]["pl"])
            new_titles_js = (
                f'const titles = {{'
                f'"cs": "{h_cs}", '
                f'"en": "{h_en}", '
                f'"de": "{h_de}", '
                f'"pl": "{h_pl}"'
                f'}};'
            )

            c_cs = strip_q(data_dict["content"]["cs"])
            c_en = strip_q(data_dict["content"]["en"])
            c_de = strip_q(data_dict["content"]["de"])
            c_pl = strip_q(data_dict["content"]["pl"])
            new_contents_js = (
                f'const contents = {{'
                f'"cs": "{c_cs}", '
                f'"en": "{c_en}", '
                f'"de": "{c_de}", '
                f'"pl": "{c_pl}"'
                f'}};'
            )

            # Replace JS placeholders
            mod_content = js_titles_re.sub(new_titles_js, mod_content)
            mod_content = js_contents_re.sub(new_contents_js, mod_content)

            # Replace all image placeholders found
            for img_path in data_dict["images"]:
                img_tag = f'<img src="{img_path}" class="content-image" />'
<<<<<<< HEAD
                mod_content = mod_content.replace(f'<{img_path}>', img_tag)
=======
                mod_content = mod_content.replace(f'<pathfromroot\\{img_path}>', img_tag)
>>>>>>> a99e174 (PictureTest3)

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

            order_match = re.match(r"(\d+)\.", raw_filename)
            order_str = order_match.group(1) if order_match else str(idx)
            manifest_lines.append(f"{order_str}. {output_filename}")

            self.progress_bar["value"] = idx
            self.master.update_idletasks()

        if any_error:
            self.status_label.config(text="Error encountered while writing files. No manifest created.")
            messagebox.showwarning("Deployment Aborted",
                                   "Error while writing files. Partial files may exist, but no manifest was created.")
            self.start_button.config(state=tk.NORMAL)
            return

        # Write manifest
        try:
            with open(MANIFEST_FILE, "w", encoding="utf-8") as mf:
                mf.write("#Manifest\n")
                mf.write("\n".join(manifest_lines))
        except Exception as e:
            self.log_error(f"Error writing manifest.txt: {e}")
            self.status_label.config(text="Error encountered. Manifest not created.")
            messagebox.showwarning("Deployment Partial",
                                   "All HTML files were generated, but manifest.txt could not be written.")
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
