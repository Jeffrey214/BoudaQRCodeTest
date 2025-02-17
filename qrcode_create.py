import qrcode

# Your working GitHub Pages link
hosted_url = "https://jeffrey214.github.io/BoudaQRCodeTest/test.html"

# Generate a fresh QR Code
qr = qrcode.make(hosted_url)

# Save and Show
qr.save("BoudaQRCode.png")
qr.show()

print(f"✅ QR code saved as 'BoudaQRCode.png'. Scan to open: {hosted_url}")
