import random
import time
from collections import deque

import cv2
import gesture_engine

WINDOW_NAME = "GEST Simulation"
SQUARE_SIZE = 50
MAX_SPEED = 12.0
ACCELERATION = 2.0
FRICTION = 0.82


def clamp(value, low, high):
    return max(low, min(value, high))


def create_shape(x, y):
    return {
        "x": int(x),
        "y": int(y),
        "size": SQUARE_SIZE,
        "color": (
            random.randint(60, 255),
            random.randint(60, 255),
            random.randint(60, 255),
        ),
    }


def draw_all_shapes(frame, shapes, selected_idx):
    """Draw all shapes, highlighting the selected one."""
    for idx, shape in enumerate(shapes):
        color = shape["color"]
        thickness = 3 if idx == selected_idx else -1
        x = int(round(shape["x"]))
        y = int(round(shape["y"]))
        size = int(round(shape["size"]))

        cv2.rectangle(
            frame,
            (x, y),
            (x + size, y + size),
            color,
            thickness,
        )

        if idx == selected_idx:
            cv2.rectangle(
                frame,
                (x - 3, y - 3),
                (x + size + 3, y + size + 3),
                (255, 255, 0),
                2,
            )


def update_shape_velocity(vx, vy, direction):
    """Smooth velocity update based on pointing direction."""
    target_vx, target_vy = 0.0, 0.0

    if direction == "RIGHT":
        target_vx = MAX_SPEED
    elif direction == "LEFT":
        target_vx = -MAX_SPEED
    elif direction == "UP":
        target_vy = -MAX_SPEED
    elif direction == "DOWN":
        target_vy = MAX_SPEED

    vx += (target_vx - vx) * (ACCELERATION / MAX_SPEED)
    vy += (target_vy - vy) * (ACCELERATION / MAX_SPEED)

    if direction is None:
        vx *= FRICTION
        vy *= FRICTION

    if abs(vx) < 0.05:
        vx = 0.0
    if abs(vy) < 0.05:
        vy = 0.0

    return vx, vy


def main():
    shapes = []
    selected_idx = -1
    initial_shape_created = False

    vx, vy = 0.0, 0.0
    left_palm_state_history = deque(maxlen=3)
    last_create_time = 0.0
    create_cooldown = 0.8

    prompt_text = "Open left palm to select"
    status_text = "Ready"

    print("Starting gesture-controlled simulation. Press ESC to exit.")
    print("Controls:")
    print("  - Left hand OPEN PALM: Select/grab shape")
    print("  - Left hand CLOSED FIST: Lock shape in place")
    print("  - Right hand POINTING: Move selected shape")
    print("  - Double open left palm: Create new shape")

    while True:
        frame, hands_info = gesture_engine.get_detailed_hands()

        if frame is None:
            print("Camera error: no frame received.")
            break

        height, width, _ = frame.shape
        left_hand = hands_info.get("left_hand")
        right_hand = hands_info.get("right_hand")

        if not initial_shape_created:
            shapes.append(create_shape(width // 2 - SQUARE_SIZE // 2, height // 2 - SQUARE_SIZE // 2))
            selected_idx = 0
            initial_shape_created = True

        left_gesture = left_hand["gesture"] if left_hand else None
        right_gesture = right_hand["gesture"] if right_hand else None
        right_direction = right_hand["direction"] if right_hand and right_hand["gesture"] == "POINTING" else None

        left_palm_state_history.append(left_gesture)

        shape_locked = False
        create_event = False
        now = time.time()

        if left_gesture == "OPEN_PALM":
            if selected_idx == -1 and len(shapes) > 0:
                selected_idx = 0
            prompt_text = "Left palm OPEN - Shape selected"
            status_text = "SELECTING"

        elif left_gesture == "CLOSED_FIST":
            shape_locked = True
            prompt_text = "Left palm CLOSED - Shape locked"
            status_text = "LOCKED"

        else:
            prompt_text = "No gesture - Open left palm"
            status_text = "WAITING"

        if (
            len(left_palm_state_history) >= 3
            and list(left_palm_state_history)[0] == "OPEN_PALM"
            and list(left_palm_state_history)[1] == "CLOSED_FIST"
            and left_gesture == "OPEN_PALM"
            and now - last_create_time >= create_cooldown
        ):
            if len(shapes) == 0:
                new_x, new_y = width // 2, height // 2
            else:
                new_x, new_y = shapes[selected_idx]["x"], shapes[selected_idx]["y"]

            shapes.append(create_shape(new_x, new_y))
            selected_idx = len(shapes) - 1
            last_create_time = now
            create_event = True
            prompt_text = "Shape CREATED!"

        if selected_idx >= 0 and selected_idx < len(shapes) and not shape_locked:
            if right_direction:
                vx, vy = update_shape_velocity(vx, vy, right_direction)
            else:
                vx, vy = update_shape_velocity(vx, vy, None)

            shapes[selected_idx]["x"] += vx
            shapes[selected_idx]["y"] += vy

            shapes[selected_idx]["x"] = clamp(
                shapes[selected_idx]["x"], 0, width - SQUARE_SIZE
            )
            shapes[selected_idx]["y"] = clamp(
                shapes[selected_idx]["y"], 0, height - SQUARE_SIZE
            )

        draw_all_shapes(frame, shapes, selected_idx)

        cv2.putText(
            frame,
            f"Status: {status_text}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            prompt_text,
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame,
            f"Left: {left_gesture if left_gesture else 'None'}",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (200, 150, 255),
            1,
        )
        cv2.putText(
            frame,
            f"Right: {right_gesture if right_gesture else 'None'} {right_direction if right_direction else ''}",
            (10, 115),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (150, 200, 255),
            1,
        )
        cv2.putText(
            frame,
            f"Shapes: {len(shapes)} | Selected: {selected_idx}",
            (10, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 200, 0), 
            2,
        )

        cv2.imshow(WINDOW_NAME, frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    gesture_engine.release_resources()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()