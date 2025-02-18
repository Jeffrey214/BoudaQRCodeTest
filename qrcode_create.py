import qrcode
import os

def generate_qr_code(url, output_name, subfolder):
    """
    Generate a QR code for the given URL and save it as output_name_QRCode.png
    inside QRCodes/<subfolder> folder.
    """
    # Base folder for QR codes
    base_qr_folder = "QRCodes"
    # Subfolder for either "DeploymentQR" or "Targetted"
    target_folder = os.path.join(base_qr_folder, subfolder)

    # Create the subfolder if it doesn't exist
    os.makedirs(target_folder, exist_ok=True)

    # Generate the QR code
    qr = qrcode.make(url)

    # Build the output file path
    file_path = os.path.join(target_folder, f"{output_name}_QRCode.png")

    # Save the QR code
    qr.save(file_path)

    print(f"✅ QR code saved as '{file_path}'. URL: {url}")

def main():
    print("Select an option:")
    print("1: Deploy (Generate QR codes for all HTML files in 'DeploymentFiles')")
    print("2: TestFiles (Generate a single QR code for a file in 'TestHTMLFiles')")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        # 1) DEPLOY
        folder_name = "DeploymentFiles"
        html_files = [f for f in os.listdir(folder_name) if f.lower().endswith(".html")]
        if not html_files:
            print("No .html files found in the DeploymentFiles folder.")
            return

        print("Generating QR codes for all .html files in DeploymentFiles...")
        for html_file in html_files:
            base_name = os.path.splitext(html_file)[0]
            # Construct the URL for the hosted file
            hosted_url = f"https://jeffrey214.github.io/BoudaQRCodeTest/DeploymentHTMLFiles/{html_file}"

            # Generate the QR code in the QRCodes/DeploymentQR folder
            generate_qr_code(hosted_url, base_name, "DeploymentQR")

        print("All deployment QR codes generated successfully.")

    elif choice == "2":
        # 2) TESTFILES
        folder_name = "TestHTMLFiles"

        # Prompt for page name (without extension)
        page_name = input("Enter the HTML page name (without extension): ").strip()
        if not page_name:
            print("No page name provided. Exiting.")
            return

        # Prompt for extension (default to ".html" if blank)
        extension = input("Enter file extension (default is .html): ").strip()
        if not extension.startswith("."):
            extension = f".{extension}" if extension else ".html"

        # Construct the URL
        hosted_url = f"https://jeffrey214.github.io/BoudaQRCodeTest/{folder_name}/{page_name}{extension}"

        # Generate the QR code in the QRCodes/Targetted folder
        generate_qr_code(hosted_url, page_name, "Targetted")

        print("Test file QR code generated successfully.")

    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
