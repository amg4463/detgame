import asyncio
import cv2
import mediapipe as mp
import websockets
import json
import pyautogui
import time

time.sleep(3)  
pyautogui.click(x=100, y=100)  # Click on the target application window

mp_pose = mp.solutions.pose

GESTURE_ACTIONS = {
    "T-POSE": "w",  
    "BEND_LEFT": "a",  
    "BEND_RIGHT": "d"  
}

active_key = None  # Track the currently pressed key

async def detect_and_control():
    global active_key  
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not detected!")
        return

    pose = mp_pose.Pose()

    async with websockets.serve(websocket_handler, "localhost", 9000):
        print(" WebSocket Server started at ws://localhost:9000")

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            height, width, _ = frame.shape

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)

            gesture = detect_gesture(results, height, width)

            if gesture != "NONE":
                cv2.putText(frame, f"Detected: {gesture}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            bend_threshold = int(height * 0.7)
            cv2.line(frame, (0, bend_threshold), (width, bend_threshold), (0, 0, 255), 2)
            cv2.putText(frame, "Bend Threshold", (10, bend_threshold - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # **KEYBOARD CONTROL LOGIC**
            if gesture in GESTURE_ACTIONS:
                key = GESTURE_ACTIONS[gesture]
                if key != active_key:  # If the gesture changed
                    if active_key:  
                        pyautogui.keyUp(active_key)  # Release the previous key
                        print(f" Released {active_key}")
                    pyautogui.keyDown(key)  # Press the new key
                    active_key = key
                    print(f"🎮 Holding {key} (Gesture: {gesture})")
            else:
                if active_key:  # Release the key when no gesture is detected
                    pyautogui.keyUp(active_key)
                    print(f" Released {active_key}")
                    active_key = None  

            cv2.imshow("Gesture Control", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
    cap.release()
    cv2.destroyAllWindows()

def detect_gesture(results, height, width):
    if not results.pose_landmarks:
        return "NONE"

    landmarks = results.pose_landmarks.landmark
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

    # **T-Pose Detection**
    arm_span = abs(left_wrist.x - right_wrist.x)
    shoulder_span = abs(left_shoulder.x - right_shoulder.x)

    if arm_span > 1.2 * shoulder_span*1.5:
        print("🟢 Detected T-POSE")
        return "T-POSE"

    # **Bend Detection**
    hip_y_avg = (left_hip.y + right_hip.y) / 2  # Get average hip position
    nose_x = nose.x

    if hip_y_avg > 0.75:  # Ensure the person is bending
        if nose_x < 0.45:  # Nose is left
            print("🟢 Detected BEND_LEFT")
            return "BEND_LEFT"
        elif nose_x > 0.55:  # Nose is right
            print("🟢 Detected BEND_RIGHT")
            return "BEND_RIGHT"

    return "NONE"

async def websocket_handler(websocket, path):
    global active_key
    while True:
        try:
            message = await websocket.recv()
            data = json.loads(message)
            gesture = data.get("gesture", "NONE")
            print(f"📥 Received Gesture: {gesture}")

            if gesture in GESTURE_ACTIONS:
                key = GESTURE_ACTIONS[gesture]
                if key != active_key:
                    if active_key:
                        pyautogui.keyUp(active_key)  # Release previous key
                        print(f"Released {active_key}")
                    pyautogui.keyDown(key)  # Press new key
                    active_key = key
                    print(f"🎮 Holding {key} (Gesture: {gesture})")
            else:
                if active_key:
                    pyautogui.keyUp(active_key)
                    print(f" Released {active_key}")
                    active_key = None

        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket Disconnected")
            break

asyncio.run(detect_and_control())
