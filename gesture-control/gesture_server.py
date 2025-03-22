import asyncio
import cv2
import mediapipe as mp
import websockets
import json
import pyautogui
import time

time.sleep(3)
pyautogui.click(x=100, y=100)

mp_pose = mp.solutions.pose

GESTURE_ACTIONS = {
    "T-POSE": "w",
    "BEND_LEFT": "a",
    "BEND_RIGHT": "d",
    "LEFT_HAND_UP": "c",
    "RIGHT_HAND_UP": "z"
}

active_key = None

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

            # **KEYBOARD CONTROL LOGIC**
            if gesture in GESTURE_ACTIONS:
                key = GESTURE_ACTIONS[gesture]
                if key != active_key:
                    if active_key:
                        pyautogui.keyUp(active_key)
                        print(f" Released {active_key}")
                    pyautogui.keyDown(key)
                    active_key = key
                    print(f"🎮 Holding {key} (Gesture: {gesture})")
            else:
                if active_key:
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
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

    # **T-Pose Detection**
    arm_span = abs(left_wrist.x - right_wrist.x)
    shoulder_span = abs(left_shoulder.x - right_shoulder.x)

    if arm_span > 1.2 * shoulder_span * 1.5:
        print("🟢 Detected T-POSE")
        return "T-POSE"

    # **Bend Detection**
    hip_y_avg = (left_hip.y + right_hip.y) / 2
    nose_x = landmarks[mp_pose.PoseLandmark.NOSE].x

    if hip_y_avg > 0.75:
        if nose_x < 0.45:
            print("🟢 Detected BEND_LEFT")
            return "BEND_LEFT"
        elif nose_x > 0.55:
            print("🟢 Detected BEND_RIGHT")
            return "BEND_RIGHT"

    # **Left Hand Raised**
    if left_wrist.y < left_shoulder.y:
        print("🟢 Detected LEFT_HAND_UP")
        return "LEFT_HAND_UP"

    # **Right Hand Raised**
    if right_wrist.y < right_shoulder.y:
        print("🟢 Detected RIGHT_HAND_UP")
        return "RIGHT_HAND_UP"

    return "NONE"

async def websocket_handler(websocket, path):
    global active_key
    while True:
        try:
            message = await websocket.recv()
            data = json.loads(message)
            gesture = data.get("gesture", "NONE")
            print(f" Received Gesture: {gesture}")

            if gesture in GESTURE_ACTIONS:
                key = GESTURE_ACTIONS[gesture]
                if key != active_key:
                    if active_key:
                        pyautogui.keyUp(active_key)
                        print(f"Released {active_key}")
                    pyautogui.keyDown(key)
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
