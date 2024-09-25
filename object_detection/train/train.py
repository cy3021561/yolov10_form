from ultralytics import YOLOv10


model = YOLOv10.from_pretrained('jameslahm/yolov10x')
model.train(data='/Users/chun/Documents/Bridgent/yolov10_form/object_detection/train/dataset_1/data.yaml', epochs=10, batch=4, imgsz=640)