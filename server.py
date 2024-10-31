from flask import Flask, jsonify ,request 
from flask_cors import CORS
from basketball_analyzer import process
import threading
from store_manager import Database
import time 
import os

app = Flask(__name__)
CORS(app)
db = Database()
@app.route("/")
def webpage():
  return jsonify({"name" : "hello"})

@app.route("/analyze",methods = ["POST","GET"])
def analyze():
  user_id = request.form.get("user_id")
  video = request.files.get("video")
  print(user_id)
  print(video)
  if not user_id:
    return jsonify({"error" : "there is no user_id"}),400
  if not video:
    return jsonify({"error" : "there is no video"}),400
  video_path = (video.filename)
  video.save(video_path)
  thread = threading.Thread(target=start_model , args=(video_path,user_id))
  thread.start()
  return jsonify({"message" : "video process started"})

def start_model(video_path,user_id):
  data = process(video_path, db,user_id)
  timestamp = time.time()

  # Delete original video to save space on computer
  if os.path.isfile(video_path):
    os.remove(video_path)

  db.update_firestore("basketball", user_id , data={'is_processing': False, str(timestamp) :data})

if __name__ == '__main__':
  app.run(host='0.0.0.0')
  # thread = threading.Thread(target=start_model , args=("./assets/basketball.mp4",0))
  # thread.start()



