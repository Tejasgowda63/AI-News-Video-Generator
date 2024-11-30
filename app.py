from flask import Flask, render_template, request, jsonify
import time
import os
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip
from flask import Flask, request, render_template, redirect, url_for, flash
from ttsmms import TTS, download
import wave
app = Flask(__name__)

os.makedirs('static/video', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/output', exist_ok=True)

def add_scrolling_text(input_video_path, output_video_path, lang_code, text, font_size=70, image_path=None, image_size=(800, 500), audio_duration=None):
    cap = cv2.VideoCapture(input_video_path)

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    fps = cap.get(5)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    img = Image.new('RGB', (frame_width, frame_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    if lang_code == "kan" :
        font = ImageFont.truetype('static/fonts/kannada.ttf', font_size)
    elif lang_code == 'eng':
        font = ImageFont.truetype('static/fonts/english.ttf', font_size)
    elif lang_code == 'hin':
        font = ImageFont.truetype('static/fonts/hindi.ttf',font_size)
    elif lang_code == 'tel':
        font = ImageFont.truetype('static/fonts/telagu.ttf',font_size)
    elif lang_code == 'tam':
        font = ImageFont.truetype('static/fonts/tamil.ttf',font_size)
    elif lang_code == 'ben':
        font = ImageFont.truetype('static/fonts/bengali.ttf',font_size)
    elif lang_code == 'mar':
        font = ImageFont.truetype('static/fonts/marathi.ttf',font_size)

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    x_position = frame_width
    y_position = 950

    if audio_duration:
        total_frames = int(audio_duration * fps)
        scrolling_speed = (frame_width + text_width) / total_frames
    else:
        scrolling_speed = 12

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img.paste(pil_frame, (0, 0))
        draw.text((x_position, y_position), text, font=font, fill=(255, 255, 255))

        if image_path:
            image = cv2.imread(image_path)
            image = cv2.resize(image, image_size)
            img.paste(Image.fromarray(image), (300, 120))

        x_position -= scrolling_speed
        if x_position <= -text_width:
            x_position = frame_width

        output_frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out.write(output_frame)

        if x_position >= frame_width:
            break

    cap.release()
    out.release()

def audiofromtext(lang_code, file_content):
    dir_path = download(lang_code, "static/modelpth")
    tts = TTS(dir_path)
    wav_path = "static/output/example.wav"
    tts.synthesis(file_content, wav_path=wav_path)
    return wav_path

def attach_audio_to_video(video_path, audio_path, output_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

def get_audio_duration(audio_path):
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    audio_clip.close()
    return duration

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global user_data
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if user_data and email == user_data.get('email') and password == user_data.get('password'):
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password, please try again.')
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/check', methods=['POST'])
def check():
    global user_data
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    password = request.form['password']
    
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': password  
    }
    return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/contact')
def contactus():
    return render_template('contactus.html')

@app.route('/eval')
def eval():
    return render_template('evaluation.html')

@app.route('/howtouse')
def howtouse():
    return render_template('howtouse.html')

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/process_text', methods=['POST'])
def process_text():
    file_content = request.form['text']
    language = request.form['language']
    image = request.files.get('image')
    kanascii = request.form['scrollText']
    
    if language == "kannada":
        lang_code = "kan"
        file_contentvid = kanascii
    elif language == "telugu":
        lang_code = "tel"
        file_contentvid = file_content
    elif language == "hindi":
        lang_code = "hin"
        file_contentvid = file_content
    elif language == "english":
        lang_code = "eng"
        file_contentvid = file_content
    elif language == "tamil":
        lang_code = "tam"
        file_contentvid = file_content
    elif language == "bengali":
        lang_code = "ben"
        file_contentvid = file_content
    elif language == "marathi":
        lang_code = "mar"
        file_contentvid = file_content
    else:
        lang_code = "eng"
        file_contentvid = file_content

    if image:
        image_path = os.path.join('static/uploads', image.filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image.save(image_path)
    else:
        image_path = None

    input_video_path = 'static/input_template.mp4'
    output_video_path = 'static/output/outputvideo.mp4'

    audio_path = audiofromtext(lang_code, file_content)
    audio_duration = get_audio_duration(audio_path)

    add_scrolling_text(input_video_path, output_video_path, lang_code, file_contentvid, font_size=70, image_path=image_path, audio_duration=audio_duration)

    video_path = 'static/output/outputvideo.mp4'
    output_path = 'static/output/video_with_audio.mp4'

    attach_audio_to_video(video_path, audio_path, output_path)
    
    video_url = output_path
    return jsonify({'video_url': output_path})

if __name__ == '__main__':
    app.run(debug=True)
