import cv2
import pyautogui
import numpy as np
import math
import time


class TemplateAligner:
    FLANN_INDEX_KDTREE = 1
    MIN_MATCH_COUNT = 100
    DEFAULT_TEMPLATE_MATCHING_THRESHOLD = 0.6

    def __init__(self, debug=False, screen_width=None, screen_height=None):
        self.debug = debug
        self.screen_width, self.screen_height = self._get_screen_dimensions(screen_width, screen_height)
        self.sift = self._initialize_sift()
        self.flann = self._initialize_flann()
        self.template_matching_threshold = self.DEFAULT_TEMPLATE_MATCHING_THRESHOLD

    def _show_image(self, np_image):
        cv2.imshow("tmp", np_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    def _get_screen_dimensions(self, screen_w, screen_h):
        if screen_w is not None and screen_h is not None:
            return screen_w, screen_h
        return pyautogui.size()

    def _initialize_sift(self):
        return cv2.SIFT_create()

    def _initialize_flann(self):
        index_params = dict(algorithm=self.FLANN_INDEX_KDTREE, trees=20)
        search_params = dict(checks=100)
        return cv2.FlannBasedMatcher(index_params, search_params)

    def template_match(self, screenshot_img, template_img):
        result = cv2.matchTemplate(screenshot_img, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return max_val, max_loc

    def get_screenshot(self):
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)
        return screenshot_gray

    def get_screen_coordinates(self, screenshot_image, coor_x, coor_y):
        img_width, img_height = screenshot_image.shape[::-1]
        scale_x = img_width / self.screen_width
        scale_y = img_height / self.screen_height

        # Scale the center coordinates
        scaled_center_x = int(coor_x / scale_x)
        scaled_center_y = int(coor_y / scale_y)

        return scaled_center_x, scaled_center_y

    def align(self, template_image_path):
        # Read Images
        template_img = cv2.imread(template_image_path, cv2.IMREAD_GRAYSCALE)
        screenshot_img = self.get_screenshot() # Need to update screenshot dymanicly in the future

        # Template matching
        max_val, max_loc = self.template_match(screenshot_img, template_img)
        print(max_val)

        if max_val < self.DEFAULT_TEMPLATE_MATCHING_THRESHOLD:
            print("No template matching found.")
        
        # # Show template matching result
        # w, h = template_img.shape[::-1]
        # top_left = max_loc
        # bot_right = (top_left[0] + w, top_left[1] + h)
        # cv2.rectangle(screenshot_img, top_left, bot_right, 0, 5)
        # cv2.circle(screenshot_img, (top_left[0] + w // 2, top_left[1] + h // 2), 10, (0, 0, 0), 3)
        # self._show_image(screenshot_img)

        # Get the desired coordinates
        w, h = template_img.shape[::-1]
        scaled_x, scaled_y = self.get_screen_coordinates(screenshot_img, max_loc[0] + w // 2, max_loc[1] + h // 2)
        return scaled_x, scaled_y

def smooth_move_to(x, y, duration=2):
    start_x, start_y = pyautogui.position()
    dx = x - start_x
    dy = y - start_y

    start_time = time.time()

    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > duration:
            break

        t = elapsed_time / duration
        eased_t = (1 - math.cos(t * math.pi)) / 2  # easeInOutSine function

        target_x = start_x + dx * eased_t
        target_y = start_y + dy * eased_t
        pyautogui.moveTo(target_x, target_y)

    # Ensure the mouse ends up exactly at the target (x, y)
    pyautogui.moveTo(x, y)

def test_align(template_path):
    aligner = TemplateAligner()
    scaled_x, scaled_y = aligner.align(template_path)
    print(scaled_x, scaled_y)
    smooth_move_to(scaled_x, scaled_y)


if __name__ == "__main__":
    import os
    import glob

    image_folder = './images'
    image_paths = glob.glob(os.path.join(image_folder, '*.png'))

    # Process each image
    for template_path in image_paths:
        print(template_path)
        test_align(template_path)

