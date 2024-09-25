import os
import shutil
import random
from math import floor
import argparse

def split_dataset(dataset_dir, output_dir, train_percent, val_percent, test_percent):
    # Check if the sum of the percentages equals 100
    if train_percent + val_percent + test_percent != 100:
        raise ValueError("Train, val, and test percentages must sum to 100.")

    # Paths to images and labels
    images_dir = os.path.join(dataset_dir, 'images')
    labels_dir = os.path.join(dataset_dir, 'labels')

    # Get list of image files
    image_files = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
    image_files.sort()  # Sort to ensure consistent pairing

    # Shuffle the dataset
    random.shuffle(image_files)

    # Calculate split indices
    total_images = len(image_files)
    train_count = floor(total_images * train_percent / 100)
    val_count = floor(total_images * val_percent / 100)
    test_count = total_images - train_count - val_count  # Remaining images go to test

    # Split the dataset
    train_files = image_files[:train_count]
    val_files = image_files[train_count:train_count + val_count]
    test_files = image_files[train_count + val_count:]

    # Helper function to copy files
    def copy_files(file_list, subset):
        for file_name in file_list:
            # Copy image
            src_image = os.path.join(images_dir, file_name)
            dst_image_dir = os.path.join(output_dir, subset, 'images')
            os.makedirs(dst_image_dir, exist_ok=True)
            shutil.copy(src_image, dst_image_dir)

            # Copy corresponding label
            label_file = os.path.splitext(file_name)[0] + '.txt'
            src_label = os.path.join(labels_dir, label_file)
            dst_label_dir = os.path.join(output_dir, subset, 'labels')
            os.makedirs(dst_label_dir, exist_ok=True)

            if os.path.exists(src_label):
                shutil.copy(src_label, dst_label_dir)
            else:
                print(f"Warning: Label file {label_file} not found for image {file_name}.")

    # Copy files to respective directories
    copy_files(train_files, 'train')
    copy_files(val_files, 'val')
    copy_files(test_files, 'test')

    print("Dataset split completed successfully!")
    print(f"Total images: {total_images}")
    print(f"Training images: {len(train_files)}")
    print(f"Validation images: {len(val_files)}")
    print(f"Testing images: {len(test_files)}")


def generate_yaml(output_dir, class_file_path):
    try:
        import yaml
    except ImportError:
        print("PyYAML is not installed. Installing now...")
        os.system('pip install PyYAML')
        import yaml

    # Read classes.txt
    with open(class_file_path, 'r') as f:
        class_names = [line.strip() for line in f.readlines() if line.strip()]

    # Remove duplicates while preserving order
    class_names_no_duplicates = list(dict.fromkeys(class_names))
    if len(class_names) != len(class_names_no_duplicates):
        print("Warning: Duplicate class names found in classes.txt. Duplicates will be removed.")
        class_names = class_names_no_duplicates

    nc = len(class_names)

    # Prepare data for yaml
    data = {
        'train': os.path.abspath(os.path.join(output_dir, 'train', 'images')),
        'val': os.path.abspath(os.path.join(output_dir, 'val', 'images')),
        'nc': nc,
        'names': class_names
    }

    # Write yaml file with proper formatting
    yaml_file_path = os.path.join(output_dir, 'data.yaml')
    with open(yaml_file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=None, sort_keys=False)

    print(f"Config yaml file generated at {yaml_file_path}")

# Usage
# python object_detection/utils/split_dataset.py --dataset_dir object_detection/raw_dataset --output_dir object_detection/train/dataset_1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split dataset into train, val, and test sets, and generate YOLOv10 config yaml.")
    parser.add_argument('--dataset_dir', type=str, default='dataset', help='Path to the dataset directory.')
    parser.add_argument('--output_dir', type=str, default='new_dataset', help='Path to the output directory.')
    parser.add_argument('--train', type=int, default=70, help='Percentage of training data.')
    parser.add_argument('--val', type=int, default=20, help='Percentage of validation data.')
    parser.add_argument('--test', type=int, default=10, help='Percentage of testing data.')
    parser.add_argument('--classes_file', type=str, default='classes.txt', help='Path to the classes.txt file.')

    args = parser.parse_args()

    split_dataset(args.dataset_dir, args.output_dir, args.train, args.val, args.test)

    # Generate the YAML config file
    class_file_path = os.path.join(args.dataset_dir, args.classes_file)
    if os.path.exists(class_file_path):
        generate_yaml(args.output_dir, class_file_path)
    else:
        print(f"Error: classes.txt file not found at {class_file_path}. Cannot generate config yaml.")
