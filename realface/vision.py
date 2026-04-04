from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from realface.features import compute_descriptor, descriptor_distance, descriptor_to_list
from realface.storage import FACES_DIR, ensure_storage, load_database, upsert_person


MATCH_THRESHOLD = 120.0


def build_detector() -> cv2.CascadeClassifier:
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(str(cascade_path))
    if detector.empty():
        raise RuntimeError(f"Unable to load Haar cascade from {cascade_path}")
    return detector


def open_camera(camera_index: int = 0) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Unable to open webcam. Check camera permissions or camera index.")
    return cap


def detect_faces(detector: cv2.CascadeClassifier, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(90, 90),
    )
    return [tuple(int(value) for value in face) for face in faces]


def largest_face(faces: List[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
    if not faces:
        return None
    return max(faces, key=lambda item: item[2] * item[3])


def crop_face(frame: np.ndarray, face_box: Tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = face_box
    return frame[y:y + h, x:x + w].copy()


def enroll_person(name: str, camera_index: int = 0) -> None:
    ensure_storage()
    window_name = "Enrollment"
    detector = build_detector()
    cap = open_camera(camera_index)
    sample_saved = False
    try:
        print("Focus the webcam window, then press SPACE or ENTER to capture, Q or ESC to cancel.")
        while True:
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("Unable to read a frame from the webcam.")

            faces = detect_faces(detector, frame)
            face_box = largest_face(faces)
            preview = frame.copy()
            if face_box is not None:
                x, y, w, h = face_box
                cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 200, 0), 2)
                cv2.putText(preview, f"Detected face for {name}", (x, max(25, y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
            else:
                cv2.putText(preview, "No face detected", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(preview, "SPACE/ENTER capture", (20, preview.shape[0] - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(preview, "Q/ESC exit", (20, preview.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow(window_name, preview)
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("Enrollment window closed.")
                return
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q"), 27):
                print("Enrollment cancelled.")
                return
            if key in (32, 13, 10):
                if face_box is None:
                    print("No face detected. Move closer to the camera and try again.")
                    continue
                face = crop_face(frame, face_box)
                descriptor = compute_descriptor(face)
                sample_path = FACES_DIR / f"{name.strip().replace(' ', '_').lower()}.png"
                cv2.imwrite(str(sample_path), face)
                upsert_person(name, descriptor_to_list(descriptor), str(sample_path))
                sample_saved = True
                print(f"Saved profile for {name} in {sample_path}")
                return
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if not sample_saved:
            print("No new face profile saved.")


def recognize_live(camera_index: int = 0) -> None:
    database = load_database()
    if not database:
        raise RuntimeError("No enrolled faces found. Register at least one person first.")

    window_name = "Live Face Recognition"
    detector = build_detector()
    cap = open_camera(camera_index)
    print("Focus the webcam window, then press Q or ESC to stop live recognition.")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("Unable to read a frame from the webcam.")

            faces = detect_faces(detector, frame)
            for x, y, w, h in faces:
                face = crop_face(frame, (x, y, w, h))
                descriptor = compute_descriptor(face)

                best_name = "Unknown"
                best_score = None
                for record in database:
                    score = descriptor_distance(descriptor, np.array(record["descriptor"], dtype=np.float32))
                    if best_score is None or score < best_score:
                        best_score = score
                        best_name = record["name"]

                is_match = best_score is not None and best_score <= MATCH_THRESHOLD
                color = (0, 180, 0) if is_match else (0, 0, 255)
                label = f"{best_name} ({best_score:.1f})" if is_match else "Unknown"
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label, (x, max(25, y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            cv2.putText(frame, "Q/ESC exit", (20, frame.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow(window_name, frame)
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("Recognition window closed.")
                break
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
