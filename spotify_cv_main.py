import cv2
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from cvzone.HandTrackingModule import HandDetector
import time
import math
with open('params.json', 'r') as file:
    config_data = json.load(file)

desired_fps = 10
delay = int(1000 / desired_fps)
auth_manager = SpotifyOAuth(client_id=config_data.get("CLIENT_ID"), client_secret=config_data.get("CLIENT_SECRET"), redirect_uri="http://localhost:3000", scope="user-read-playback-state user-library-modify user-modify-playback-state user-library-read app-remote-control user-read-private user-read-email playlist-read-private user-library-modify streaming user-read-recently-played")

sp = spotipy.Spotify(auth_manager=auth_manager)

if auth_manager.is_token_expired(sp.auth_manager.get_access_token()):
    sp.auth_manager.refresh_access_token(sp.auth_manager.get_access_token()["refresh_token"])

cap = cv2.VideoCapture(0)
detector = HandDetector(staticMode=False, maxHands=2, modelComplexity=1, detectionCon=0.8, minTrackCon=0.5)

finger_info_timer = time.time()
finger_info_interval = 5 

volume_control_active = False
thumbs_up_detected = False
pinch_threshold =40

while True:
    try:
        success, img = cap.read()
        hands, img = detector.findHands(img, draw=True, flipType=True)

        if time.time() - finger_info_timer >= finger_info_interval:
            finger_info_timer = time.time()

            if hands:
                hand1 = hands[0]
                if hand1["type"] == 'Right':
                    pos = detector.fingersUp(hand1)
                    print(f"Right Hand Finger Positions: {pos}")

                    if pos == [0, 0, 0, 0, 0] or [1,0,0,0,0]:    
                        sp.pause_playback()
                    elif pos == [1, 1, 1, 1, 1] or pos == [0, 1, 1, 1, 1]:
                        sp.start_playback()
                    thumb_tip = hand1["lmList"][4]  
                    index_tip = hand1["lmList"][8]  
                    distance = math.dist(thumb_tip, index_tip)
                    volume = int((distance - 50) / 2)
                    volume = max(0, min(100, volume))
                    
                    print(f"Pinch Distance: {distance}, Adjusted Volume: {volume}")
                    sp.volume(volume)
            # if len(hands) == 2:
            #     hand2 = hands[1]  
                if hand1["type"] == 'Left':
                    pos2 = detector.fingersUp(hand1)
                    print(f"Left Hand Finger Positions: {pos2}")
                    if pos2 == [0, 0, 0, 0, 0]:
                        sp.previous_track()
                    elif pos2 == [1, 1, 1, 1, 1] or pos2 == [0, 1, 1, 1, 1]:
                        sp.next_track()
                    elif pos2==[1,0,0,0,0] or pos2==[1,0,0,0,1]or pos2==[0,0,0,0,1]:
                        current_Track=sp.current_playback()
                        if current_Track:
                            track_id=current_Track['item']['id']
                            sp.current_user_saved_tracks_add(tracks=[track_id])
                            print(f"added current track to ur music library.\n")
                    current_Track=sp.current_playback()
                    print(f"\ncurrent song: {current_Track['item']['name']}\n")
            print(" ")
        cv2.imshow("Image", img)
        cv2.waitKey(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        

