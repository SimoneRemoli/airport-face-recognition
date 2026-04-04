from typing import List

import cv2
import numpy as np


FACE_SIZE = (128, 128)
GRID_SIZE = (8, 8)
LBP_BINS = 256


def preprocess_face(face_bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, FACE_SIZE)
    return cv2.equalizeHist(resized)


def lbp_image(gray_face: np.ndarray) -> np.ndarray:
    center = gray_face[1:-1, 1:-1]
    result = np.zeros_like(center, dtype=np.uint8)
    offsets = [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
        (1, 0),
        (1, -1),
        (0, -1),
    ]
    for index, (dy, dx) in enumerate(offsets):
        neighbour = gray_face[1 + dy:gray_face.shape[0] - 1 + dy, 1 + dx:gray_face.shape[1] - 1 + dx]
        result |= ((neighbour >= center).astype(np.uint8) << index)
    return result


def compute_descriptor(face_bgr: np.ndarray) -> np.ndarray:
    normalized = preprocess_face(face_bgr)
    lbp = lbp_image(normalized)

    cell_h = lbp.shape[0] // GRID_SIZE[0]
    cell_w = lbp.shape[1] // GRID_SIZE[1]
    descriptor_parts = []
    for row in range(GRID_SIZE[0]):
        for col in range(GRID_SIZE[1]):
            cell = lbp[row * cell_h:(row + 1) * cell_h, col * cell_w:(col + 1) * cell_w]
            hist, _ = np.histogram(cell.ravel(), bins=LBP_BINS, range=(0, LBP_BINS), density=False)
            hist = hist.astype(np.float32)
            hist /= max(hist.sum(), 1.0)
            descriptor_parts.append(hist)
    descriptor = np.concatenate(descriptor_parts)
    return descriptor.astype(np.float32)


def descriptor_distance(a: np.ndarray, b: np.ndarray) -> float:
    eps = 1e-7
    return float(0.5 * np.sum(((a - b) ** 2) / (a + b + eps)))


def descriptor_to_list(descriptor: np.ndarray) -> List[float]:
    return descriptor.astype(float).tolist()
