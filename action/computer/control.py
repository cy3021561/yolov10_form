import pyautogui
import time
import math


def add_delay(before=0.3, after=0.3):
    """Decorator to add a delay before and after the execution of a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if before > 0:
                time.sleep(before)
            result = func(*args, **kwargs)
            if after > 0:
                time.sleep(after)
            return result
        return wrapper
    return decorator

def smooth_move_to(x, y, duration=2):
    start_x, start_y = pyautogui.position()
    dx = x - start_x
    dy = y - start_y
    distance = math.hypot(dx, dy)  # Calculate the distance in pixels

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


class Control:
    """A class to simulate human behavior."""
    
    def __init__(self, verbose=False):
        self.verbose = verbose

    @add_delay()
    def mouse_move(self, coor_x, coor_y, smooth=False):
        try:
            if smooth:
                smooth_move_to(coor_x, coor_y)
            else:
                pyautogui.moveTo(coor_x, coor_y)
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while moving the mouse to certain position: {e}. "
            )
        
    @add_delay()
    def mouse_click(self, button="left", clicks=1, interval=0.1):
        try:
            if self.verbose:
                print(f"Current mouse x and y: {pyautogui.position()}")
            pyautogui.click(button=button, clicks=clicks, interval=interval)
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while clicking the mouse: {e}. "
            )
        
    @add_delay()
    def keyboard_write(self):
        pass

    def screenshot(self):
        pass