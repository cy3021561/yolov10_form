import cv2
import pyautogui
import numpy as np
from PIL import Image
import time
from functools import wraps



def measure_average_time(method):
    """
    Decorator to measure and print the average execution time of a method.

    Args:
        method (callable): The method to be decorated.

    Returns:
        callable: The wrapped method with timing functionality.
    """
    @wraps(method)
    def timed(*args, **kwargs):
        # Start the timer
        start_time = time.time()
        # Call the original method
        result = method(*args, **kwargs)
        # Stop the timer
        end_time = time.time()
        # Calculate elapsed time
        elapsed_time = end_time - start_time

        # Initialize tracking attributes if they don't exist
        if not hasattr(timed, 'total_time'):
            timed.total_time = 0.0
            timed.call_count = 0

        # Update total time and call count
        timed.total_time += elapsed_time
        timed.call_count += 1

        # Calculate average time
        average_time = timed.total_time / timed.call_count

        # Print the average time
        print(f"Average time spent on '{method.__name__}': {average_time:.6f} seconds over {timed.call_count} calls")

        return result
    return timed


class TemplateAligner:
    # Default threshold for template matching; can be adjusted as needed
    DEFAULT_TEMPLATE_MATCHING_THRESHOLD = 0.85

    def __init__(self, debug=False, screen_width=None, screen_height=None):
        """
        Initialize the TemplateAligner instance.

        Args:
            debug (bool): Flag to enable debugging mode.
            screen_width (int, optional): Width of the screen. Defaults to actual screen width if not provided.
            screen_height (int, optional): Height of the screen. Defaults to actual screen height if not provided.
        """
        self.debug = debug
        self.screen_width, self.screen_height = self._get_screen_dimensions(screen_width, screen_height)
        self.current_x = None  # Stores the current x-coordinate of the matched template
        self.current_y = None  # Stores the current y-coordinate of the matched template

    def _show_image(self, np_image):
        """
        Display an image using OpenCV.

        Args:
            np_image (numpy.ndarray): The image to display.
        """
        cv2.imshow("tmp", np_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    def _get_screen_dimensions(self, screen_w, screen_h):
        """
        Get the screen dimensions.

        Args:
            screen_w (int, optional): Provided screen width.
            screen_h (int, optional): Provided screen height.

        Returns:
            tuple: A tuple containing screen width and height.
        """
        if screen_w is not None and screen_h is not None:
            return screen_w, screen_h
        return pyautogui.size()  # Returns the actual screen size

    def template_match(self, screenshot_img, template_img):
        """
        Perform template matching to find the template in the screenshot.

        Args:
            screenshot_img (numpy.ndarray): The screenshot image in which to search.
            template_img (numpy.ndarray): The template image to search for.

        Returns:
            tuple: A tuple containing the maximum correlation value and location.
        """
        result = cv2.matchTemplate(screenshot_img, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return max_val, max_loc

    def get_screenshot(self):
        """
        Capture a screenshot of the current screen.

        Returns:
            numpy.ndarray: The grayscale screenshot image.
        """
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
        return screenshot_gray

    def get_screen_coordinates(self, screenshot_image, coor_x, coor_y):
        """
        Convert image coordinates to screen coordinates.

        Args:
            screenshot_image (numpy.ndarray): The image from which coordinates are taken.
            coor_x (int): X-coordinate in the image.
            coor_y (int): Y-coordinate in the image.

        Returns:
            tuple: Scaled X and Y coordinates relative to the screen size.
        """
        img_width, img_height = screenshot_image.shape[::-1]
        scale_x = img_width / self.screen_width
        scale_y = img_height / self.screen_height

        # Scale the center coordinates
        scaled_center_x = int(coor_x / scale_x)
        scaled_center_y = int(coor_y / scale_y)

        return scaled_center_x, scaled_center_y

    # @measure_average_time
    def align(self, template_image_path, target_image_path=None, show_crop=False, show_overlay=False, custom_threshold=None):
        """
        Align the template image with the target image or current screen.

        Args:
            template_image_path (str): Path to the template image.
            target_image_path (str, optional): Path to the target image. If None, a screenshot is used.
            show_crop (bool, optional): Whether to save the cropped matched area.
            show_overlay (bool, optional): Whether to save an overlay comparison image.

        Returns:
            bool: True if alignment is successful, False otherwise.
        """
        # Set custom threshold if it exist
        if custom_threshold:
            threshold_val = custom_threshold
        else:
            threshold_val = self.DEFAULT_TEMPLATE_MATCHING_THRESHOLD

        # Read the template image in grayscale
        template_img = cv2.imread(template_image_path, cv2.IMREAD_GRAYSCALE)

        # Use provided target image or take a screenshot
        if target_image_path:
            target_img = cv2.imread(target_image_path, cv2.IMREAD_GRAYSCALE)
        else:
            target_img = self.get_screenshot()  # Capture the current screen

        # Perform template matching
        max_val, max_loc = self.template_match(target_img, template_img)

        # Check if the match is above the threshold
        if max_val < threshold_val:
            print(f"No matching found for {template_image_path}. Score: {max_val}")
            return False

        # Optionally save the cropped matched area
        if show_crop:
            cropped_pil = self.cropped_match(template_img, target_img, max_loc, show_crop)
            cropped_pil.save("matched_cropped.png")

        # Optionally save an overlay comparison image
        if show_overlay:
            template_pil, target_pil = self.generate_overlay(template_img, target_img, max_loc, show_overlay)
            compare_pil = self.create_comparison_image(template_pil, target_pil)
            compare_pil.save("alignment_comparison.png")

        # Calculate the center coordinates of the matched area
        w, h = template_img.shape[::-1]
        self.current_x, self.current_y = self.get_screen_coordinates(
            target_img, max_loc[0] + w // 2, max_loc[1] + h // 2
        )
        return True

    def get_aligned_cropped(self, template_image_path, target_image_path=None, custom_threshold=None):
        """
        Output the aligned-cropped image on the target image or current screen.

        Args:
            template_image_path (str): Path to the template image.
            target_image_path (str, optional): Path to the target image. If None, a screenshot is used.

        Returns:
            PIL.Image.Image: The cropped matched area as a PIL image.
        """
        # Set custom threshold if it exist
        if custom_threshold:
            threshold_val = custom_threshold
        else:
            threshold_val = self.DEFAULT_TEMPLATE_MATCHING_THRESHOLD

        # Read the template image in grayscale
        template_img = cv2.imread(template_image_path, cv2.IMREAD_GRAYSCALE)

        # Use provided target image or take a screenshot
        if target_image_path:
            target_img = cv2.imread(target_image_path, cv2.IMREAD_GRAYSCALE)
        else:
            target_img = self.get_screenshot()  # Capture the current screen

        # Perform template matching
        max_val, max_loc = self.template_match(target_img, template_img)

        # Check if the match is above the threshold
        if max_val < threshold_val:
            print(max_val)
            print("No template matching found.")
            return None
        
        cropped_pil = self.cropped_match(template_img, target_img, max_loc)
        
        return cropped_pil


    def cropped_match(self, template_img, target_img, max_loc, show=False):
        """
        Crop the matched area from the target image.

        Args:
            template_img (numpy.ndarray): The template image.
            target_img (numpy.ndarray): The target image where the template was matched.
            max_loc (tuple): The top-left coordinates of the matched area.

        Returns:
            PIL.Image.Image: The cropped matched area as a PIL image.
        """
        # Get the dimensions of the template image
        w, h = template_img.shape[::-1]
        # Crop the matched region from the target image
        cropped_img = target_img[max_loc[1]:max_loc[1] + h, max_loc[0]:max_loc[0] + w]
        cropped_pil = Image.fromarray(cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB))

        if show:
            self._show_image(cropped_img)
        
        return cropped_pil

    def generate_overlay(self, template_img, target_img, max_loc, show=False):
        """
        Generate an overlay of the template image on the matched area in the target image.

        Args:
            template_img (numpy.ndarray): The template image.
            target_img (numpy.ndarray): The target image.
            max_loc (tuple): The top-left coordinates of the matched area.

        Returns:
            tuple: A tuple containing the template and target images as PIL images.
        """
        # Get the dimensions of the template image
        h, w = template_img.shape[:2]

        # Crop the matched region from the target image
        cropped_target_img = target_img[max_loc[1]:max_loc[1] + h, max_loc[0]:max_loc[0] + w]

        # Convert images to BGR format if they are grayscale
        if len(cropped_target_img.shape) == 2:
            cropped_target_img_bgr = cv2.cvtColor(cropped_target_img, cv2.COLOR_GRAY2BGR)
        else:
            cropped_target_img_bgr = cropped_target_img

        if len(template_img.shape) == 2:
            template_img_bgr = cv2.cvtColor(template_img, cv2.COLOR_GRAY2BGR)
        else:
            template_img_bgr = template_img

        # Resize the template image to match the cropped target image size
        template_img_bgr_resized = cv2.resize(template_img_bgr, (w, h))

        # Create an overlay by blending the two images
        overlay = cv2.addWeighted(cropped_target_img_bgr, 0.5, template_img_bgr_resized, 0.5, 0)
        
        if show:
            self._show_image(overlay)

        # Convert images to PIL format
        template_pil = Image.fromarray(cv2.cvtColor(template_img_bgr_resized, cv2.COLOR_BGR2RGB))
        target_pil = Image.fromarray(cv2.cvtColor(cropped_target_img_bgr, cv2.COLOR_BGR2RGB))

        return template_pil, target_pil

    def create_comparison_image(self, aligned_image: Image.Image, reference_image: Image.Image) -> Image.Image:
        """
        Create a side-by-side comparison image of the aligned and reference images.

        Args:
            aligned_image (PIL.Image.Image): The aligned template image.
            reference_image (PIL.Image.Image): The cropped target image.

        Returns:
            PIL.Image.Image: The comparison image.
        """
        # Ensure both images have the same dimensions
        max_width = max(aligned_image.width, reference_image.width)
        max_height = max(aligned_image.height, reference_image.height)

        aligned_resized = aligned_image.resize((max_width, max_height))
        reference_resized = reference_image.resize((max_width, max_height))

        # Create a new image to hold both images side by side
        comparison_image = Image.new('RGB', (max_width * 2, max_height))
        comparison_image.paste(aligned_resized, (0, 0))
        comparison_image.paste(reference_resized, (max_width, 0))

        return comparison_image


# Usage sample
def test_align(template_path, target_path=None):
    aligner = TemplateAligner()
    # result = aligner.align(
    #     template_path,
    #     target_path,
    #     show_crop=True,
    #     show_overlay=True
    # )
    # print(f"Match template {template_path} result: {result}")
    
    # Just output cropped image
    cropped_img = aligner.get_aligned_cropped(template_path, target_path)
    if cropped_img:
        cropped_img.show()


if __name__ == "__main__":
    import os
    import glob

    target_img_path = './template_alignment/target_1.png'
    image_folder = './template_alignment/test_images'
    
    # Get all PNG image paths in the folder
    image_paths = glob.glob(os.path.join(image_folder, '*.png'))
    print(image_paths)

    # Process each image in the folder
    for template_path in image_paths:
        print(template_path)
        test_align(template_path, target_img_path)
