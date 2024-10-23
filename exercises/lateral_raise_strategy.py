import cv2
import mediapipe as mp
import numpy as np
from exercises.exercise_strategy import ExerciseStrategy

class LateralRaiseStrategy(ExerciseStrategy):
    
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
        self.is_exercising = True
        self.cap = cv2.VideoCapture(0)

         # --- Kamera çözünürlüğünü artır ---
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Genişlik
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Yükseklik
        
        # Hedef işaretli noktalar (Lateral Raise için)
        landmarks_to_highlight = [23, 11, 13, 24, 12, 14, 16, 14, 12, 15, 13, 11]

        # Bağlantılı noktalar (indexler)
        lines_to_draw = [
            (23, 11), (11, 13),
            (24, 12), (12, 14),
            (16, 14), (14, 12),
            (15, 13), (13, 11),
            (23, 24)  # İki omuz arasındaki bağlantı
        ]

        threshold_up_angle1 = 90  # Açı eşiği yukarı hareket için
        threshold_down_angle1 = 100  # Açı eşiği aşağı hareket için
        threshold_up_angle2 = 20  # Açı eşiği aşağı hareket için
        threshold_down_angle2 = 160  # Açı eşiği yukarı hareket için

        with mp_pose.Pose(static_image_mode=False, model_complexity=2, enable_segmentation=False) as pose:
            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    break

                # Görüntüyü ayna etkisi için ters çevir
                frame = cv2.flip(frame, 1)

                # BGR'den RGB'ye çevir
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = pose.process(image_rgb)

                # Landmark'ları gizle ve sadece belirli noktaları çiz
                if result.pose_landmarks:
                    # İşaretli noktaları çiz
                    points = []
                    height, width, _ = frame.shape
                    for idx in landmarks_to_highlight:
                        landmark = result.pose_landmarks.landmark[idx]
                        x, y = int(landmark.x * width), int(landmark.y * height)

                        # İşaretli noktayı daire ile vurgula
                        cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)
                        points.append((x, y))

                    # Belirli noktaları birleştir
                    for start_idx, end_idx in lines_to_draw:
                        start_point = points[landmarks_to_highlight.index(start_idx)]
                        end_point = points[landmarks_to_highlight.index(end_idx)]
                        cv2.line(frame, start_point, end_point, (255, 0, 0), 2)  # Mavi çizgi

                    # Açıları hesapla
                    point_a = np.array(points[landmarks_to_highlight.index(23)])  # Sağ kalça
                    point_b = np.array(points[landmarks_to_highlight.index(11)])  # Sağ omuz
                    point_c = np.array(points[landmarks_to_highlight.index(13)])  # Sağ dirsek
                    angle1 = self.calculate_angle(point_a, point_b, point_c)

                    point_d = np.array(points[landmarks_to_highlight.index(24)])  # Sol kalça
                    point_e = np.array(points[landmarks_to_highlight.index(12)])  # Sol omuz
                    point_f = np.array(points[landmarks_to_highlight.index(14)])  # Sol dirsek
                    angle2 = self.calculate_angle(point_d, point_e, point_f)

                    # Açı kontrolü ve durum belirleme
                    if (threshold_up_angle1 <= angle1 <= threshold_down_angle1) and (threshold_up_angle2 <= angle2 <= threshold_down_angle2) and (self.stage != 'up'):
                        self.counter += 1  # Doğru hareket yapıldığında sayacı artır
                        self.stage = 'up'
                    elif angle1 < threshold_up_angle1 and angle2 < threshold_up_angle2 and (self.stage == 'up'):
                        self.stage = 'down'

                    # Sayıcıyı ve açıları göster
                    cv2.putText(frame, f'Reps: {self.counter}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    cv2.putText(frame, f'Angle 1: {angle1:.2f}', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    cv2.putText(frame, f'Angle 2: {angle2:.2f}', (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                # Görüntüyü JPEG formatına çevir
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        self.cap.release()
        cv2.destroyAllWindows()

    def get_totals(self, user):
        return self.get_total_exercises(user)  # Ortak metodu kullan   
    
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