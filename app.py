from datetime import datetime
from flask import Flask, Response, jsonify, render_template, redirect, url_for, flash, request, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from exercises.bicep_curl_strategy import BicepsCurlStrategy
from exercises.crunch_strategy import CrunchStrategy
from exercises.triceps_extension_strategy import TricepsExtensionStrategy
from exercises.shoulder_press_strategy import ShoulderPressStrategy
from exercises.lateral_raise_strategy import LateralRaiseStrategy
from exercises.squat_strategy import SquatStrategy
from models.exercise import add_exercise, create_exercises_table
from models.user import create_user_table, get_db_connection

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Egzersiz stratejilerini saklamak için bir sözlük oluştur
exercise_strategies = {}

strategy_classes = {
    'biceps_curl': BicepsCurlStrategy,
    'triceps_extension': TricepsExtensionStrategy,
    'lateral_raise': LateralRaiseStrategy,
    'squat': SquatStrategy,
    'shoulder_press': ShoulderPressStrategy,
    'crunch': CrunchStrategy
}

# Login formu
class LoginForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    submit = SubmitField('Giriş Yap')

# Register formu
class RegisterForm(FlaskForm):
    first_name = StringField('Ad', validators=[DataRequired()])
    last_name = StringField('Soyad', validators=[DataRequired()])
    username = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Şifre', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Şifreyi Onayla', validators=[DataRequired(), EqualTo('password', message='Şifreler eşleşmiyor')])
    date_of_birth = StringField('Doğum Tarihi (YYYY-MM-DD)', validators=[DataRequired()])
    height = StringField('Boy (cm)', validators=[DataRequired()])
    weight = StringField('Kilo (kg)', validators=[DataRequired()])
    submit = SubmitField('Kayıt Ol')

#--------------------------------------------------ROOTLAR ------------------------------------------------------------------------------------

#region routelar burada
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Kullanıcıyı veri tabanından al
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        # Şifreyi kontrol et
        if user and check_password_hash(user['password'], password):
            session['user'] = username  # Kullanıcı adını oturumda sakla
            return redirect(url_for('layout'))  # Giriş başarılı, layout sayfasına yönlendir
        else:
            flash('Kullanıcı adı veya şifre hatalı', 'danger')

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = generate_password_hash(form.password.data)
        first_name = form.first_name.data
        last_name = form.last_name.data
        date_of_birth = form.date_of_birth.data
        height = form.height.data
        weight = form.weight.data

        # Kullanıcıyı veri tabanına kaydet
        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if existing_user:
            flash('Kullanıcı adı zaten mevcut!', 'danger')
        else:
            if form.password.data != form.confirm_password.data:
                flash('Şifreler eşleşmiyor!', 'danger')
            else:
                try:
                    conn.execute('INSERT INTO users (first_name, last_name, username, password, date_of_birth, height, weight) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (first_name, last_name, username, password, date_of_birth, height, weight))
                    conn.commit()
                    flash('Kayıt başarılı! Lütfen giriş yapın.', 'success')
                    return redirect(url_for('login'))
                except Exception as e:
                    flash('Bir hata oluştu: {}'.format(e), 'danger')
                finally:
                    conn.close()

    return render_template('register.html', form=form)

@app.route('/layout')
def layout():
    if 'user' not in session:
        return redirect(url_for('login'))  # Oturum yoksa giriş sayfasına yönlendir

    user = session['user']
    # Tüm stratejileri oluştur ve toplamları al
    totals = {exercise: strategy_classes[exercise]().get_totals(user) for exercise in strategy_classes}

    return render_template('layout.html', user=user, totals=totals)  # Toplamları sayfaya gönder


@app.route('/statistics')
def statistics():
    user = session['user']
    # Tüm stratejileri oluştur ve toplamları al
    exerciseTotals = {exercise: strategy_classes[exercise]().get_totals(user) for exercise in strategy_classes}
    return render_template('statistics.html', user=user, totals=exerciseTotals)  # Boş bir dict gönder

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('login'))
 
#endregion

#--------------------------------------------------------------------HAREKETLER--------------------------------------------------------------------
@app.route('/exercise/<exercise_name>', methods=['GET'])
def exercise(exercise_name):
    if 'user' not in session:
        return redirect(url_for('login'))  # Kullanıcı oturumu yoksa giriş sayfasına yönlendir
    
    user = session['user']
    # Kullanıcı için strateji oluştur
    if exercise_name in strategy_classes:
        # Stratejiyi oluştur ve kullanıcıya özgü egzersiz stratejisini kaydet
        exercise_strategies[user] = strategy_classes[exercise_name]()  
        
        # Tüm toplam değerleri al
        totals = {exercise: strategy_classes[exercise]().get_totals(user) for exercise in strategy_classes}
        
        # İlgili sayfayı yükle ve toplam değerleri gönder
        return render_template('components/' + exercise_name + '.html', user=user, totals=totals)  
    else:
        flash('Geçersiz egzersiz seçimi', 'danger')
        return redirect(url_for('layout'))

#--------------------------------------------------------------------KAMERA AKSİYONLARI------------------------------------------------------------------------

#region start-stop-finish
@app.route('/start/<exercise_name>', methods=['POST'])
def start(exercise_name):
    if 'user' not in session:
        return jsonify(status='Unauthorized'), 401  # Kullanıcı oturumu yoksa hata döndür

    # Geçerli bir egzersiz ismi olup olmadığını kontrol et
    if exercise_name not in strategy_classes:
        return jsonify(status='Invalid exercise name', error='Egzersiz adı geçersiz'), 400

    user = session['user']
    exercise_strategies[user] = strategy_classes[exercise_name]()  # Stratejiyi oluştur
    return jsonify(status='Exercise started', exercise=exercise_name)  # Başarılı yanıt gönder

@app.route('/stop', methods=['POST'])
def stop():
    user = session['user']
    strategy = exercise_strategies.get(user)

    if strategy:
        strategy.stop_exercise()  # Egzersizi durdur
        return jsonify(status='Exercise Stopped')
    return jsonify(status='Strategy not found'), 404

@app.route('/finish/<exercise_name>', methods=['POST'])
def finish_stream(exercise_name):
    if 'user' not in session:
        return jsonify(status='Unauthorized'), 401  # Kullanıcı oturumu yoksa hata döndür

    user = session['user']

    # Kullanıcıya özel stratejiyi al
    strategy = exercise_strategies.get(user)
    if strategy is None:
        return jsonify(status='No active exercise strategy found'), 400  # Strateji yoksa hata döndür

    counter_value = strategy.get_counter()  # Seçilen strateji üzerinden sayaç değerini al
    current_date = datetime.now().date()  # Şu anki tarihi al

    if counter_value > 0:
        # Veritabanından aynı tarih ve kullanıcıya ait mevcut egzersiz kaydını al
        conn = get_db_connection()
        existing_record = conn.execute('SELECT * FROM exercises WHERE user = ? AND created_date = ?', 
                                       (user, current_date)).fetchone()

        if existing_record:
            # Aynı tarihte zaten kayıt var, mevcut sayıyı güncelle
            new_count = existing_record[exercise_name] + counter_value  # Dinamik güncelleme
            conn.execute(f'''
                UPDATE exercises
                SET {exercise_name} = ?
                WHERE user = ? AND created_date = ?
            ''', (new_count, user, current_date))
        else:
            # Aynı tarihte kayıt yok, yeni bir kayıt ekle
            # Diğer egzersizlerin sayısını 0 olarak ayarlıyoruz
            conn.execute(''' 
                INSERT INTO exercises (user, biceps_curl, triceps_extension, lateral_raise, squat, shoulder_press, crunch, created_date)
                VALUES (?, ?, 0, 0, 0, 0, 0, ?)
            ''', (user, counter_value, current_date))

        conn.commit()
        conn.close()

        # Sayaç sıfırlama işlemi
        strategy.reset_counter()

        # Kullanıcıya başarı mesajı döndür
        return jsonify(status='Exercise Finished', counter=counter_value)
    else:
        return jsonify(status='No data to save')  # Sayaç sıfırsa veri kaydedilmez 

#endregion

#-------------------------------------------------------------------HAREKET METHODLARI------------------------------------------------------------

#region hareket kodları
@app.route('/video_feed')
def video_feed():
    user = session['user']
    strategy = exercise_strategies.get(user)

    if strategy:
        return Response(strategy.perform_exercise(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return jsonify(status='Strategy not found'), 404

@app.route('/get_counter')
def get_counter():
    user = session['user']
    strategy = exercise_strategies.get(user)
    
    if strategy:
        counter_value = strategy.get_counter()
        return jsonify({'counter': counter_value})
    return jsonify(status='Strategy not found'), 404

#endregion

if __name__ == '__main__':
    create_user_table()
    create_exercises_table()
    app.run(debug=True)
