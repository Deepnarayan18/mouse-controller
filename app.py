import cv2
import time
import numpy as np
import mediapipe as mp
import pyautogui
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk  # Import Image and ImageTk from PIL

# Handle import error for pyautogui
try:
    import pyautogui
except ImportError:
    print("The 'pyautogui' module is not installed.")
    print("Attempting to install 'pyautogui'...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
    try:
        import pyautogui
    except ImportError:
        print("Failed to install 'pyautogui'. Please install it manually.")
        sys.exit(1)

# Function to initialize the camera
def initialize_camera():
    # Try multiple camera indices to find the correct one
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera index {i} opened successfully.")
            return cap
        cap.release()
    print("No available camera found.")
    sys.exit(1)

# Function to move mouse based on hand gesture
def move_mouse(x, y):
    try:
        screen_width, screen_height = pyautogui.size()
        # Inverting x coordinate because webcam image is a mirror image
        pyautogui.moveTo(screen_width - x, y)
    except Exception as e:
        print(f"Failed to move mouse: {e}")

# Function to update smoothening factor from slider
def update_smoothening(value):
    global smoothening
    smoothening = int(value)

# Initialize the camera
cap = initialize_camera()

# Set the width and height for the webcam feed
wCam, hCam = 1200, 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, wCam)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hCam)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Smoothening parameters
smoothening = 5
prev_loc_x, prev_loc_y = 0, 0

# Create tkinter window
root = tk.Tk()
root.title("Hand Gesture Mouse Control")

# Create a frame for webcam feed
frame_webcam = tk.Frame(root, width=wCam, height=hCam)
frame_webcam.pack()

# Function to update webcam frame
def update_webcam_frame():
    global prev_loc_x, prev_loc_y

    # Capture frame-by-frame
    success, img = cap.read()

    if success:
        # Convert the image to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                landmarks = hand_landmarks.landmark

                # Get the coordinates of the wrist (or another stable point)
                wrist = landmarks[mp_hands.HandLandmark.WRIST]

                # Convert normalized coordinates to pixel values
                h, w, c = img.shape
                wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)

                # Smoothen the values
                curr_loc_x = prev_loc_x + (wrist_x - prev_loc_x) / smoothening
                curr_loc_y = prev_loc_y + (wrist_y - prev_loc_y) / smoothening

                # Move the mouse cursor to the smoothened position
                move_mouse(curr_loc_x, curr_loc_y)

                prev_loc_x, prev_loc_y = curr_loc_x, curr_loc_y

        # Convert OpenCV image to PIL format and then to tkinter format
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (wCam, hCam))
        img = Image.fromarray(img)
        img_tk = ImageTk.PhotoImage(image=img)
        label_webcam.img_tk = img_tk  # Keep a reference to avoid garbage collection
        label_webcam.config(image=img_tk)
    
    # Call this function again after 10ms
    label_webcam.after(10, update_webcam_frame)

# Label to display webcam feed
label_webcam = tk.Label(frame_webcam)
label_webcam.pack()

# Frame for controlling parameters
frame_controls = tk.Frame(root)
frame_controls.pack()

# Smoothening slider
lbl_smoothening = tk.Label(frame_controls, text="Smoothening Factor:")
lbl_smoothening.pack(side=tk.LEFT, padx=10)
scale_smoothening = tk.Scale(frame_controls, from_=1, to=20, orient=tk.HORIZONTAL, command=update_smoothening)
scale_smoothening.pack(side=tk.LEFT, padx=10)
scale_smoothening.set(smoothening)

# Exit button
btn_exit = tk.Button(frame_controls, text="Exit", command=root.quit)
btn_exit.pack(side=tk.RIGHT, padx=10)

# Start updating webcam frame
update_webcam_frame()

# Start the tkinter main loop
root.mainloop()

# When everything is done, release the capture
cap.release()
cv2.destroyAllWindows()
