import qrcode
import os
import requests
from PIL import Image, ImageDraw
from io import BytesIO

try:
    from PIL import ImageResampling
    RESAMPLE_FILTER = ImageResampling.LANCZOS
except ImportError:
    RESAMPLE_FILTER = Image.LANCZOS

# =========================
# Configuration Section
# =========================
# GitHub configuration (for hosted URLs)
GITHUB_USERNAME = "jeffrey214"
REPO_NAME = "BoudaQRCodeTest"
BASE_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}"
# For QR code generation in deployment or test mode, hosted URLs will be built using BASE_URL.

# Local logo configuration:
# deploy.py is in the "Control Modules" folder, so we go one level up to the root.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(CURRENT_DIR, "..", "PictureDeps", "Logos", "BoudaLogo.PNG")
# =========================

def generate_qr_code(url, output_name, subfolder, debug=False):
    """
    Generate a QR code for the given URL and save it as output_name_QRCode.png
    inside QRCodes/<subfolder> folder.
    A white square ("hole") (30% of the QR code's width) is created in the center.
    The logo is resized to fit within this square while preserving its aspect ratio,
    and then centered within the white square.
    If debug is True, the logo is saved for verification.
    """
    # Base folder for QR codes
    base_qr_folder = "QRCodes"
    target_folder = os.path.join(base_qr_folder, subfolder)
    os.makedirs(target_folder, exist_ok=True)

    # Create QR code with high error correction
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    
    # Dimensions of the QR code
    qr_width, qr_height = qr_img.size
    # White hole size: 30% of QR code width (square)
    hole_size = int(qr_width * 0.3)
    hole_pos = ((qr_width - hole_size) // 2, (qr_height - hole_size) // 2)
    
    # Draw white square (the hole)
    draw = ImageDraw.Draw(qr_img)
    draw.rectangle([hole_pos, (hole_pos[0] + hole_size, hole_pos[1] + hole_size)], fill="white")
    
    # Load the logo from the local repository
    try:
        if not os.path.exists(LOGO_PATH):
            raise FileNotFoundError(f"Logo file not found at {LOGO_PATH}")
        with open(LOGO_PATH, "rb") as f:
            logo_data = f.read()
        
        if debug:
            logo_debug_path = os.path.join(target_folder, f"{output_name}_LogoDebug.png")
            with open(logo_debug_path, "wb") as f:
                f.write(logo_data)
            print(f"[DEBUG] Logo loaded and saved as {logo_debug_path}")
        
        logo = Image.open(BytesIO(logo_data)).convert("RGBA")
        orig_w, orig_h = logo.size
        aspect_ratio = orig_w / orig_h
        
        # Compute new dimensions so that both width and height are <= hole_size
        if aspect_ratio >= 1:
            # Logo is wider than tall or square: limit width to hole_size
            new_w = hole_size
            new_h = int(hole_size / aspect_ratio)
        else:
            # Logo is taller than wide: limit height to hole_size
            new_h = hole_size
            new_w = int(hole_size * aspect_ratio)
        
        logo = logo.resize((new_w, new_h), resample=RESAMPLE_FILTER)
        
        # Calculate offset within the white square to center the logo
        offset_x = (hole_size - new_w) // 2
        offset_y = (hole_size - new_h) // 2
        paste_pos = (hole_pos[0] + offset_x, hole_pos[1] + offset_y)
        
        # Paste the logo using its alpha channel (if available)
        qr_img.paste(logo, paste_pos, mask=logo)
    except Exception as e:
        print(f"Logo load or paste failed: {e}. Proceeding without logo.")

    # Save final QR code image
    file_path = os.path.join(target_folder, f"{output_name}_QRCode.png")
    qr_img.save(file_path)
    print(f"✅ QR code saved as '{file_path}'. URL: {url}")

def main():
    print("Select an option:")
    print("1: Deploy (Generate QR codes for all HTML files in 'DeploymentFiles')")
    print("1d: Deploy in debug mode (also saves the logo for verification)")
    print("2: TestFiles (Generate a single QR code for a file in 'TestHTMLFiles')")
    choice = input("Enter your choice: ").strip()
    debug_mode = (choice == "1d")
    
    if choice in ["1", "1d"]:
        folder_name = "DeploymentFiles"
        html_files = [f for f in os.listdir(folder_name) if f.lower().endswith(".html")]
        if not html_files:
            print("No .html files found in the DeploymentFiles folder.")
            return
        print("Generating QR codes for all .html files in DeploymentFiles...")
        for html_file in html_files:
            base_name = os.path.splitext(html_file)[0]
            hosted_url = f"{BASE_URL}/DeploymentFiles/{html_file}"
            generate_qr_code(hosted_url, base_name, "DeploymentQR", debug=debug_mode)
        print("All deployment QR codes generated successfully.")
    
    elif choice == "2":
        folder_name = "TestHTMLFiles"
        page_name = input("Enter the HTML page name (without extension): ").strip()
        if not page_name:
            print("No page name provided. Exiting.")
            return
        extension = input("Enter file extension (default is .html): ").strip()
        if not extension.startswith("."):
            extension = f".{extension}" if extension else ".html"
        hosted_url = f"{BASE_URL}/{folder_name}/{page_name}{extension}"
        generate_qr_code(hosted_url, page_name, "Targetted", debug=False)
        print("Test file QR code generated successfully.")
    
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
