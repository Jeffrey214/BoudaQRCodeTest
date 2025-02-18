import os
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# Folders (assumed relative to the script’s directory)
TEMPLATE_FOLDER = "template"
CONTENT_FOLDER = "ContentFiles"
DEPLOY_FOLDER = "DeploymentFiles"
MANIFEST_FILE = os.path.join(DEPLOY_FOLDER, "manifest.txt")

# Template file name (change if necessary)
TEMPLATE_FILE = os.path.join(TEMPLATE_FOLDER, "template.html")

# Regex patterns to extract information from the raw content file
PATTERN_TITLE = re.compile(r"<title>(.*?)</title>", re.DOTALL)
PATTERN_HEADER = re.compile(r'<div[^>]*id=["\']header-title["\'][^>]*>(.*?)</div>', re.DOTALL)
PATTERN_CS_CONTENT = re.compile(r'"cs":\s*"([^"]*?)",', re.DOTALL)

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

        # List to collect error messages
        self.errors = []

    def log_error(self, message):
        self.errors.append(message)
        self.error_text.insert(tk.END, message + "\n")
        self.error_text.see(tk.END)

    def process_files(self):
        self.start_button.config(state=tk.DISABLED)
        self.error_text.delete("1.0", tk.END)
        self.errors = []
        self.status_label.config(text="Starting processing...")
        self.master.update_idletasks()

        # Check for necessary folders
        for folder in [TEMPLATE_FOLDER, CONTENT_FOLDER, DEPLOY_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)
        
        # Load the template file
        try:
            with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
                template_content = f.read()
        except Exception as e:
            self.log_error(f"Error reading template file: {e}")
            messagebox.showerror("Error", "Cannot read template file.")
            self.start_button.config(state=tk.NORMAL)
            return

        # Get list of raw content files (.txt files)
        raw_files = [f for f in os.listdir(CONTENT_FOLDER) if f.lower().endswith(".txt")]
        if not raw_files:
            self.log_error("No raw content files found in ContentFiles folder.")
            self.start_button.config(state=tk.NORMAL)
            return

        # Sort files based on the numeric prefix before the first period.
        def sort_key(filename):
            match = re.match(r"(\d+)\.", filename)
            return int(match.group(1)) if match else 9999
        raw_files.sort(key=sort_key)

        manifest_lines = []
        total_files = len(raw_files)
        self.progress_bar["maximum"] = total_files

        for idx, raw_filename in enumerate(raw_files, start=1):
            self.status_label.config(text=f"Processing {raw_filename} ({idx} of {total_files})")
            self.master.update_idletasks()

            raw_path = os.path.join(CONTENT_FOLDER, raw_filename)
            try:
                with open(raw_path, "r", encoding="utf-8") as rf:
                    raw_data = rf.read()
            except Exception as e:
                self.log_error(f"Error reading {raw_filename}: {e}")
                continue

            # Extract title from raw content file
            title_match = PATTERN_TITLE.search(raw_data)
            if title_match:
                extracted_title = title_match.group(1).strip()
            else:
                extracted_title = "No Title Found"
                self.log_error(f"Title not found in {raw_filename}")

            # Extract header title from raw content file
            header_match = PATTERN_HEADER.search(raw_data)
            if header_match:
                extracted_header = header_match.group(1).strip()
            else:
                extracted_header = "No Header Found"
                self.log_error(f"Header title not found in {raw_filename}")

            # Extract 'cs' content from the JavaScript content object
            content_match = PATTERN_CS_CONTENT.search(raw_data)
            if content_match:
                extracted_content = content_match.group(1).strip()
            else:
                extracted_content = "No Content Found"
                self.log_error(f"'cs' content not found in {raw_filename}")

            # Replace placeholders in the template content
            # The template file should contain the following markers:
            # {{TITLE}}, {{HEADER_TITLE}}, and {{CONTENT}}
            modified_content = template_content.replace("{{TITLE}}", extracted_title)
            modified_content = modified_content.replace("{{HEADER_TITLE}}", extracted_header)
            modified_content = modified_content.replace("{{CONTENT}}", extracted_content)

            # Determine the output filename (replace .txt with .html)
            base_name = os.path.splitext(raw_filename)[0]
            output_filename = base_name + ".html"
            output_path = os.path.join(DEPLOY_FOLDER, output_filename)

            try:
                with open(output_path, "w", encoding="utf-8") as outf:
                    outf.write(modified_content)
            except Exception as e:
                self.log_error(f"Error writing {output_filename}: {e}")
                continue

            # Extract order number from the filename (assumes filename starts with number followed by a period)
            order_match = re.match(r"(\d+)\.", raw_filename)
            order_str = order_match.group(1) if order_match else str(idx)
            manifest_lines.append(f"{order_str}. {output_filename}")

            # Update progress bar
            self.progress_bar["value"] = idx
            self.master.update_idletasks()

        # Write the manifest file
        try:
            with open(MANIFEST_FILE, "w", encoding="utf-8") as mf:
                mf.write("\n".join(manifest_lines))
        except Exception as e:
            self.log_error(f"Error writing manifest file: {e}")

        self.status_label.config(text="Processing complete.")
        messagebox.showinfo("Done", "Processing complete.")
        self.start_button.config(state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = ProcessorUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
