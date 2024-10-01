


# TODO
def adjust_thresholds_by_resolution():
    """
    Adjust the thresholds for matching by image resolution
    """
    pass


# This algo needs optimized, now is O(n^2)
def associate_labels_to_fields(label_coors, field_coors, h_threshold=150, v_threshold=20, d_threshold=200):
    """
    Compare the coordinates between OCR and OD bounding boxes and find the coresponding label text for each field

    Args:
    - label_coors: A list of label name and BBoxes coordinates (top-left) from OCR
    - field_coors: A list of field type and BBoxes coordinates (top-left) from Object Detection
    - h_threshold: Horizontal threshold
    - v_threshold: Vertical threshold
    - d_threshold: Distance threshold

    Return:
    - list: A list of tuple containing (label_name, field_type, coor_x, coor_y) for each associated candidate.
    """
    associations = []
    for field_type, field_x, field_y in field_coors:
        candidates = []
        for label_name, label_x, label_y in label_coors:
            # Calculate horizontal and vertical distances using top-left coordinates
            horizontal_distance = field_x - label_x
            vertical_distance = field_y - label_y

            # Check label to the Left of Field:
            if 0 <= horizontal_distance <= h_threshold and abs(vertical_distance) <= v_threshold:
                # Compute Euclidean distance using top-left coordinates
                distance = ((horizontal_distance) ** 2 + (vertical_distance) ** 2) ** 0.5
                if distance <= d_threshold:
                    candidates.append((distance, field_x, field_y, label_name))
            # Also check label above the field
            elif 0 <= vertical_distance <= v_threshold and abs(horizontal_distance) <= h_threshold:
                distance = ((horizontal_distance) ** 2 + (vertical_distance) ** 2) ** 0.5
                if distance <= d_threshold:
                    candidates.append((distance, field_x, field_y, label_name))

        if candidates:
            # Select the label with the minimum distance
            dist, coor_x, coor_y, associated_label = min(candidates, key=lambda x: x[0])
            associations.append((associated_label, field_type, coor_x, coor_y))

    return associations



if __name__ == "__main__":
    pass