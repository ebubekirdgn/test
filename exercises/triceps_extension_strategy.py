import cv2
import mediapipe as mp
import numpy as np
from exercises.exercise_strategy import ExerciseStrategy

class TricepsExtensionStrategy(ExerciseStrategy):

    def __init__(self):
        self.counter = 0
        self.is_exercising = False
        self.cap = None
        self.stage = None  # 'up' veya 'down' durumu

    def calculate_angle(self, a, b, c):
        a = np.array(a)  # İlk nokta
        b = np.array(b)  # Ortadaki nokta
        c = np.array(c)  # Son nokta

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180.0:
            angle = 360 - angle

        return angle

    def perform_exercise(self):
        # Set up MediaPipe components
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        self.is_exercising = True
        self.cap = cv2.VideoCapture(0)
 
        # --- Kamera çözünürlüğünü artır ---
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Genişlik
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Yükseklik

        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    break

                # Flip the frame for a mirror effect
                frame = cv2.flip(frame, 1)

                # Convert BGR to RGB
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image_rgb)

                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark

                    # Get landmarks for both arms
                    left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * frame.shape[1],
                                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * frame.shape[0]]
                    left_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x * frame.shape[1],
                                landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y * frame.shape[0]]
                    left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x * frame.shape[1],
                                landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y * frame.shape[0]]

                    right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x * frame.shape[1],
                                    landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y * frame.shape[0]]
                    right_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x * frame.shape[1],
                                landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y * frame.shape[0]]
                    right_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x * frame.shape[1],
                                landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y * frame.shape[0]]

                    # Calculate angles for both arms
                    left_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
                    right_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)

                    # Angle control
                    if left_angle > 160 and right_angle > 160:
                        self.stage = "down"  # Down movement

                    if (left_angle < 75 and right_angle < 75) and self.stage == 'down':
                        self.stage = "up"  # Up movement
                        self.counter += 1  # Increment counter

                    # Display counter and angles
                    cv2.putText(frame, f'Counter: {self.counter}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f'Left Angle: {int(left_angle)}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    cv2.putText(frame, f'Right Angle: {int(right_angle)}', (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                    # Draw the pose landmarks
                    mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS, 
                                            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=5, circle_radius=5),  # Kalın çizgi
                                            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=5, circle_radius=5))  # Kalın nokta

                # Convert the image to JPEG format for streaming
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        self.cap.release()

    def stop_exercise(self):
        self.is_exercising = False
        if self.cap:
            self.cap.release()  # Kamerayı serbest bırak
        cv2.destroyAllWindows()  # Tüm pencereleri kapat

    def reset_counter(self):
        self.counter = 0
        
    def get_counter(self):
        return self.counter  # Sayaç değerini döndüren fonksiyon
    
    def get_totals(self, user):
        return self.get_total_exercises(user)  # Ortak metodu kullan
