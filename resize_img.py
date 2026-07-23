from PIL import Image
import os
img = Image.open("C:/ComfyUI/output/wedding_output_00001_.png")
w = 1280
h = int(img.height * w / img.width)
img.resize((w, h), Image.LANCZOS).save("C:/temp/tts/wedding_preview.jpg", "JPEG", quality=80)
print("Done")
