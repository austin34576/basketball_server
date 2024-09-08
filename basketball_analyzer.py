from ultralytics import YOLO
import cv2
from PIL import Image
import torch

model = YOLO("best.pt")
model.info()
device = torch.device('cpu')
model.to(device)

def process(video_path):
    cap = cv2.VideoCapture(video_path)

    while True:
        ret, frame = cap.read()
        if ret:
            result = model(frame)
        else:
            break
