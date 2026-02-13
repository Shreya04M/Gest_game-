import cv2
import mediapipe as mp

# Explicitly access solutions through mediapipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def open_camera():
    for index in (0, 1, 2):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            return cap
        cap.release()
    return None

cap = open_camera()
if cap is None:
    print("❌ Camera not opened")
    exit()

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

print("✅ MediaPipe Hands running")
def get_finger_states(hand_landmarks, handedness):
    # Landmark indices
    #[Thumb, Index, Middle, Ring, Pinky]

    tips = [4, 8, 12, 16, 20]
    pips = [3, 6, 10, 14, 18]

    finger_states = []

    # Thumb (horizontal logic depends on hand)
    if handedness == "Right":
        finger_states.append(hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x)
    else:
        finger_states.append(hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x)

    # Other fingers (vertical)
    for tip, pip in zip(tips[1:], pips[1:]):
        finger_states.append(
            hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y
        )

    return finger_states
def classify_gesture(finger_states):
    thumb, index, middle, ring, pinky = finger_states

    # Open Palm → all fingers open
    if all(finger_states):
        return "OPEN_PALM"

    # Closed Fist → all fingers closed
    if not any(finger_states):
        return "CLOSED_FIST"

    # Pointing → only index finger open
    if index and not middle and not ring and not pinky:
        return "POINTING"

    return "NONE"
def get_pointing_direction(hand_landmarks):
    # Index finger tip and base
    tip = hand_landmarks.landmark[8]   # Index tip
    pip = hand_landmarks.landmark[6]   # Index middle joint

    dx = tip.x - pip.x
    dy = tip.y - pip.y

    # Horizontal movement stronger than vertical
    if abs(dx) > abs(dy):
        if dx > 0:
            return "RIGHT"
        else:
            return "LEFT"
    else:
        if dy > 0:
            return "DOWN"
        else:
            return "UP"

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Frame not captured")
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness
        ):
            hand_label = handedness.classification[0].label
            finger_states = get_finger_states(hand_landmarks, hand_label)

            gesture = classify_gesture(finger_states)
            action = "NONE"

            if hand_label == "Right" and gesture == "POINTING":
                direction = get_pointing_direction(hand_landmarks)
                action = f"MOVE_{direction}"

            # Display gesture
            cv2.putText(
                frame,
                f"ACTION: {action}",
                (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"{hand_label}: {gesture}",
                (10, 30 if hand_label == "Left" else 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

            # Display finger states
            text = f"{hand_label}: {finger_states}"
            cv2.putText(
                frame,
                text,
                (10, 30 if hand_label == "Left" else 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2
            )

            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            cv2.imshow("Hand Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
cap.release()
cv2.destroyAllWindows()
hands.close()
