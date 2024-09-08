from ultralytics import YOLO
import cv2
from PIL import Image
import torch
from ultralytics.utils.plotting import Annotator
import os
from pathlib import Path

model = YOLO("best.pt")

# Detects object and if they made it
def detect_object(image):
    result = model(image, show = True)
    annotator = Annotator(image)
    made = False
    for r in result:
        boxes = r.boxes
        for box in boxes:
            class_name = model.names[int(box.cls)]
            if class_name == "made":
                made = True
    image = annotator.result()
    return image,made
# Resize image (to speed up the model)
def resize_image(image):
    h,w,_ = image.shape
    w = w//3
    h = h//3
    image = cv2.resize(image,(w,h))
    return image,h,w

# Resize to original (to upload to Firebase)
def resize_original(image, w, h):
    pass

def make_directory(name: str):
    # Check if the directory exists; if not, create it
    if not os.path.isdir(name):
        os.mkdir(name)

# Create the output video
def setup_video_tool(cap, video_path):
    make_directory("output")
    # Get the video frame dimensions
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 20
    output_path = f"output/{Path(video_path).stem}.mp4"
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), int(fps), (int(width), int(height)))
    return width,height,out,output_path
def put_text(frame, text, org):
    pass

# Get the stats and put it on the frame
def write_scores(frame, left, right, score):
    pass

def update_score(frame, current_time, left, right, person_pos, score, scores, w):
    pass


def process(video_path):
    cap = cv2.VideoCapture(video_path)
    width,height,out,output_path = setup_video_tool(cap,video_path)
    while True:
        ret, frame = cap.read()
        if ret:
            image,w,h = resize_image(frame)
            image,made = detect_object(image)
            out.write(image)
        else:
            break
    cap.release()
    out.release()

process("./assets/basketball.mp4")