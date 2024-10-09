import pyautogui
import keyboard
import time
from PIL import ImageGrab

# Parameters for the cropping region
CROP_WIDTH = 300  # Width of the cropping region
CROP_HEIGHT = 75  # Height of the cropping region


def capture_screenshot(center_x, center_y, width, height):
    # Get screen size
    screen_width, screen_height = pyautogui.size()

    # Get the scale factor between the actual screen size and the image size captured by ImageGrab
    screenshot = ImageGrab.grab()
    img_width, img_height = screenshot.size
    scale_x = img_width / screen_width
    scale_y = img_height / screen_height

    # Scale the center coordinates
    scaled_center_x = int(center_x * scale_x)
    scaled_center_y = int(center_y * scale_y)

    # Calculate the bounding box of the region to crop
    left = max(0, scaled_center_x - int(width * scale_x) // 2)
    top = max(0, scaled_center_y - int(height * scale_y) // 2)
    right = min(img_width, scaled_center_x + int(width * scale_x) // 2)
    bottom = min(img_height, scaled_center_y + int(height * scale_y) // 2)

    # Crop the screenshot to the desired region
    cropped_image = screenshot.crop((left, top, right, bottom))

    # Save the cropped image
    timestamp = int(time.time())
    cropped_image.save(f"cropped_screenshot_{timestamp}.png")
    print(f"Saved cropped screenshot as cropped_screenshot_{timestamp}.png")


def main():
    print("Press 'c' to capture a screenshot at the mouse position, or 'q' to quit.")
    while True:
        # Wait for the user to press 'c' to capture a screenshot
        if keyboard.is_pressed('c'):
            # Get the current mouse position
            x, y = pyautogui.position()

            # Capture and save the cropped screenshot
            capture_screenshot(x, y, CROP_WIDTH, CROP_HEIGHT)

            # Pause to avoid multiple captures from a single key press
            time.sleep(0.5)

        # Exit the loop if the user presses 'q'
        elif keyboard.is_pressed('q'):
            print("Quitting...")
            break


if __name__ == "__main__":
    main()