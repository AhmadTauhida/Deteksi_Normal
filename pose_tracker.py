import cv2
import mediapipe as mp
from typing import Optional, Tuple

from utils import MovingAverageSmoother, calculate_ankle_angle, OneEuroFilter


class AnkleTracker:
    # PERBAIKAN 1: Ubah default model_complexity menjadi 1 untuk performa real-time yang lebih baik dan stabil.
    def __init__(self, model_complexity: int = 1, smooth_landmarks: bool = True, smoothing_window: int = 5):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            smooth_landmarks=smooth_landmarks,
            enable_segmentation=False,
            # PERBAIKAN 2: Naikkan confidence menjadi 0.7 agar marker tidak mudah getar/ngawur
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        self.smoother = OneEuroFilter(min_cutoff=0.5, beta=0.05)

    def _landmark_to_point(self, landmark, frame_width: int, frame_height: int) -> Tuple[float, float]:
        return landmark.x * frame_width, landmark.y * frame_height

    def _extract_side_angle(self, landmarks, side_prefix: str, image_width: int, image_height: int) -> Optional[float]:
        knee = getattr(self.mp_pose.PoseLandmark, f"{side_prefix}_KNEE")
        ankle = getattr(self.mp_pose.PoseLandmark, f"{side_prefix}_ANKLE")
        
        # GANTI _HEEL menjadi _FOOT_INDEX
        foot_idx = getattr(self.mp_pose.PoseLandmark, f"{side_prefix}_FOOT_INDEX") 

        knee_landmark = landmarks[knee.value]
        ankle_landmark = landmarks[ankle.value]
        foot_landmark = landmarks[foot_idx.value] # Gunakan foot_index

        visibility_threshold = 0.7 
        if (
            knee_landmark.visibility < visibility_threshold
            or ankle_landmark.visibility < visibility_threshold
            or foot_landmark.visibility < visibility_threshold # Cek visibilitas foot_index
        ):
            return None

        knee_point = self._landmark_to_point(knee_landmark, image_width, image_height)
        ankle_point = self._landmark_to_point(ankle_landmark, image_width, image_height)
        foot_point = self._landmark_to_point(foot_landmark, image_width, image_height)

        # Lempar ke utils.py yang baru
        return calculate_ankle_angle(knee_point, ankle_point, foot_point)

    def _get_left_side_angle(self, landmarks, image_width: int, image_height: int) -> Tuple[Optional[float], str]:
        """Hanya mengambil sudut ankle dari kaki kiri jika kaki kiri benar-benar menghadap kamera."""
        
        # PERBAIKAN 4: Validasi posisi Z (kedalaman) untuk membedakan kaki kiri dan kanan
        # Semakin kecil nilai Z, semakin dekat ke kamera.
        left_ankle_z = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].z
        right_ankle_z = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value].z
        
        # Jika ankle kanan lebih dekat ke kamera daripada ankle kiri (sedang menghadap kanan)
        if right_ankle_z < left_ankle_z:
             return None, "Right leg facing camera (Ignored)"

        left_angle = self._extract_side_angle(landmarks, "LEFT", image_width, image_height)
        if left_angle is not None:
            return left_angle, "Left"
        return None, "Unknown"

    def process_frame(self, frame: cv2.Mat) -> Tuple[cv2.Mat, Optional[float], str]:
        # (Isi dari process_frame tetap sama persis seperti kode aslimu)
        image_height, image_width = frame.shape[:2]
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)
        image_rgb.flags.writeable = True
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        angle: Optional[float] = None
        side_label = "Unknown"

        if results.pose_landmarks:
            angle, side_label = self._get_left_side_angle(
                results.pose_landmarks.landmark, image_width, image_height
            )
            angle = self.smoother.filter(angle)
            
            # Opsional: Kamu bisa membungkus draw_landmarks dalam kondisi 'if angle is not None:' 
            # agar garis kerangka hanya digambar ketika kaki kiri yang valid terdeteksi.
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
                    f"Left Ankle: {angle:.1f} Deg",
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
                    "Left ankle not clearly visible",
                    (16, 32),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (220, 220, 220),
                    2,
                    cv2.LINE_AA,
                )

        return image_bgr, angle, side_label