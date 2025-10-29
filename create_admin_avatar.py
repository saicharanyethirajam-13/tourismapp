import os
from PIL import Image, ImageDraw, ImageFont

# Ensure 'static' folder exists
os.makedirs("static", exist_ok=True)

# Create a new blue image
img = Image.new("RGB", (300, 300), color=(0, 102, 204))
draw = ImageDraw.Draw(img)

# Text and font
text = "ADMIN"
font = ImageFont.load_default()

# Use textbbox instead of textsize (newer Pillow versions)
bbox = draw.textbbox((0, 0), text, font=font)
text_w = bbox[2] - bbox[0]
text_h = bbox[3] - bbox[1]

# Center text
x = (img.width - text_w) / 2
y = (img.height - text_h) / 2
draw.text((x, y), text, fill=(255, 255, 255), font=font)

# Save inside 'static' folder
output_path = os.path.join("static", "admin_default.png")
img.save(output_path)
print(f"✅ Default admin avatar created at {output_path}")
