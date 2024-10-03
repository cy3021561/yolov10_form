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


def map_coordinates(box, screen_w, screen_h, img_w, img_h, shift_x=10, shift_y=10):
    """
    Transform the images bbox coordinates on a screenshot scale

    Args:
    - box (ultralytics.engine.results.Boxes): YOLO bbox object
    - screen_w, screen_h (int, int): Screen width and height
    - img_w, img_h (int, int): Image width and height
    - shift_x, shift_y (int, int): Shift value by pixel level, in order to let cursor click that field

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


def get_bboxes_coordinates(chosen_model, img, classes=[], conf=0.5, rectangle_thickness=2, save_img=False):
    """
    Get the bbox coordinates based on screenshot scale for future cursor movements

    Args:
    - chosen_model (ultralytics.engine.model.Model): Loaded YOLO model object
    - img (numpy.ndarray): Input image loaded by cv2.imread()
    - class (list of str): A list of class names to filter predictions to
    - conf (float): The minimum confidence threshold for a prediction to be considered

    Returns:
    - tuple: (label_name, coordinate_x, coordinate_y)
    - numpy.ndarray: labeled images for doublechecking
    """
    results = predict(chosen_model, img, classes, conf=conf)
    screen_w, screen_h = pyautogui.size()
    img_h, img_w = results[0].boxes[0].orig_shape
    label_and_coors = {}
    copy_img = img.copy()
    for result in results:
        for i, box in enumerate(result.boxes):
            label_type = result.names[int(box.cls[0])]
            coor_x, coor_y = map_coordinates(box, screen_w, screen_h, img_w, img_h)
            label_and_coors[str(i)] = (label_type, coor_x, coor_y)
            cv2.rectangle(copy_img, (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
                          (int(box.xyxy[0][2]), int(box.xyxy[0][3])), (255, 0, 0), rectangle_thickness)
            cv2.putText(copy_img, f"{i}",
                        (int(box.xyxy[0][0]) + 10, int(box.xyxy[0][1]) + 30),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 3)
            
    if save_img:
        output_path = "/Users/chun/Documents/Bridgent/yolov10_form/llm/output_image_1.png"  # Change this path as needed
        cv2.imwrite(output_path, copy_img)

    return label_and_coors, copy_img


if __name__ == "__main__":
    image_pth = "/Users/chun/Documents/Bridgent/yolov10_form/object_detection/train/aug_dataset_1/screenshot_test_2.png"
    image = cv2.imread(image_pth)
    model = YOLOv10("/Users/chun/Documents/Bridgent/yolov10_form/object_detection/weights/best.pt")
    label_and_coors, result_img = get_bboxes_coordinates(model, image, classes=[], conf=0.8)
    print(label_and_coors)
    # Save the image to a file
    
    output_path = "/Users/chun/Documents/Bridgent/yolov10_form/llm/output_image_2.png"
    cv2.imwrite(output_path, result_img)
    
    cv2.imshow("Image", result_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()