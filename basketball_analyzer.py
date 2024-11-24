from ultralytics import YOLO
import cv2
from PIL import Image
import torch
from ultralytics.utils.plotting import Annotator
import os
from pathlib import Path
from store_manager import Database
import imageio

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
    shoot = False
    player_centers = []
    ball_centers = []
    for r in result:
        boxes = r.boxes
        for box in boxes:
            class_name = model.names[int(box.cls)]
            box_coords = box.xyxy[0] # get box coords in (left, top, right, bottom) format
            if class_name == "made":
                made = True
            if class_name == "shoot" or class_name == "person":
                if class_name == "shoot":
                    shoot = True
                center = int((box_coords[0] + box_coords[2])/2)
                player_centers.append(center)
            if class_name == "ball":
                x_center = int((box_coords[0] + box_coords[2])/2)
                y_center = int((box_coords[1] + box_coords[3])/2)
                ball_centers.append([x_center, y_center])

            # annotator.box_label(box_coords,class_name,class_colors[class_name])

    # image = annotator.result()
    return image,made,player_centers,shoot, ball_centers
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
    make_directory("image")
    # Get the video frame dimensions
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 30
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
def write_scores(image, score,left,right,miss):
    # image = put_text(image, "total score" + str(score), (20,20)) # Total score
    # image = put_text(image, "right score" + str(right), (440,20)) # Total score
    # image = put_text(image, "left score" + str(left), (250,20)) # Total score
    # image = put_text(image, "left miss" + str(miss[0]), (20,100))
    # image = put_text(image, "right miss" + str(miss[1]), (20,150))
    return image


def update_score(score,player_centers,w,left,right):
	# Update the score by 1 and return the score
    score += 1
    if player_centers[0] <= w//2:
        left += 1
    else:
        right += 1
    return score,left,right

def update_miss(miss,player_centers,w):
    if player_centers:
        if player_centers[0] <= w//2:
            miss[0] += 1
        else:
            miss[1] += 1
    return miss

def snapshot(made,current_time, images, video_path, db):
    imageio.mimsave(f"output/output.gif",images, loop=0, duration=10)
    #print(type(images[0]))
    #gif = Image.open(images[0])
    #gif.save("output/output.gif", save_all=True, append_images=images[1:], duration=1000, loop=0)
    url = db.upload_file(f"output/{Path(video_path).stem}{current_time}.gif",f"output/output.gif")
    return {
        "made" : made,
        "url" : url,
        "time" : current_time
    }

def process(video_path, db, user_id):
    db.update_firestore("basketball", user_id , data={'progress': int(0) })
    cap = cv2.VideoCapture(video_path)
    width,height,out,output_path = setup_video_tool(cap,video_path)
    snapshots = [] # List of each of the made/missed images
    images = []
    trail = []

    score = 0
    right = 0
    left = 0
    miss = [0,0]

    frams_pass = 0
    shoot_frame = 0
    shoot_time = 80
    max_time = 20
    total_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    progress_frame = 0


    while True:
        ret, frame = cap.read()
        if ret:
            current_time = cap.get(cv2.CAP_PROP_POS_MSEC)
            image,w,h = resize_image(frame)
            image,made,player_centers,shoot,ball_centers = detect_object(image)
            if made:
                shoot_frame = 0
                if frams_pass >= max_time:
                    frams_pass = 0
                    score,left,right = update_score(score,player_centers,w,left,right)
                    if images:
                        snapshots.append(snapshot(True,current_time,images, video_path, db))
                    images = []
                    trail = []
            else:
                frams_pass += 1
            if shoot_frame >= shoot_time:
                miss = update_miss(miss,player_centers,w)
                snapshots.append(snapshot(False,current_time,images, video_path, db))
                images = []
                trail = []
                shoot_frame = 0
            elif shoot or shoot_frame > 0:
                if ball_centers:
                    trail.append([ball_centers[0][0], ball_centers[0][1]])
                for dot in trail:
                    cv2.circle(image,(dot[0], dot[1]), radius = 3, color = (0, 255, 0), thickness = -1)
                images.append(image)
                shoot_frame +=1
            progress_frame += 1

            
            db.update_firestore("basketball", user_id , data={'progress': int(progress_frame/ total_frame * 100) })


            image = write_scores(image,score,left,right,miss)
            # TODO: IMPORTANT: This fixes the video corrupted error, you need to resize video to the original size using resize_original()
            image = resize_original(image,width,height)

		    # This will write the image to the video
            out.write(image)
        else:
            break
    cap.release()
    out.release()

    url = db.upload_file(output_path,output_path) # Model video
    org_url = db.upload_file(f"assets/{video_path}",video_path) # original video
    print(url)
    print(org_url)
    return {"url": url, "org_url":org_url, "score":score,"left":left,"right":right,"miss":miss, "snapshots": snapshots}