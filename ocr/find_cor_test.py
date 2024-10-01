import pyautogui
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import re
from scipy.spatial import distance
from scipy.cluster import hierarchy

def get_screen_scaling_factor():
    actual_width, actual_height = pyautogui.size()
    screenshot = pyautogui.screenshot()
    screenshot_width, screenshot_height = screenshot.size
    width_scale = screenshot_width / actual_width
    height_scale = screenshot_height / actual_height
    return width_scale, height_scale

def custom_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    return screenshot_np

def is_valid_word(text):
    # Stricter criteria for valid words
    if len(text) < 2:  # Changed from <= 2
        return False
    if not re.search('[a-zA-Z]', text):
        return False
    if re.match(r'^\.\w+$', text):
        return False
    return True

def cluster_words(word_data, horizontal_threshold, vertical_threshold, max_cluster_size=5):
    def distance_metric(a, b):
        dx = abs(a[0] - b[0]) / horizontal_threshold
        dy = abs(a[1] - b[1]) / vertical_threshold
        return max(dx, dy * 0.5)  # Use max to be more sensitive to both dimensions

    positions = np.array([(w['left'], w['top']) for w in word_data])
    distances = distance.pdist(positions, metric=distance_metric)
    linkage = hierarchy.linkage(distances, method='single')
    clusters = hierarchy.fcluster(linkage, 2, criterion='distance')
    
    # Split large clusters
    for cluster_id in set(clusters):
        mask = clusters == cluster_id
        if np.sum(mask) > max_cluster_size:
            sub_positions = positions[mask]
            sub_distances = distance.pdist(sub_positions, metric=distance_metric)
            sub_linkage = hierarchy.linkage(sub_distances, method='single')
            sub_clusters = hierarchy.fcluster(sub_linkage, 0.5, criterion='distance')
            clusters[mask] = sub_clusters + max(clusters)
    
    return clusters

def locate_all_text_on_screen(image):
    import cv2
    import pytesseract

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    width_scale, height_scale = get_screen_scaling_factor()
    
    valid_words = []
    for i in range(len(data['text'])):
        if data['text'][i].strip() and is_valid_word(data['text'][i].strip()):
            valid_words.append({
                'text': data['text'][i],
                'left': data['left'][i],
                'top': data['top'][i],
                'width': data['width'][i],
                'height': data['height'][i]
            })
    
    # Cluster words based on their proximity
    word_clusters = cluster_words(valid_words, horizontal_threshold=80, vertical_threshold=5, max_cluster_size=5)
    
    text_locations = []
    scaled_coors = []
    for cluster_id in set(word_clusters):
        words_in_cluster = [valid_words[i] for i in range(len(valid_words)) if word_clusters[i] == cluster_id]
        words_in_cluster.sort(key=lambda w: (w['left'], w['top']))  # Sort words left-to-right, top-to-bottom
        
        phrase = ' '.join(word['text'] for word in words_in_cluster)
        x_min = min(word['left'] for word in words_in_cluster)
        y_min = min(word['top'] for word in words_in_cluster)
        x_max = max(word['left'] + word['width'] for word in words_in_cluster)
        y_max = max(word['top'] + word['height'] for word in words_in_cluster)
        
        # Calculate scaled top-left coordinates
        top_left_x = int(x_min / width_scale)
        top_left_y = int(y_min / height_scale)
        
        scaled_coor = {
            'x_min': top_left_x,
            'y_min': top_left_y,
            'x_max': int(x_max / width_scale),
            'y_max': int(y_max / height_scale)
        }
        
        # Append phrase and top-left coordinates
        text_locations.append((phrase, top_left_x, top_left_y))
        scaled_coors.append(scaled_coor)
    
    return text_locations, scaled_coors


def mark_text_on_image(image, text_locations, scaled_coors):
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    # Convert the image to RGB and create a PIL image for drawing
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    draw = ImageDraw.Draw(pil_image)
    
    # Load a font for drawing text
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font = ImageFont.load_default()

    width_scale, height_scale = get_screen_scaling_factor()

    for pair, coords in zip(text_locations, scaled_coors):
        text, coor_x, coor_y = pair
        # Scale the coordinates back to the original image size
        scaled_coords = {
            'x_min': int(coords['x_min'] * width_scale),
            'y_min': int(coords['y_min'] * height_scale),
            'x_max': int(coords['x_max'] * width_scale),
            'y_max': int(coords['y_max'] * height_scale)
        }
        # Draw a dot at the top-left coordinate
        dot_radius = 5  # Radius of the dot
        top_left_x = int(coor_x * width_scale)
        top_left_y = int(coor_y * height_scale)
        draw.ellipse([
            top_left_x - dot_radius, top_left_y - dot_radius,
            top_left_x + dot_radius, top_left_y + dot_radius
        ], fill="red", outline="red")
        # Optionally, draw the bounding box
        draw.rectangle([
            scaled_coords['x_min'], scaled_coords['y_min'], 
            scaled_coords['x_max'], scaled_coords['y_max']
        ], outline="blue", width=2)
        # Draw the text label
        label = f"{text} ({coor_x}, {coor_y})"
        draw.text((scaled_coords['x_min'], scaled_coords['y_min'] - 20), label, fill="red", font=font)

    # Convert back to a NumPy array and return
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


if __name__ == "__main__":
    # screen_image = custom_screenshot()
    image_pth = "/Users/chun/Documents/Bridgent/yolov10_form/object_detection/train/aug_dataset_1/screenshot_test_2.png"
    image = cv2.imread(image_pth)
    text_info, scales_coors = locate_all_text_on_screen(image)
    marked_image = mark_text_on_image(image, text_info, scales_coors)

    cv2.imwrite("tmp_marked_screenshot.png", cv2.cvtColor(marked_image, cv2.COLOR_RGB2BGR))

    print(f"Detected {len(text_info)} text items. Marked image saved as 'tmp_marked_screenshot.png'")

    for text, coor_x, coor_y in text_info:
        print(f"'{text}': {coor_x}, {coor_y}")

    print(f"Actual screen size: {pyautogui.size()}")
    print(f"Scaling factors: {get_screen_scaling_factor()}")