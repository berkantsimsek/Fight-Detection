import cv2
import numpy as np
from keras._tf_keras.keras.models import load_model

def preprocess_frame(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (224, 224))
    normalized = resized / 255.0
    return np.expand_dims(normalized, axis=0)

class ViolenceDetector:
    def __init__(self, model_path, test_mode=False):
        self.model = load_model(model_path)
        self.fgbg = cv2.createBackgroundSubtractorMOG2()
        self.test_mode = test_mode

    def detect(self, frame, motion_threshold=1000):
        if self.test_mode:
            return "Violence", 0.9, True  # Test modunda sabit Violence

        fgmask = self.fgbg.apply(frame)
        motion_detected = cv2.countNonZero(fgmask) > motion_threshold
        if not motion_detected:
            return "Non-Violence", 0.0, False
        input_frame = preprocess_frame(frame)
        pred_proba = self.model.predict(input_frame, verbose=0)[0][0]
        label = "Violence" if pred_proba > 0.5 else "Non-Violence"
        confidence = pred_proba if label == "Violence" else 1 - pred_proba
        return label, confidence, motion_detected

    def set_test_mode(self, enabled):
        self.test_mode = enabled