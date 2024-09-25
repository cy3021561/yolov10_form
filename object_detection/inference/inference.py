import cv2
import pyautogui
from ultralytics import YOLOv10

def predict(chosen_model, img, classes=[], conf=0.5):
    """
    Do the object detection
    """
    if classes:
        results = chosen_model.predict(img, classes=classes, conf=conf)
    else:
        results = chosen_model.predict(img, conf=conf)

    return results


def map_coordinates(box, screen_w, screen_h, img_w, img_h, shift_x=5, shift_y=5):
    """
    Transform the images bbox coordinates on a screenshot scale

    Args:
    - box (ultralytics.engine.results.Boxes): YOLO bbox object
    - screen_w, screen_h (int, int): Screen width and height
    - img_w, img_h (int, int): Image width and height

    Returns:
    - tuple: (coordinate_x, coordinate_y)
    """
    # Access the bounding boxes in xyxy format
    xyxy_boxes = box.xyxy

    # Extract top-left coordinates
    x_top_left = xyxy_boxes[:, 0]
    y_top_left = xyxy_boxes[:, 1]

    # Adjust for screen scaling
    scale_x = screen_w / img_w
    scale_y = screen_h / img_h
    adjusted_x_top_left = x_top_left * scale_x
    adjusted_y_top_left = y_top_left * scale_y

    return int(adjusted_x_top_left) + shift_x, int(adjusted_y_top_left) + shift_y


def get_bboxes_coordinates(chosen_model, img, classes=[], conf=0.5, rectangle_thickness=2, text_thickness=1):
    """
    Get the bbox coordinates based on screenshot scale for future cursor movements

    Args:
    - chosen_model (ultralytics.engine.model.Model): Loaded YOLO model object
    - img (np array): Input image loaded by cv2.imread()
    - class (list of str): A list of class names to filter predictions to
    - conf (float): The minimum confidence threshold for a prediction to be considered

    Returns:
    - tuple: (label_name, coordinate_x, coordinate_y)
    - np array: labeled images for doublechecking
    """
    results = predict(chosen_model, img, classes, conf=conf)
    screen_w, screen_h = pyautogui.size()
    img_h, img_w = results[0].boxes[0].orig_shape
    label_and_coors = []
    for result in results:
        for box in result.boxes:
            label_name = result.names[int(box.cls[0])]
            coor_x, coor_y = map_coordinates(box, screen_w, screen_h, img_w, img_h)
            label_and_coors.append((label_name, coor_x, coor_y))
            cv2.rectangle(img, (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
                          (int(box.xyxy[0][2]), int(box.xyxy[0][3])), (255, 0, 0), rectangle_thickness)
            cv2.putText(img, f"{result.names[int(box.cls[0])]}",
                        (int(box.xyxy[0][0]), int(box.xyxy[0][1]) - 10),
                        cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), text_thickness)
    return label_and_coors, img


if __name__ == "__main__":
    image_pth = "/Users/chun/Documents/Bridgent/yolov10_form/object_detection/train/aug_dataset_1/screenshot_test_1.png"
    image = cv2.imread(image_pth)
    model = YOLOv10("/Users/chun/Documents/Bridgent/yolov10_form/object_detection/weights/best_2.pt")
    label_and_coors, result_img = get_bboxes_coordinates(model, image, classes=[], conf=0.3)
    print(label_and_coors)
    cv2.imshow("Image", result_img)
    cv2.waitKey(0)