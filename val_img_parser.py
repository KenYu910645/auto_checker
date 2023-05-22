import cv2
from PIL import Image
import numpy as np
import pytesseract

# Open the GIF image using Pillow
img = np.array(Image.open("/home/lab530/KenYu/auto_checker/img.gif").convert("RGB"))
hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# HSV color thresholding
mask = cv2.inRange(hsv_img, (0, 255, 0), (255, 255, 255))

# Create a structuring element for erosion
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))  # Adjust the kernel size as needed

# Erode pixels
mask = cv2.erode(mask, kernel, iterations=1)

# Dilate pixels
mask = cv2.dilate(mask, kernel, iterations=1)

# Reverse white and black
mask = cv2.bitwise_not(mask)

# Save image
mask_img = Image.fromarray(mask).save("mask.png", "PNG")

print(pytesseract.image_to_string(mask, lang="eng"))

