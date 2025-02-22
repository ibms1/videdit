import streamlit as st
import cv2
import numpy as np
import tempfile
import os
from datetime import datetime
from pathlib import Path
import shutil
from scipy.signal import butter, filtfilt

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
    
        # تحجيم magnitude من 0 إلى 1 إلى 1 إلى 8
        scaled_magnitude = 1 + magnitude * 7  # 1 + (0 * 7) = 1, 1 + (1 * 7) = 8
    
        # استخدام المعامل fs للتعامل مع التطبيع تلقائياً
        filter_output = butter(4, [0.5, 14.9], btype='band', fs=self.sample_rate)
        b = filter_output[0]
        a = filter_output[1]
    
        noise = np.random.normal(0, 1, len(time))
        filtered_noise = filtfilt(b, a, noise)
        amplitude = np.exp(scaled_magnitude) * 0.5  # تقليل التأثير لمنع الاهتزازات المفرطة
        motion = filtered_noise * amplitude
        return motion

    def apply_effect(self, frame, dx, dy, angle, blur_amount):
        height, width = frame.shape[:2]
        
        # تحديد محدودية حركة الكاميرا لمنع الإطار الأسود
        dx = int(np.clip(dx, -width/10, width/10))
        dy = int(np.clip(dy, -height/10, height/10))
        angle = np.clip(angle, -5, 5)  # الحد من زاوية الدوران
        
        # تطبيق مصفوفة التحويل للدوران والإزاحة
        M = cv2.getRotationMatrix2D((width/2, height/2), angle, 1.0)
        M[0, 2] += dx
        M[1, 2] += dy
        
        # تطبيق التحويلات
        transformed = cv2.warpAffine(frame, M, (width, height), 
                              borderMode=cv2.BORDER_REFLECT)
        
        # تطبيق ضبابية بسيطة فقط إذا كانت حركة الزلزال كبيرة
        if blur_amount > 3:
            kernel_size = int(min(blur_amount, 9))
            if kernel_size % 2 == 0:  # يجب أن يكون الحجم فردي
                kernel_size += 1
            transformed = cv2.GaussianBlur(transformed, (kernel_size, kernel_size), 0)
        
        return transformed

def earthquake_effect(video_path, output_path, magnitude=0.3, progress_bar=None):  # خفض القيمة الافتراضية للتأثير
    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(video.get(cv2.CAP_PROP_FPS))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    effect = RealisticEarthquake()
    duration = total_frames / fps
    
    # تقليل شدة الاهتزازات 
    magnitude = min(max(magnitude, 0.1), 0.5)  # تقييد الشدة بين 0.1 و 0.5
    
    x_motion = effect.generate_seismic_motion(duration, magnitude * 0.4)  # تقليل حركة X
    y_motion = effect.generate_seismic_motion(duration, magnitude * 0.3)  # تقليل حركة Y 
    rotation = effect.generate_seismic_motion(duration, magnitude * 0.05)  # تقليل الدوران بشكل كبير
    
    try:
        frame_count = 0
        while True:
            ret, frame = video.read()
            if not ret:
                break
                
            if frame_count < len(x_motion):
                dx = int(x_motion[frame_count])
                dy = int(y_motion[frame_count])
                angle = rotation[frame_count]
                
                motion_magnitude = np.sqrt(dx*dx + dy*dy)
                blur_amount = min(max(motion_magnitude * 0.2, 1), 7)  # تقليل شدة التمويه
                
                result = effect.apply_effect(frame, dx, dy, angle, blur_amount)
                out.write(result)
            
            frame_count += 1
            if progress_bar:
                progress_bar.progress(min(frame_count / total_frames, 1.0))
                
    finally:
        video.release()
        out.release()

def flip_video(video_path, flip_type):
    """Flip video based on specified type"""
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    if flip_type in ["Right", "Left"]:
        out = cv2.VideoWriter(temp_output, fourcc, fps, (height, width))
    else:
        out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
    
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
    
    cap.release()
    out.release()
    
    return temp_output

def speed_up_video(video_path, output_path, speed_factor, progress_bar=None):
    """Speed up video"""
    if speed_factor <= 1:
        shutil.copy2(video_path, output_path)
        return
    
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % int(speed_factor) == 0:
            out.write(frame)
        frame_count += 1
        if progress_bar:
            progress_bar.progress(frame_count / int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    
    cap.release()
    out.release()

def slow_motion(video_path, output_path, speed_factor, progress_bar=None):
    """Add slow motion effect"""
    if speed_factor <= 1:
        shutil.copy2(video_path, output_path)
        return
    
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps // int(speed_factor), (width, height))
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        for _ in range(int(speed_factor)):
            out.write(frame)
        frame_count += 1
        if progress_bar:
            progress_bar.progress(frame_count / int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    
    cap.release()
    out.release()

def reverse_video(video_path, output_path, progress_bar=None):
    """Reverse video direction"""
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    
    for frame in reversed(frames):
        out.write(frame)
        if progress_bar:
            progress_bar.progress(len(frames) / int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    
    cap.release()
    out.release()

def black_and_white_video(video_path, output_path, theme="normal", progress_bar=None):
    """
    Convert video to Black and White with theme options
    theme options: "normal", "white_theme", "dark_theme", "inverted"
    """
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
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
        
        if progress_bar:
            progress_bar.progress(cap.get(cv2.CAP_PROP_POS_FRAMES) / int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    
    cap.release()
    out.release()

def sketch_effect(video_path, output_path, progress_bar=None):
    """
    Apply sketch effect to video
    """
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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
            uploaded_video = None  # تجاهل الملف إذا كان حجمه أكبر من 25 ميجابايت

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
        
        if effect_type == "Mirror/Flip":
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
                    earthquake_effect(input_path, output_path, progress_bar=progress_bar)  # Use default magnitude
                elif effect_type == "Mirror/Flip":
                    status.text("Applying mirror/flip effect...")
                    temp_output = flip_video(input_path, flip_type)
                    shutil.copy2(temp_output, output_path)
                    os.remove(temp_output)
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
                    os.remove(input_path)
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
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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