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


def _try_open_camera(index, backend=None):
    if backend is None:
        candidate = cv2.VideoCapture(index)
    else:
        candidate = cv2.VideoCapture(index, backend)

    if candidate.isOpened():
        return candidate

    candidate.release()
    return None


def _create_camera_capture():
    """Try common camera indices/backends for robust startup on Windows."""
    backends = [None]
    if hasattr(cv2, "CAP_DSHOW"):
        backends.append(cv2.CAP_DSHOW)
    if hasattr(cv2, "CAP_MSMF"):
        backends.append(cv2.CAP_MSMF)

    for cam_index in (0, 1, 2):
        for backend in backends:
            opened = _try_open_camera(cam_index, backend)
            if opened is not None:
                return opened

    return cv2.VideoCapture(0)


cap = _create_camera_capture()


def _read_frame_with_reconnect():
    """Read a frame and attempt one reconnect cycle if camera read fails."""
    global cap

    if cap is None or not cap.isOpened():
        cap = _create_camera_capture()

    ret, frame = cap.read()
    if ret:
        return ret, frame

    if cap is not None:
        cap.release()
    cap = _create_camera_capture()
    return cap.read()


def get_finger_states(hand_landmarks, handedness):
    """Returns array of 5 booleans: [thumb, index, middle, ring, pinky] for open/closed state."""
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
    """Classify gesture from finger states: OPEN_PALM, CLOSED_FIST, POINTING, NONE."""
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


def get_hand_direction(hand_landmarks):
    """Get pointing direction from index finger for POINTING gesture."""
    tip = hand_landmarks.landmark[8]
    pip = hand_landmarks.landmark[6]

    dx = tip.x - pip.x
    dy = tip.y - pip.y

    if abs(dx) > abs(dy):
        return "RIGHT" if dx > 0 else "LEFT"
    else:
        return "DOWN" if dy > 0 else "UP"


def get_action():
    """Legacy function: returns frame and simple action."""
    ret, frame = _read_frame_with_reconnect()
    if not ret:
        return None, None

    frame = cv2.flip(frame, 1)
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


def get_detailed_hands():
    """Returns frame and detailed hand state: {left_hand: {...}, right_hand: {...}}"""
    ret, frame = _read_frame_with_reconnect()
    if not ret:
        return None, None

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    hands_info = {"left_hand": None, "right_hand": None}

    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness
        ):
            hand_label = handedness.classification[0].label
            finger_states = get_finger_states(hand_landmarks, hand_label)
            gesture = classify_gesture(finger_states)
            direction = get_hand_direction(hand_landmarks) if gesture == "POINTING" else None

            hand_info = {
                "gesture": gesture,
                "direction": direction,
                "finger_states": finger_states,
                "landmarks": hand_landmarks,
            }

            if hand_label == "Left":
                hands_info["left_hand"] = hand_info
            else:
                hands_info["right_hand"] = hand_info

    return frame, hands_info


def release_resources():
    if cap is not None and cap.isOpened():
        cap.release()
    hands.close()