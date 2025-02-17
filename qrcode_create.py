import qrcode
import os

# Ensure the QR Codes folder exists
qr_folder = "QRCodes"
os.makedirs(qr_folder, exist_ok=True)

# Prompt user for the page name
page_name = input("Enter the HTML page name (without .html): ")

# Construct the full URL with the correct folder structure
hosted_url = f"https://jeffrey214.github.io/BoudaQRCodeTest/HTMLFiles/{page_name}.html"

# Generate a fresh QR Code
qr = qrcode.make(hosted_url)

# Define the file path
file_path = os.path.join(qr_folder, f"{page_name}_QRCode.png")

# Save and Show
qr.save(file_path)
qr.show()

print(f"✅ QR code saved as '{file_path}'. Scan to open: {hosted_url}")
