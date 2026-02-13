import cv2
import numpy as np
import math

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Skin color range
    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin = np.array([20, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    # Noise removal
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    finger_count = 0

    if contours:
        hand_contour = max(contours, key=cv2.contourArea)

        if cv2.contourArea(hand_contour) > 5000:
            # Draw contour
            cv2.drawContours(frame, [hand_contour], -1, (0, 255, 0), 2)

            hull = cv2.convexHull(hand_contour, returnPoints=False)
            defects = cv2.convexityDefects(hand_contour, hull)

            if defects is not None:
                for i in range(defects.shape[0]):
                    s, e, f, d = defects[i, 0]

                    start = tuple(hand_contour[s][0])
                    end = tuple(hand_contour[e][0])
                    far = tuple(hand_contour[f][0])

                    # Triangle sides
                    a = math.dist(start, end)
                    b = math.dist(start, far)
                    c = math.dist(end, far)

                    # Angle using cosine rule
                    angle = math.acos((b*b + c*c - a*a) / (2*b*c)) * 57

                    # Count fingers based on angle + depth
                    if angle < 90 and d > 10000:
                        finger_count += 1
                        cv2.circle(frame, far, 5, (0, 0, 255), -1)

                    cv2.line(frame, start, end, (255, 0, 0), 2)

            finger_count += 1  # thumb or base finger

            cv2.putText(
                frame,
                f"Fingers: {finger_count}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 255, 0),
                3
            )

    cv2.imshow("Finger Tracking (Python 3.13)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()