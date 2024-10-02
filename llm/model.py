from object_detection.inference import get_bboxes_coordinates
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ocr.find_cor_test import locate_all_text_on_screen
from llm.field_match import associate_labels_to_fields
import pyautogui
import cv2
import json
import base64


def read_page_json(json_path):
    """
    """
    with open(json_path, 'r') as file:
        data = json.load(file)

    return data


def split_image_vertically(img, num_splits=4, overlap_ratio=0.1):
    """
    Vertically splits an image into the specified number of parts with overlap.

    Args:
    - img (np.ndarray): The input image to split.
    - num_splits (int): Number of vertical parts to split the image into.
    - overlap_ratio (float): Ratio of overlap between consecutive splits (0.0 to 1.0).

    Returns:
    - list of np.ndarray: A list of image parts.
    """
    # Get the image dimensions
    img_h, img_w = img.shape[:2]
    
    # Calculate the height of each split, including overlap
    split_height = img_h // num_splits
    overlap = int(split_height * overlap_ratio)
    
    # Store the sub-images
    image_parts = []

    for i in range(num_splits):
        # Calculate the starting and ending y-coordinates for the split
        start_y = max(0, i * split_height - overlap)
        end_y = min(img_h, (i + 1) * split_height + overlap)
        
        # Crop the sub-image
        image_part = img[start_y:end_y, :]
        image_parts.append(image_part)

    return image_parts


def draw_candidates_on_image(image, candidates):
    """
    Draws a dot on the image at (coor_x, coor_y) for each candidate and labels it with (label_name, label_type).
    Adjusts the coordinates based on the screen size.

    Args:
        image (numpy.ndarray): The image on which to draw.
        candidates (list of tuples): List of (label_name, label_type, coor_x, coor_y).

    Returns:
        numpy.ndarray: The image with dots and labels drawn.
    """
    import cv2

    # Get the screen size using pyautogui
    screen_width, screen_height = pyautogui.size()

    # Get the dimensions of the image
    image_height, image_width = image.shape[:2]

    # Calculate the scale factors
    x_scale = image_width / screen_width
    y_scale = image_height / screen_height

    # Create a copy of the image to draw on
    image_with_dots = image.copy()

    for candidate in candidates:
        label_name, label_type, coor_x, coor_y = candidate

        # Transform the coordinates to the image size
        img_x = int(coor_x * x_scale)
        img_y = int(coor_y * y_scale)

        # Draw a small circle (dot) at the transformed coordinates
        dot_radius = 5  # Radius of the dot
        dot_color = (0, 0, 255)  # Red color in BGR
        cv2.circle(image_with_dots, (img_x, img_y), dot_radius, dot_color, -1)

        # Prepare the label text
        label_text = f"{label_name}, {label_type}"

        # Put the text near the dot
        text_position = (img_x + 10, img_y - 10)  # Adjust offset as needed
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_color = (0, 0, 255)  # Same color as the dot
        thickness = 1
        cv2.putText(image_with_dots, label_text, text_position, font, font_scale, font_color, thickness, cv2.LINE_AA)

    return image_with_dots


def generate_prompt(np_img, prompt_message, exist_column_dict):
    """
    Generate prompt based on the input image section
    """
    _, buffer = cv2.imencode('.png', np_img)
    image_data = base64.b64encode(buffer).decode('utf-8')
    message = [
        SystemMessage(content=prompt_message),
        HumanMessage(
            content=[
                {"type": "text", "text": f"**Existing Column Names:** {str(exist_column_dict)}"},
                {"type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                },
            ]
        ),
    ]
    return message


def test_call():
    pass

if __name__ == "__main__":
    import os
    from ultralytics import YOLOv10
    from dotenv import load_dotenv

    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)

    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    parser = JsonOutputParser()
    chain = llm | parser

    img_pth = "/Users/chun/Documents/Bridgent/yolov10_form/object_detection/train/aug_dataset_1/screenshot_test_1.png"
    img = cv2.imread(img_pth)
    model = YOLOv10("/Users/chun/Documents/Bridgent/yolov10_form/object_detection/weights/best.pt")
    field_coors, bboxes_img = get_bboxes_coordinates(model, img, classes=[], conf=0.8, save_img=True)
    img_parts = split_image_vertically(bboxes_img)
    prompt_messeage = """
    **Prompt:**  
    You are given an image and a JSON object containing existing column names for a web page. Your task is to identify the column name corresponding to each blue bounding box by its index. Follow these steps to update the JSON object:
    
    0. **If there's no any bounding box, just return the JSON object you got.
    1. **Identify the Bounding Box:** Use the provided index in the bounding box; do not create your own index.
    2. **Initial Search:** Look directly to the left of the bounding box to find text that matches an existing column name based on its meaning.
    3. **Extended Search:** If no match is found in the initial search, continue looking further to the left for additional context to identify the column name.
    4. **Handle Unmatched Cases:** If no match is found after both steps, assign `None` as the value for that bounding box.
    5. **Record the Result:** If a match is found, update the JSON object with the pair `{column_name: bbox_index}`.

    **Return:**  
    - You must **ONLY** return the updated JSON object containing column names and their corresponding bounding box indices.
    - If no matches are found or no updates are necessary, simply return the input JSON object as is.
    - Do not include any additional comments, explanations, or text outside of the JSON object in the response. 

    **Tips:**  
    - Aim to match the bounding boxes to the given column names as accurately as possible. If the text does not match an existing name, look leftward to deduce its association (e.g., if you see "End Date" and "Smoking" to its left, it could correspond to "Smoking End Date").
    - It is not required to match all bounding boxes. If some column names do not correspond to any bounding boxes, skip them.
    """


    # Read webpage json file
    existing_columns = read_page_json("/Users/chun/Documents/Bridgent/yolov10_form/llm/page_content_files/office_ally_patient.json")
    for i, part in enumerate(img_parts):
        mesg = generate_prompt(img_parts[i], prompt_messeage, existing_columns)
        response = chain.invoke(mesg)
        existing_columns = dict(response)
        print(f"Processing part {i+1}, result: {existing_columns}")
        # cv2.imshow(f"Image Part {i+1}", part)
        # cv2.waitKey(0)
    
    # cv2.destroyAllWindows()


    # # Match with ocr results    
    # label_coors, _ = locate_all_text_on_screen(img)
    # candidates = associate_labels_to_fields(label_coors, field_coors)
    # print(candidates)

    # # Draw candidates on the image
    # result_image = draw_candidates_on_image(img, candidates)

    # # Display the image
    # cv2.imwrite("matches_candidates.png", result_image)
    # cv2.imshow("Candidates", result_image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()