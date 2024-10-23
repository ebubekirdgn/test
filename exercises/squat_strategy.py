import cv2
import mediapipe as mp
import numpy as np
from exercises.exercise_strategy import ExerciseStrategy
class SquatStrategy(ExerciseStrategy):

    def __init__(self):
        self.counter = 0
        self.is_exercising = False
        self.cap = None
        self.stage = None  # 'up' veya 'down' durumu
    
    def calculate_angle(self, a, b, c):
        """Üç nokta arasındaki açıyı hesapla."""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        angle = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(angle * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360 - angle
        return angle

    def perform_exercise(self):
        # MediaPipe bileşenlerini ayarla
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)

        # Kamera çözünürlüğünü artır
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Genişlik
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Yükseklik

        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    break

                # Görüntüyü ayna etkisi için ters çevir
                frame = cv2.flip(frame, 1)

                # BGR'den RGB'ye çevir
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image_rgb)

                # Landmark'ları çiz ve belirli noktaları kontrol et
                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark

                    # Sol ve sağ bacak landmark'ları
                    left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x * frame.shape[1],
                                landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y * frame.shape[0]]
                    left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x * frame.shape[1],
                                 landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y * frame.shape[0]]
                    left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x * frame.shape[1],
                                  landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y * frame.shape[0]]

                    right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x * frame.shape[1],
                                 landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y * frame.shape[0]]
                    right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x * frame.shape[1],
                                  landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y * frame.shape[0]]
                    right_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x * frame.shape[1],
                                   landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y * frame.shape[0]]

                    # Açıları hesapla
                    angle1 = self.calculate_angle(left_hip, left_knee, left_ankle)  # Sol bacak açısı
                    angle2 = self.calculate_angle(right_hip, right_knee, right_ankle)  # Sağ bacak açısı

                    # Açı kontrolü
                    if angle1 < 90 and angle2 < 90:
                        self.stage = "down"  # Aşağı
                    if angle1 > 90 and angle2 > 90 and self.stage == 'down':
                        self.stage = "up"  # Yukarı
                        self.counter += 1  # Sayaç artır

                    # Sayıcıyı ve açıları göster
                    cv2.putText(frame, f'Counter: {self.counter}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f'Angle1: {int(angle1)}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    cv2.putText(frame, f'Angle2: {int(angle2)}', (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                    # Landmark'ları çiz
                    mp_drawing.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),  # Noktalar
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)  # Bağlantılar
                    )

                # Görüntüyü JPEG formatına çevir
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                # Görüntüyü stream olarak gönder
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            # Kamera kaynaklarını serbest bırak
            self.cap.release()
            cv2.destroyAllWindows()

        self.cap.release()
        cv2.destroyAllWindows()


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
