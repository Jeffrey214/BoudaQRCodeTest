import os
import re
import sys
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import our content parser module.
from content_parser import parse_content_file

# Set up logging to a file.
logging.basicConfig(
    filename="deploy.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Folder paths
TEMPLATE_FOLDER = "template"
CONTENT_FOLDER = "ContentFiles"
DEPLOY_FOLDER = "DeploymentFiles"

# Manifest and Template file paths
MANIFEST_FILE = os.path.join(DEPLOY_FOLDER, "manifest.txt")
TEMPLATE_FILE = os.path.join(TEMPLATE_FOLDER, "template.html")

# Helper function to remove quotes if present.
def maybe_strip_quotes(s):
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s

# Escape backticks and single quotes for JS.
def js_escape(s):
    return s.replace("`", "\\`").replace("'", "\\'")

# Remove any <img ...> tags from the given HTML.
def remove_images(html):
    return re.sub(r'<img[^>]*>', '', html)

# --- Duplicate File Chooser Dialog ---
def choose_file_dialog(options, title="Duplicate Files Detected", prompt="Select one file to use for this order:"):
    dialog = tk.Toplevel()
    dialog.title(title)
    tk.Label(dialog, text=prompt).pack(padx=10, pady=10)
    listbox = tk.Listbox(dialog, selectmode=tk.SINGLE, width=50)
    listbox.pack(padx=10, pady=10)
    for option in options:
        listbox.insert(tk.END, option)
    chosen = []
    def on_ok():
        selection = listbox.curselection()
        if selection:
            chosen.append(listbox.get(selection[0]))
        dialog.destroy()
    ok_button = tk.Button(dialog, text="OK", command=on_ok)
    ok_button.pack(pady=10)
    dialog.transient()   # Show on top
    dialog.grab_set()    # Make modal
    dialog.wait_window()
    if chosen:
        return chosen[0]
    else:
        return None

# Helper to remove wrapping <p> tags if present.
def remove_wrapping_p(html):
    html = html.strip()
    if html.startswith("<p>") and html.endswith("</p>"):
        return html[3:-4].strip()
    return html

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
        logging.info("Deployment Processor initialized.")

    def log_error(self, message):
        self.errors.append(message)
        self.error_text.insert(tk.END, message + "\n")
        self.error_text.see(tk.END)
        logging.error(message)

    def process_files(self):
        logging.info("Processing started.")
        self.start_button.config(state=tk.DISABLED)
        self.error_text.delete("1.0", tk.END)
        self.errors.clear()
        self.status_label.config(text="Starting processing...")
        self.master.update_idletasks()

        # Ensure required folders exist.
        for folder in [TEMPLATE_FOLDER, CONTENT_FOLDER, DEPLOY_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)
                logging.info(f"Created folder: {folder}")

        # Load the template.
        try:
            with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
                template_content = f.read()
            logging.info("Template loaded successfully.")
        except Exception as e:
            self.log_error("Error reading template file: " + str(e))
            messagebox.showerror("Error", "Cannot read template file.")
            self.start_button.config(state=tk.NORMAL)
            return

        # List all content files with .txt or .md extension.
        raw_files = [f for f in os.listdir(CONTENT_FOLDER) if f.lower().endswith((".txt", ".md"))]
        if not raw_files:
            self.log_error("No content files found in ContentFiles.")
            self.start_button.config(state=tk.NORMAL)
            return

        # Group files by numeric order (extracted from filename).
        file_groups = {}
        order_pattern = re.compile(r"(\d+)\.")
        for filename in raw_files:
            match = order_pattern.match(filename)
            if match:
                order = match.group(1)
                file_groups.setdefault(order, []).append(filename)
            else:
                logging.warning(f"File {filename} does not have a numeric prefix; skipping.")
        # For groups with duplicates, ask the user which file to use.
        selected_files = []
        for order in sorted(file_groups, key=lambda x: int(x)):
            group = file_groups[order]
            if len(group) == 1:
                selected_files.append(group[0])
            else:
                choice = choose_file_dialog(group, title=f"Duplicate Order {order}", 
                                            prompt=f"Multiple files found for order {order}. Choose one:")
                if choice:
                    selected_files.append(choice)
                else:
                    self.log_error(f"No selection made for duplicate order {order}. Aborting.")
                    messagebox.showwarning("Deployment Aborted", f"Duplicate order {order} not resolved.")
                    self.start_button.config(state=tk.NORMAL)
                    return

        self.progress_bar["maximum"] = len(selected_files)
        logging.info(f"Selected {len(selected_files)} files for processing.")

        # Parse each content file using the content_parser module.
        parsed_data = {}
        any_error = False
        for idx, filename in enumerate(selected_files, start=1):
            filepath = os.path.join(CONTENT_FOLDER, filename)
            try:
                data = parse_content_file(filepath)
                parsed_data[filename] = data
                logging.debug(f"Parsed file: {filename}")
            except Exception as e:
                self.log_error(f"Error parsing {filename}: {e}")
                any_error = True
                break
            self.progress_bar["value"] = idx
            self.master.update_idletasks()

        if any_error:
            self.status_label.config(text="Error encountered during parsing. No files generated.")
            messagebox.showwarning("Deployment Aborted", "One or more files failed to parse.")
            self.start_button.config(state=tk.NORMAL)
            logging.error("Processing aborted due to parsing errors.")
            return

        self.status_label.config(text="All files valid. Generating HTML...")
        self.master.update_idletasks()

        # Replacement patterns in the template.
        title_re = re.compile(r'(<title>)(.*?)(</title>)', re.DOTALL | re.IGNORECASE)
        header_re = re.compile(r'(<div\s+[^>]*id=["\']header-title["\'][^>]*>)(.*?)(</div>)', re.DOTALL)
        content_re = re.compile(r'(<div\s+[^>]*id=["\']content-text["\'][^>]*>)(.*?)(</div>)', re.DOTALL)
        js_titles_re = re.compile(r'const\s+titles\s*=\s*\{[^}]*\};', re.DOTALL)
        js_contents_re = re.compile(r'const\s+contents\s*=\s*\{[^}]*\};', re.DOTALL)

        manifest_lines = []
        self.progress_bar["value"] = 0
        overwritten_files = []

        for idx, filename in enumerate(selected_files, start=1):
            logging.info(f"Generating HTML for: {filename}")
            self.status_label.config(text=f"Generating for {filename} ({idx} of {len(selected_files)})")
            self.master.update_idletasks()
            data = parsed_data[filename]
            mod_content = template_content

            # Process title and header. Remove any image tags from the header.
            cs_title = remove_wrapping_p(maybe_strip_quotes(data["title"]["cs"]))
            cs_header = remove_wrapping_p(maybe_strip_quotes(data["header"]["cs"]))
            cs_header = remove_images(cs_header)
            cs_content = maybe_strip_quotes(data["content"]["cs"])

            mod_content = title_re.sub(lambda m: m.group(1) + cs_title + m.group(3), mod_content)
            mod_content = header_re.sub(lambda m: m.group(1) + cs_header + m.group(3), mod_content)
            mod_content = content_re.sub(lambda m: m.group(1) + cs_content + m.group(3), mod_content)

            # Build new JS objects for language switching.
            h_cs = js_escape(remove_images(remove_wrapping_p(maybe_strip_quotes(data["header"]["cs"]))))
            h_en = js_escape(remove_images(remove_wrapping_p(maybe_strip_quotes(data["header"]["en"]))))
            h_de = js_escape(remove_images(remove_wrapping_p(maybe_strip_quotes(data["header"]["de"]))))
            h_pl = js_escape(remove_images(remove_wrapping_p(maybe_strip_quotes(data["header"]["pl"]))))
            new_titles_js = f"const titles = {{'cs': `{h_cs}`, 'en': `{h_en}`, 'de': `{h_de}`, 'pl': `{h_pl}`}};"
            c_cs = js_escape(maybe_strip_quotes(data["content"]["cs"]))
            c_en = js_escape(maybe_strip_quotes(data["content"]["en"]))
            c_de = js_escape(maybe_strip_quotes(data["content"]["de"]))
            c_pl = js_escape(maybe_strip_quotes(data["content"]["pl"]))
            new_contents_js = f"const contents = {{'cs': `{c_cs}`, 'en': `{c_en}`, 'de': `{c_de}`, 'pl': `{c_pl}`}};"
            mod_content = js_titles_re.sub(new_titles_js, mod_content)
            mod_content = js_contents_re.sub(new_contents_js, mod_content)

            # Replace image placeholders (extended syntax).
            for img_tuple in data["images"]:
                img_path, img_code = img_tuple
                if not img_code:
                    img_code = "w"
                if img_code.lower() == "w":
                    style = "width: 100%; height: auto;"
                else:
                    size_letter = img_code[0].lower()
                    align_letter = img_code[1].lower() if len(img_code) > 1 else "c"
                    size_map = {'s': '25%', 'm': '50%', 'l': '75%'}
                    width = size_map.get(size_letter, "100%")
                    if align_letter == "c":
                        style = f"width: {width}; display: block; margin-left: auto; margin-right: auto; height: auto;"
                    elif align_letter == "l":
                        style = f"width: {width}; float: left; margin-right: 20px; height: auto;"
                    elif align_letter == "r":
                        style = f"width: {width}; float: right; margin-left: 20px; height: auto;"
                    else:
                        style = f"width: {width}; height: auto;"
                if img_code.lower() == "w":
                    placeholder = f"<{img_path}>"
                else:
                    placeholder = f"<{img_path}|{img_code}>"
                adjusted_path = f"../{img_path}"
                img_tag = f'<img src="{adjusted_path}" class="content-image" style="{style}" onerror="this.remove()" />'
                mod_content = mod_content.replace(placeholder, img_tag)

            base_name = os.path.splitext(filename)[0]
            output_filename = base_name + ".html"
            output_path = os.path.join(DEPLOY_FOLDER, output_filename)
            if os.path.exists(output_path):
                overwritten_files.append(output_filename)
            try:
                with open(output_path, "w", encoding="utf-8") as outf:
                    outf.write(mod_content)
                logging.info(f"Generated HTML: {output_filename}")
            except Exception as e:
                self.log_error(f"Error writing {output_filename}: {e}")
                any_error = True
                break

            order_match = re.match(r"(\d+)\.", filename)
            order_str = order_match.group(1) if order_match else str(idx)
            manifest_lines.append(f"{order_str}. {output_filename}")
            self.progress_bar["value"] = idx
            self.master.update_idletasks()

        if any_error:
            self.status_label.config(text="Error encountered while writing files. No manifest created.")
            messagebox.showwarning("Deployment Aborted", "Error while writing files. Partial files may exist, but no manifest was created.")
            self.start_button.config(state=tk.NORMAL)
            logging.error("Processing aborted due to errors.")
            return

        try:
            with open(MANIFEST_FILE, "w", encoding="utf-8") as mf:
                mf.write("#Manifest\n")
                mf.write("\n".join(manifest_lines))
            logging.info("Manifest file written successfully.")
        except Exception as e:
            self.log_error(f"Error writing manifest.txt: {e}")
            self.status_label.config(text="Error encountered. Manifest not created.")
            messagebox.showwarning("Deployment Partial", "All HTML files were generated, but manifest.txt could not be written.")
            self.start_button.config(state=tk.NORMAL)
            return

        if overwritten_files:
            warning_message = f"Warning! {len(overwritten_files)} file(s) were overwritten:\n" + "\n".join(overwritten_files)
            logging.warning(warning_message)
            messagebox.showwarning("Files Overwritten", warning_message)

        self.status_label.config(text="Processing complete.")
        messagebox.showinfo("Done", "Processing complete. All files have been generated.")
        self.start_button.config(state=tk.NORMAL)
        logging.info("Processing complete.")

def run_gui():
    root = tk.Tk()
    app = ProcessorUI(root)
    root.mainloop()

# --- Watch mode using watchdog ---
class DeploymentEventHandler(FileSystemEventHandler):
    def __init__(self, deploy_func):
        super().__init__()
        self.deploy_func = deploy_func

    def on_modified(self, event):
        if any(folder in event.src_path for folder in [TEMPLATE_FOLDER, CONTENT_FOLDER]):
            logging.info(f"Change detected in {event.src_path}. Rerunning deployment.")
            self.deploy_func()

def run_watch_mode(deploy_func):
    event_handler = DeploymentEventHandler(deploy_func)
    observer = Observer()
    observer.schedule(event_handler, TEMPLATE_FOLDER, recursive=True)
    observer.schedule(event_handler, CONTENT_FOLDER, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def run_headless():
    root = tk.Tk()
    root.withdraw()
    app = ProcessorUI(root)
    app.process_files()
    run_watch_mode(app.process_files)

if __name__ == '__main__':
    if "--watch" in sys.argv:
        logging.info("Starting in headless watch mode.")
        run_headless()
    else:
        run_gui()
