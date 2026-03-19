import cv2
import gesture_engine


def main():
    print("Starting gesture test. Press ESC to exit.")

    while True:
        frame, action = gesture_engine.get_action()

        if frame is None:
            print("Camera not working")
            break

        print("Frame:", frame is not None, "Action:", action)

        cv2.putText(
            frame,
            f"Action: {action}",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Gesture Test", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    gesture_engine.cap.release()
    gesture_engine.hands.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()