import cv2
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from cvzone.HandTrackingModule import HandDetector
import time
import math

with open('params.json', 'r') as file:
    config_data = json.load(file)

with open(".cache", "r") as f:
    cached_token_info = json.load(f)

print(f"Token expiration: {cached_token_info['expires_at']}")

desired_fps = 30 
delay = int(1000 / desired_fps)
auth_manager = SpotifyOAuth(
    client_id=config_data.get("CLIENT_ID"),
    client_secret=config_data.get("CLIENT_SECRET"),
    redirect_uri="http://localhost:3000",
    scope="user-read-playback-state user-library-modify user-modify-playback-state user-library-read app-remote-control user-read-private user-read-email playlist-read-private user-library-modify streaming user-read-recently-played user-modify-playback-state user-read-playback-state "
)

sp = spotipy.Spotify(auth_manager=auth_manager)

cap = cv2.VideoCapture(0)
detector = HandDetector(
    staticMode=False, maxHands=2, modelComplexity=1, detectionCon=0.8, minTrackCon=0.5
)

finger_info_timer = time.time()
finger_info_interval = 3

while True:
    try:
        success, img = cap.read()
        hands, img = detector.findHands(img, draw=True, flipType=True)

        if time.time() - finger_info_timer >= finger_info_interval:
            finger_info_timer = time.time()

            if hands:
                hand1 = hands[0]
                if hand1["type"] == "Right":
                    pos = detector.fingersUp(hand1)
                    print(f"Right Hand Finger Positions: {pos}")

                    if pos == [0, 0, 0, 0, 0] or pos == [1, 0, 0, 0, 0]:
                        if auth_manager.is_token_expired(
                            sp.auth_manager.get_access_token()
                        ):
                            sp.auth_manager.refresh_access_token(
                                sp.auth_manager.get_access_token()["refresh_token"]
                            )
                        current_playback = sp.current_playback()
                        if current_playback and current_playback["is_playing"]:
                            try:
                                sp.pause_playback()
                                print("Song paused successfully!")
                            except Exception as e:
                                print(f"Error pausing playback: {e}")
                        else:
                            print("Song is not currently playing.")
                    elif pos == [1, 1, 1, 1, 1] or pos == [0, 1, 1, 1, 1]:
                        if auth_manager.is_token_expired(
                            sp.auth_manager.get_access_token()
                        ):
                            sp.auth_manager.refresh_access_token(
                                sp.auth_manager.get_access_token()["refresh_token"]
                            )
                        current_playback = sp.current_playback()
                        if current_playback and not current_playback["is_playing"]:
                            try:
                                sp.start_playback()
                                print("Song resumed successfully!")
                            except Exception as e:
                                print(f"Error resuming playback: {e}")
                        else:
                            print("Song is already playing.")

                    thumb_tip = hand1["lmList"][4]
                    index_tip = hand1["lmList"][8]
                    distance = math.dist(thumb_tip, index_tip)
                    print(distance)
                    threshold =70
                    if distance>threshold:
                        volume = int((distance - 50) / 2)
                        volume = max(0, min(100, volume))

                        print(f"Pinch Distance: {distance}, Adjusted Volume: {volume}")
                        sp.volume(volume)

                if hand1["type"] == "Left":
                    pos2 = detector.fingersUp(hand1)
                    print(f"Left Hand Finger Positions: {pos2}")
                    if pos2 == [0, 0, 0, 0, 0]:
                        sp.previous_track()
                    elif pos2 == [1, 1, 1, 1, 1] or pos2 == [0, 1, 1, 1, 1]:
                        sp.next_track()
                    elif (
                        pos2 == [1, 0, 0, 0, 0]
                        or pos2 == [1, 0, 0, 0, 1]
                        or pos2 == [0, 0, 0, 0, 1]
                    ):
                        current_Track = sp.current_playback()
                        if current_Track:
                            track_id = current_Track["item"]["id"]
                            sp.current_user_saved_tracks_add(tracks=[track_id])
                            print(
                                f"added current track to your music library.\n"
                            )
                    current_Track = sp.current_playback()
                    print(
                        f"\ncurrent song: {current_Track['item']['name']}\n"
                    )

            print(" ")
        # cv2.imshow("Image", img)
        cv2.waitKey(1)

    except Exception as e:
        print(f"An error occurred: {e}")
