import streamlit as st
import cv2
import numpy as np
import tempfile
import os
from scipy.signal import butter, filtfilt
import shutil
from moviepy.editor import VideoFileClip, AudioFileClip

def set_page_style():
    """Set custom page styling"""
    st.set_page_config(
        page_title="Video Effects Pro",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
        <style>
            .main { padding: 2rem; background-color: #f8f9fa; }
            .title-container {
                text-align: center;
                padding: 2rem 0;
                background: linear-gradient(90deg, #1e3799, #0c2461);
                color: white;
                border-radius: 10px;
                margin-bottom: 2rem;
            }
            .upload-container {
                background-color: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .stRadio > label { font-weight: 600; color: #2c3e50; }
            .stSlider > div > div { background-color: #3498db; }
            .stButton > button {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 0.5rem 2rem;
                border: none;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }
            .stButton > button:hover {
                background-color: #2980b9;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .stProgress > div > div { background-color: #3498db; }
            .success-message {
                background-color: #2ecc71;
                color: white;
                padding: 1rem;
                border-radius: 5px;
                text-align: center;
                margin: 1rem 0;
            }
            .error-message {
                background-color: #e74c3c;
                color: white;
                padding: 1rem;
                border-radius: 5px;
                text-align: center;
                margin: 1rem 0;
            }
            .stVideo {
                width: 100%;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
        </style>
    """, unsafe_allow_html=True)

class RealisticEarthquake:
    def __init__(self):
        self.sample_rate = 30  # FPS
        self.nyquist = self.sample_rate * 0.5
        
    def generate_seismic_motion(self, duration, magnitude):
        time = np.linspace(0, duration, int(duration * self.sample_rate))
        b, a = butter(4, [0.1, 0.5], btype='band')
        noise = np.random.normal(0, 1, len(time))
        filtered_noise = filtfilt(b, a, noise)
        amplitude = np.exp(magnitude) * 2
        motion = filtered_noise * amplitude
        return motion
        
    def apply_effect(self, frame, dx, dy, angle, blur_amount):
        height, width = frame.shape[:2]
        M = cv2.getRotationMatrix2D((width/2, height/2), angle, 1.0)
        M[:, 2] += [dx, dy]
        
        transformed = cv2.warpAffine(frame, M, (width, height))
        
        if blur_amount > 1:
            kernel_size = int(blur_amount)
            if kernel_size % 2 == 0:
                kernel_size += 1  # Ensure odd kernel size
            transformed = cv2.GaussianBlur(transformed, (kernel_size, kernel_size), 0)
        
        return transformed

def earthquake_effect(video_path, output_path, magnitude=5.5, progress_bar=None):
    # Primero procesamos el video sin audio usando OpenCV
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    
    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(video.get(cv2.CAP_PROP_FPS))
    
    # Usar un codec más compatible
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
    
    effect = RealisticEarthquake()
    duration = total_frames / fps
    
    x_motion = effect.generate_seismic_motion(duration, magnitude)
    y_motion = effect.generate_seismic_motion(duration, magnitude - 0.5)
    rotation = effect.generate_seismic_motion(duration, magnitude - 2.5)
    
    try:
        frame_count = 0
        while True:
            ret, frame = video.read()
            if not ret:
                break
                
            dx = int(x_motion[frame_count])
            dy = int(y_motion[frame_count])
            angle = rotation[frame_count]
            
            motion_magnitude = np.sqrt(dx*dx + dy*dy)
            blur_amount = min(max(motion_magnitude * 0.5, 3), 15)
            
            result = effect.apply_effect(frame, dx, dy, angle, blur_amount)
            out.write(result)
            
            frame_count += 1
            if progress_bar:
                progress_bar.progress(frame_count / total_frames)
                
    finally:
        video.release()
        out.release()
    
    # Ahora agregamos el audio original
    add_audio_to_video(temp_output, video_path, output_path)
    os.remove(temp_output)

def flip_video(video_path, output_path, flip_type, progress_bar=None):
    """Flip video based on specified type"""
    # Procesar video sin audio primero
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Determinamos las dimensiones basado en el tipo de flip
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if flip_type in ["Right", "Left"]:
        out_width, out_height = height, width
    else:
        out_width, out_height = width, height
    
    # Usar un codec más compatible
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (out_width, out_height))
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        if flip_type == "Right":
            processed_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif flip_type == "Left":
            processed_frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif flip_type == "Up":
            processed_frame = cv2.flip(frame, 0)
        elif flip_type == "Down":
            flipped = cv2.flip(frame, 0)
            processed_frame = cv2.rotate(flipped, cv2.ROTATE_180)
        elif flip_type == "Horizontal":
            processed_frame = cv2.flip(frame, 1)
        elif flip_type == "Vertical":
            processed_frame = cv2.flip(frame, 0)
        else:
            processed_frame = frame
            
        out.write(processed_frame)
        
        frame_count += 1
        if progress_bar:
            progress_bar.progress(frame_count / total_frames)
    
    cap.release()
    out.release()
    
    # Agregar audio original
    add_audio_to_video(temp_output, video_path, output_path)
    os.remove(temp_output)

def speed_up_video(video_path, output_path, speed_factor, progress_bar=None):
    """Speed up video and audio"""
    if speed_factor <= 1:
        shutil.copy2(video_path, output_path)
        return
    
    # Usar moviepy para acelerar manteniendo la sincronización de audio
    clip = VideoFileClip(video_path)
    final_clip = clip.speedx(speed_factor)
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    
    if progress_bar:
        progress_bar.progress(1.0)

def slow_motion(video_path, output_path, speed_factor, progress_bar=None):
    """Add slow motion effect with audio"""
    if speed_factor <= 1:
        shutil.copy2(video_path, output_path)
        return
    
    # Usamos moviepy para ralentizar manteniendo la sincronización de audio
    factor = 1.0 / speed_factor
    clip = VideoFileClip(video_path)
    final_clip = clip.speedx(factor)
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    
    if progress_bar:
        progress_bar.progress(1.0)

def reverse_video(video_path, output_path, progress_bar=None):
    """Reverse video and audio direction"""
    # Usamos moviepy para invertir también el audio
    clip = VideoFileClip(video_path)
    final_clip = clip.fx(lambda x: x.fl_time(lambda t: x.duration - t))
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    
    if progress_bar:
        progress_bar.progress(1.0)

def black_and_white_video(video_path, output_path, theme="normal", progress_bar=None):
    """
    Convert video to Black and White with theme options
    theme options: "normal", "white_theme", "dark_theme", "inverted"
    """
    # Procesamos primero el video sin audio
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Usar un codec más compatible
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if theme == "normal":
            # Standard grayscale
            processed_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)
        elif theme == "inverted":
            # Inverted grayscale (negative)
            inverted = cv2.bitwise_not(gray_frame)
            processed_frame = cv2.cvtColor(inverted, cv2.COLOR_GRAY2BGR)
        elif theme == "white_theme":
            # White theme: High brightness and contrast
            brightened = cv2.convertScaleAbs(gray_frame, alpha=1.2, beta=30)
            processed_frame = cv2.cvtColor(brightened, cv2.COLOR_GRAY2BGR)
        elif theme == "dark_theme":
            # Dark theme: Lower brightness, higher contrast
            darkened = cv2.convertScaleAbs(gray_frame, alpha=1.3, beta=-30)
            processed_frame = cv2.cvtColor(darkened, cv2.COLOR_GRAY2BGR)
        
        out.write(processed_frame)
        
        frame_count += 1
        if progress_bar:
            progress_bar.progress(frame_count / total_frames)
    
    cap.release()
    out.release()
    
    # Agregar audio original
    add_audio_to_video(temp_output, video_path, output_path)
    os.remove(temp_output)

def sketch_effect(video_path, output_path, progress_bar=None):
    """
    Apply sketch effect to video and preserve audio.
    """
    # Procesamos primero el video sin audio
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Usar un codec más compatible
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Convertir a escala de grises
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Efecto de sketch mejorado
        inverted = cv2.bitwise_not(gray)
        blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
        inverted_blurred = cv2.bitwise_not(blurred)
        sketch = cv2.divide(gray, inverted_blurred, scale=256.0)
        processed_frame = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
        
        out.write(processed_frame)
        
        frame_count += 1
        if progress_bar:
            progress_bar.progress(frame_count / total_frames)
    
    cap.release()
    out.release()
    
    # Agregar audio original
    add_audio_to_video(temp_output, video_path, output_path)
    os.remove(temp_output)

def add_audio_to_video(video_path, audio_path, output_path):
    """
    Combine video and audio using moviepy.
    """
    video_clip = VideoFileClip(video_path)
    audio_clip = VideoFileClip(audio_path).audio
    final_clip = video_clip.set_audio(audio_clip)
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

def save_uploaded_file(uploaded_file):
    """Save uploaded file and return path"""
    if uploaded_file is None:
        return None
        
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def main():
    set_page_style()
    
    st.markdown("""
        <div class='title-container'>
            <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>🎬 Video Effects Pro</h1>
            <p style='font-size: 1.2rem; opacity: 0.9;'>Advanced Video Effects Made Simple</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<div class='upload-container'>", unsafe_allow_html=True)
        st.markdown("### 📤 Upload Video")
        uploaded_video = st.file_uploader(
            "Choose a video file (max 25MB)",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="Supported formats: MP4, AVI, MOV, MKV",
            accept_multiple_files=False,
            key="video_uploader"
        )

        if uploaded_video and uploaded_video.size > 25 * 1024 * 1024:  # 25 MB
            st.error("File size exceeds 25 MB. Please upload a smaller file.")
            uploaded_video = None
        st.markdown("</div>", unsafe_allow_html=True)
    
    if uploaded_video:
        with col2:
            st.markdown("### 👁️ Preview")
            st.video(uploaded_video)
        
        st.markdown("---")
        st.markdown("### ⚙️ Effect Settings")
        
        effect_type = st.radio(
            "Select Effect",
            ["Earthquake", "Mirror/Flip", "Speed Up", "Slow Motion", "Reverse", "Black & White", "Sketch"],
            horizontal=True
        )
        
        if effect_type == "Earthquake":
            magnitude = st.slider(
                "Earthquake Magnitude",
                min_value=1.0,
                max_value=8.0,
                value=5.5,
                step=0.1,
                help="Higher values create stronger earthquake effects"
            )
        elif effect_type == "Mirror/Flip":
            flip_type = st.radio(
                "Flip Direction",
                ["Right", "Left", "Up", "Down", "Horizontal", "Vertical"],
                horizontal=True,
                help="""
                Right: Rotate 90° clockwise
                Left: Rotate 90° counter-clockwise
                Up: Flip vertically
                Down: Flip vertically and rotate 180°
                Horizontal: Mirror horizontally
                Vertical: Mirror vertically
                """
            )
        elif effect_type in ["Speed Up", "Slow Motion"]:
            speed = st.slider(
                "Speed Factor",
                min_value=1.0,
                max_value=4.0,
                value=2.0,
                step=0.1,
                help="Values > 1 speed up, values < 1 slow down"
            )
        elif effect_type == "Black & White":
            theme_option = st.radio(
                "Color Theme",
                ["Normal", "White Theme", "Dark Theme", "Inverted"],
                horizontal=True,
                help="""
                Normal: Standard grayscale
                White Theme: Brighter grayscale with higher contrast
                Dark Theme: Darker grayscale with higher contrast
                Inverted: Negative grayscale (black becomes white, white becomes black)
                """
            )
        
        st.markdown("---")
        col5, col6, col7 = st.columns([1, 2, 1])
        with col6:
            process_button = st.button(
                "🚀 Process Video",
                use_container_width=True,
                help="Click to apply selected effect"
            )
        
        if process_button:
            try:
                progress_bar = st.progress(0)
                status = st.empty()
                
                input_path = save_uploaded_file(uploaded_video)
                output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                
                if effect_type == "Earthquake":
                    status.text("Applying earthquake effect...")
                    earthquake_effect(input_path, output_path, magnitude, progress_bar)
                elif effect_type == "Mirror/Flip":
                    status.text("Applying mirror/flip effect...")
                    flip_video(input_path, output_path, flip_type, progress_bar)
                elif effect_type == "Speed Up":
                    status.text("Speeding up video...")
                    speed_up_video(input_path, output_path, speed, progress_bar)
                elif effect_type == "Slow Motion":
                    status.text("Slowing down video...")
                    slow_motion(input_path, output_path, speed, progress_bar)
                elif effect_type == "Reverse":
                    status.text("Reversing video...")
                    reverse_video(input_path, output_path, progress_bar)
                elif effect_type == "Black & White":
                    status.text("Converting to black and white...")
                    theme_mapping = {
                        "Normal": "normal",
                        "White Theme": "white_theme",
                        "Dark Theme": "dark_theme", 
                        "Inverted": "inverted"
                    }
                    theme = theme_mapping.get(theme_option, "normal")
                    black_and_white_video(input_path, output_path, theme, progress_bar)
                elif effect_type == "Sketch":
                    status.text("Applying Sketch effect...")
                    sketch_effect(input_path, output_path, progress_bar)
                
                progress_bar.progress(1.0)
                status.empty()
                
                st.markdown("""
                    <div class='success-message'>
                        ✨ Video processed successfully!
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### 🎉 Results")
                result_col1, result_col2 = st.columns([2, 1])
                
                with result_col1:
                    st.video(output_path)
                
                with result_col2:
                    with open(output_path, "rb") as f:
                        processed_video_data = f.read()
                    
                    st.download_button(
                        "📥 Download Processed Video",
                        data=processed_video_data,
                        file_name=f"enhanced_{uploaded_video.name}",
                        mime="video/mp4",
                        use_container_width=True
                    )
                    
                    st.markdown("#### 📊 Video Info")
                    cap = cv2.VideoCapture(output_path)
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    duration = frame_count / fps
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()
                    
                    st.markdown(f"""
                        - **Duration:** {duration:.1f} seconds
                        - **FPS:** {fps}
                        - **Resolution:** {width}x{height}
                        - **Total Frames:** {frame_count}
                    """)
                
                try:
                    shutil.rmtree(os.path.dirname(input_path))
                    os.remove(output_path)
                except Exception:
                    pass
                
            except Exception as e:
                st.markdown(f"""
                    <div class='error-message'>
                        ❌ Error: {str(e)}
                    </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# Hide Streamlit elements
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    #stStreamlitLogo {display: none;}
    a {
        text-decoration: none;
        color: inherit;
        pointer-events: none;
    }
    a:hover {
        text-decoration: none;
        color: inherit;
        cursor: default;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)