import pyautogui
import pyperclip
import time
import math


def add_delay(before=0.05, after=0.05):
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

def smooth_move_to(x, y, duration=0.2):
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
    
    def __init__(self, modifier_key=None, verbose=False):
        self.verbose = verbose
        self.modifier_key = modifier_key

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
            pyautogui.click(button=button, clicks=clicks, interval=interval)
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while clicking the mouse: {e}. "
            )
    
    @add_delay()
    def mouse_scroll(self, clicks):
        """
        Scrolls the mouse wheel up or down the specified number of clicks. Negative clicks value scroll down, vice versa.
        """
        try:
            pyautogui.scroll(clicks)
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while scrolling: {e}. "
            )
        
    @add_delay()
    def keyboard_write(self, text, interval=0.01, copy_paste=True):
        """
        Type out a string of characters with some realistic delay.
        """
        try:
            if not copy_paste:
                pyautogui.write(text, interval=interval)
            else:
                pyperclip.copy(text)
                # Paste
                self.keyboard_hotkey(self.modifier_key, 'v')
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while keyboard writing: {e}. "
            )

    @add_delay()
    def keyboard_press(self, button, presses=1, interval=0.1):
        """
        Press a key or a sequence of keys.

        If keys is a string, it is treated as a single key and is pressed the number of times specified by presses.
        If keys is a list, each key in the list is pressed once.
        """
        try:
            pyautogui.press(button, presses=presses, interval=interval)
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while keyboard pressing: {e}. "
            )
        
    @add_delay()
    def keyboard_hotkey(self, *args, interval=0.1):
        """
        Press a sequence of keys in the order they are provided, and then release them in reverse order.
        """
        try:
            pyautogui.hotkey(*args, interval=interval)
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while doing keyboard hotkey: {e}. "
            )
        
    def keyboard_release_all_keys(self):
        # List of common keys that might be held down
        keys_to_release = ['command', 'ctrl', 'alt', 'shift', 'win', 'enter', 'esc', 'fn']

        for key in keys_to_release:
            pyautogui.keyUp(key)