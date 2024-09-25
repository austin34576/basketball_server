from ultralytics import YOLO
import cv2
from PIL import Image
import torch
from ultralytics.utils.plotting import Annotator
import os
from pathlib import Path
from store_manager import Database

    # Define color mapping for each class recognized in the basketball analysis
class_colors = {
    "ball": (255, 0, 0),  # Red for basketball
    "made": (0,128,0),  # Green for successful shots
    "person": (0,0,255),  # Blue for players
    "rim": (255,255,0),# Yellow for the rim
    "shoot": (241,178,220) # Magenta for shooting actions
}

model = YOLO("best.pt")

# Detects object and if they made it
def detect_object(image):
    result = model(image)
    annotator = Annotator(image)
    made = False
    player_centers = []
    for r in result:
        boxes = r.boxes
        for box in boxes:
            class_name = model.names[int(box.cls)]
            box_coords = box.xyxy[0]
            if class_name == "made":
                made = True
            if class_name == "shoot" or class_name == "person":
                center = int((box_coords[0] + box_coords[2])/2)
                player_centers.append(center)
            annotator.box_label(box_coords,class_name,class_colors[class_name])
    image = annotator.result()
    return image,made,player_centers
# Resize image (to speed up the model)
def resize_image(image):
    h,w,_ = image.shape
    w = w//2
    h = h//2
    image = cv2.resize(image,(w,h))
    return image,w,h

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

def resize_original(image, w, h):
# Resize the image back to its original dimensions
    image = cv2.resize(image, (w, h))
    return image


# Look at comments to see what you need to change
def put_text(image, text, org):
    # “text” is what will appear on the screen
    # “org” is the location of the text in pixels, for example if org=(50,50) the text would be placed 50 pixels right, and 50 pixels down
    # Specify font style
    font = cv2.FONT_HERSHEY_SIMPLEX
    # Specify font scale
    font_scale = 1
    # Define color of the text using RGB (replace R,G,B with the values of the color you want)
    color = (0, 0, 0)
    # Define thickness of the text
    thickness = 2
    # Add the text to the image
    image = cv2.putText(image, text, org, font, font_scale, color, thickness, cv2.LINE_AA)
    return image





# Get the stats and put it on the image
def write_scores(image, score,left,right):
    image = put_text(image, "total score" + str(score), (20,20)) # Total score
    image = put_text(image, "right score" + str(right), (440,20)) # Total score
    image = put_text(image, "left score" + str(left), (250,20)) # Total score

    return image


def update_score(score,player_centers,w,left,right):
	# Update the score by 1 and return the score
    score += 1
    if player_centers[0] <= w//2:
        left += 1
    else:
        right += 1
    return score,left,right
    
def process(video_path, db):
    cap = cv2.VideoCapture(video_path)
    width,height,out,output_path = setup_video_tool(cap,video_path)
    score = 0
    right = 0
    left = 0
    frams_pass = 0
    max_time = 100
    while True:
        ret, frame = cap.read()
        if ret:
            image,w,h = resize_image(frame)
            image,made,player_centers = detect_object(image)
            if made and frams_pass >= max_time:
                frams_pass =0
                score,left,right = update_score(score,player_centers,w,left,right)
            else:
                frams_pass += 1
                


            image = write_scores(image,score,left,right)

            # TODO: IMPORTANT: This fixes the video corrupted error, you need to resize video to the original size using resize_original()
            image = resize_original(image,width,height)

		    # This will write the image to the video
            out.write(image)
        else:
            break
    cap.release()
    out.release()

    url = db.upload_file(output_path,output_path)
    print(url)
    return {"url": url,"score":score,"left":left,"right":right}