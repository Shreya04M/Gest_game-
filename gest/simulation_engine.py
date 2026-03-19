import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

cap = cv2.VideoCapture(0)

def get_action():

    ret, frame = cap.read()
    if not ret:
        return None, None

    frame = cv2.flip(frame,1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    action = "NONE"

    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness
        ):
            hand_label = handedness.classification[0].label

            tip = hand_landmarks.landmark[8]
            pip = hand_landmarks.landmark[6]

            dx = tip.x - pip.x
            dy = tip.y - pip.y

            if abs(dx) > abs(dy):
                action = "MOVE_RIGHT" if dx > 0 else "MOVE_LEFT"
            else:
                action = "MOVE_DOWN" if dy > 0 else "MOVE_UP"

    return frame, action