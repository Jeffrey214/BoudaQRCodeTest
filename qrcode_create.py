import qrcode
import os

# Ensure the QR Codes folder exists
qr_folder = "QRCodes"
os.makedirs(qr_folder, exist_ok=True)

# Let the user choose which HTML folder to use
print("Select the HTML folder:")
print("1: TestHTMLFiles")
print("2: DeploymentHTMLFiles")
folder_choice = input("Enter 1 or 2: ").strip()

if folder_choice == "1":
    folder_name = "TestHTMLFiles"
elif folder_choice == "2":
    folder_name = "DeploymentHTMLFiles"
else:
    print("Invalid choice, defaulting to TestHTMLFiles.")
    folder_name = "TestHTMLFiles"

# Prompt user for the page name
page_name = input("Enter the HTML page name (without .html): ").strip()

# Construct the full URL with the chosen folder structure
hosted_url = f"https://jeffrey214.github.io/BoudaQRCodeTest/{folder_name}/{page_name}.html"

# Generate the QR Code
qr = qrcode.make(hosted_url)

# Define the file path
file_path = os.path.join(qr_folder, f"{page_name}_QRCode.png")

# Save and display the QR code
qr.save(file_path)
qr.show()

print(f"✅ QR code saved as '{file_path}'. Scan to open: {hosted_url}")
