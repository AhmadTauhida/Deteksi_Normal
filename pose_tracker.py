import cv2
import mediapipe as mp
from typing import Optional, Tuple

from utils import MovingAverageSmoother, calculate_ankle_angle


class AnkleTracker:
    def __init__(self, model_complexity: int = 2, smooth_landmarks: bool = True, smoothing_window: int = 5):
        # model_complexity=2 (the heaviest of MediaPipe's 3 pose models) was
        # taking 60-150ms+ per frame on typical CPUs, far slower than the
        # ~20ms the old capture loop assumed. model_complexity=1 is a much
        # better fit for real-time webcam use while still being accurate
        # enough for ankle-angle tracking.
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            smooth_landmarks=smooth_landmarks,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.smoother = MovingAverageSmoother(window_size=smoothing_window)

    def _landmark_to_point(self, landmark, frame_width: int, frame_height: int) -> Tuple[float, float]:
        return landmark.x * frame_width, landmark.y * frame_height

    def _extract_side_angle(self, landmarks, side_prefix: str, image_width: int, image_height: int) -> Optional[float]:
        knee = getattr(self.mp_pose.PoseLandmark, f"{side_prefix}_KNEE")
        ankle = getattr(self.mp_pose.PoseLandmark, f"{side_prefix}_ANKLE")
        heel = getattr(self.mp_pose.PoseLandmark, f"{side_prefix}_HEEL")

        knee_landmark = landmarks[knee.value]
        ankle_landmark = landmarks[ankle.value]
        heel_landmark = landmarks[heel.value]

        visibility_threshold = 0.4
        if (
            knee_landmark.visibility < visibility_threshold
            or ankle_landmark.visibility < visibility_threshold
            or heel_landmark.visibility < visibility_threshold
        ):
            return None

        knee_point = self._landmark_to_point(knee_landmark, image_width, image_height)
        ankle_point = self._landmark_to_point(ankle_landmark, image_width, image_height)
        heel_point = self._landmark_to_point(heel_landmark, image_width, image_height)

        return calculate_ankle_angle(knee_point, ankle_point, heel_point)

    def _select_best_side(self, landmarks, image_width: int, image_height: int) -> Tuple[Optional[float], str]:
        right_angle = self._extract_side_angle(landmarks, "RIGHT", image_width, image_height)
        left_angle = self._extract_side_angle(landmarks, "LEFT", image_width, image_height)

        if right_angle is not None and left_angle is not None:
            return (right_angle, "Right") if right_angle <= left_angle else (left_angle, "Left")
        if right_angle is not None:
            return right_angle, "Right"
        if left_angle is not None:
            return left_angle, "Left"
        return None, "Unknown"

    def process_frame(self, frame: cv2.Mat) -> Tuple[cv2.Mat, Optional[float], str]:
        image_height, image_width = frame.shape[:2]
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)
        image_rgb.flags.writeable = True
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        angle: Optional[float] = None
        side_label = "Unknown"

        if results.pose_landmarks:
            angle, side_label = self._select_best_side(
                results.pose_landmarks.landmark, image_width, image_height
            )
            angle = self.smoother.smooth(angle)
            self.mp_drawing.draw_landmarks(
                image_bgr,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(144, 238, 144), thickness=2, circle_radius=2),
            )

            if angle is not None:
                cv2.putText(
                    image_bgr,
                    f"{side_label} Ankle: {angle:.1f}°",
                    (16, 32),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.85,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
            else:
                cv2.putText(
                    image_bgr,
                    "Ankle landmarks not visible",
                    (16, 32),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (220, 220, 220),
                    2,
                    cv2.LINE_AA,
                )

        return image_bgr, angle, side_label