from abc import ABC, abstractmethod
import sqlite3
from datetime import datetime

class ExerciseStrategy(ABC):
    @abstractmethod
    def perform_exercise(self):
        pass
    
    def get_total_exercises(self, user):
            # Bu fonksiyon, aktif olan kullanıcının ay içerisindeki egzersiz toplamlarını getirir
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            
            # Şu anki ayın başlangıcını al
            current_month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            
            # Her hareket için mevcut ayın toplam sayılarını al
            cursor.execute('''
                SELECT
                    SUM(biceps_curl) AS total_biceps_curl,
                    SUM(triceps_extension) AS total_triceps_extension,
                    SUM(lateral_raise) AS total_lateral_raise,
                    SUM(squat) AS total_squat,
                    SUM(shoulder_press) AS total_shoulder_press,
                    SUM(crunch) AS total_crunch
                FROM exercises
                WHERE user = ?
                AND created_date >= ?
            ''', (user, current_month_start))
            
            totals = cursor.fetchone()
            conn.close()
            
            return {
                'total_biceps_curl': totals[0] or 0,
                'total_triceps_extension': totals[1] or 0,
                'total_lateral_raise': totals[2] or 0,
                'total_squat': totals[3] or 0,
                'total_shoulder_press': totals[4] or 0,
                'total_crunch': totals[5] or 0,
            }