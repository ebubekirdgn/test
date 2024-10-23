from exercises.exercise_strategy import ExerciseStrategy
import cv2
import mediapipe as mp
import numpy as np

class CrunchStrategy(ExerciseStrategy):

    def __init__(self):
        self.counter = 0  # Egzersiz sayısı
        self.is_exercising = False  # Egzersiz durumu (başladı mı, bitti mi?)
        self.cap = None  # VideoCapture nesnesi, kamerayı başlatıp kontrol etmek için
        self.stage = None

    def calculate_angle(self, a, b, c):
        a = np.array(a)  # İlk nokta
        b = np.array(b)  # Orta nokta
        c = np.array(c)  # Son nokta

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180.0:
            angle = 360 - angle

        return angle

    def perform_exercise(self):
        
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

                # Görüntüyü yeniden boyutlandırarak uzaklaştırma
                scale_percent = 50  # Oranı daha düşük yaparak geniş görünüm
                width = int(frame.shape[1] * scale_percent / 100)
                height = int(frame.shape[0] * scale_percent / 100)
                frame = cv2.resize(frame, (width, height))

                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark

                    # Kalça ve omuz landmark'larını alın
                    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]

                    # Vücut açısına dayalı yukarı/aşağı durumu
                    if hip[1] > shoulder[1]:  # Kalça omuzdan daha aşağıda
                        state = "DOWN"
                    else:  # Kalça omuz hizasından yukarı çıktıysa
                        if state == "DOWN":
                            self.counter += 1  # Bir tur say
                        state = "UP"

                    # Geri bildirim (UP/DOWN ve sayaç)
                    cv2.putText(image, f'Counter: {self.counter}', (50, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    if state == "UP":
                        cv2.putText(image, "Up", (50, 100), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    elif state == "DOWN":
                        cv2.putText(image, "Down", (50, 100), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                    # Landmarkları ve bağlantıları çizin (sporcu üst vücut)
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                # Görüntüyü yayına hazır hale getirme
                ret, buffer = cv2.imencode('.jpg', image)  # JPEG formatına çevir
                frame = buffer.tobytes()

                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

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
    