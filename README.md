## BoudaQRCodeTest
Version 0.3.0-alpha

# Program Description
This is a simple program meant to be integrated with physical QR Codes within the Artillery Fortress Bouda
This program uses a html template with differant graphical elements, then using a simple python program content files are handled and integrated into the html environment as seperate display files.

At this current time this is a test a development build with all basic functions working, but it is far from complete.

# Instructions:
1. Create content files and place them in the ContentFiles folder in root. Files can be in either ".txt" or ".md" format, depending on format there are differant rules for formatting.
    - ".txt" file template is located in (template/ContentFilesTemplate/txtFileTemplate.txt)
    - Use standard text for content
    - For pictures please use the following format "<pathfromroot/./picturefile.ext|formatcode>
    - Supported extensions include: ".png", ".jpg", ".obj", and ".gif"
    - Supported format coding of pictures include: "|s", "|m", and "|l" (Corresponds to "Small", "Medium", and "Large) for size of picture and "|-l", "|-c", and "|-r" (Corresponds to "Left", "Center", and "Right")

    - ".md" file template is located in (template/ContentFilesTemplate/mdFileTemplate.md)
    - Use markdown standard text format, (referance: https://www.markdownguide.org/basic-syntax/)
    - For pictures please use the following format "<pathfromroot/./picturefile.ext|formatcode>
    - Supported extensions include: ".png", ".jpg", ".obj", and ".gif"
    - Supported format coding of pictures include: "|s", "|m", and "|l" (Corresponds to "Small", "Medium", and "Large) for size of picture and "|-l", "|-c", and "|-r" (Corresponds to "Left", "Center", and "Right")

2. Use deploy.py to convert the content files into html and inject it into the website html template (location: template/template.html)
    - Creates .html files of the ContentFiles that were created and prepares them for deployment

3. Use qrcode_create.py to generate custom QR Codes for each page, currently it works for github hosted pages
    - Configuration options can be found at the top of the code

# Support
For support feel free to contact me on discord at Jeffrey_214 or at jeffreyrdotson@gmail.com