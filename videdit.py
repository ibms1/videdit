import streamlit as st
import cv2
import numpy as np
import tempfile
import os
from datetime import datetime
from pathlib import Path
import shutil

def set_page_style():
    """Set custom page styling"""
    st.set_page_config(
        page_title="Video Editor Pro",
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

def process_frame_for_motion(frame, prev_frame, invert=False):
    """Process frame for motion detection"""
    if frame is None or prev_frame is None:
        return None
    
    try:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray_frame, gray_prev_frame)
        _, motion_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        result = cv2.bitwise_not(motion_mask) if not invert else motion_mask
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    except Exception as e:
        st.error(f"Error processing frame: {str(e)}")
        return None

def video_to_frames(video_path):
    """Convert video to frames"""
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def frames_to_video(frames, output_path, fps, input_video_path=None):
    """Convert frames to video and preserve audio if possible"""
    try:
        if not frames or len(frames) == 0:
            raise ValueError("No frames to process")
            
        valid_frames = [f for f in frames if f is not None]
        if not valid_frames:
            raise ValueError("No valid frames found")
            
        height, width, _ = valid_frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
        
        out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
        for frame in valid_frames:
            out.write(frame)
        out.release()
        
        shutil.copy2(temp_output, output_path)
        
        try:
            os.unlink(temp_output)
        except:
            pass
            
    except Exception as e:
        st.error(f"Error saving video: {str(e)}")
        raise e

def speed_up_video(video_path, speed_factor):
    """Speed up video"""
    if speed_factor <= 1:
        return video_path
        
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % int(speed_factor) == 0:
            out.write(frame)
        frame_count += 1
    
    cap.release()
    out.release()
    return temp_output

def slow_motion(video_path, speed_factor):
    """Add slow motion effect"""
    if speed_factor <= 1:
        return video_path
        
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps//int(speed_factor), (width, height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        for _ in range(int(speed_factor)):
            out.write(frame)
    
    cap.release()
    out.release()
    return temp_output

def reverse_video(video_path):
    """Reverse video direction"""
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
    
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    
    for frame in reversed(frames):
        out.write(frame)
    
    cap.release()
    out.release()
    return temp_output

def flip_video(video_path, flip_type):
    """
    Flip video based on specified type
    flip_types: Right, Left, Up, Down, Horizontal, Vertical
    """
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # تحديد أبعاد الإخراج بناءً على نوع الدوران
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
    
    # Header
    st.markdown("""
        <div class='title-container'>
            <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>🎬 Video Editor Pro</h1>
            <p style='font-size: 1.2rem; opacity: 0.9;'>Professional Video Editing Made Simple</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Upload Section
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<div class='upload-container'>", unsafe_allow_html=True)
        st.markdown("### 📤 Upload Video")
        uploaded_video = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="Supported formats: MP4, AVI, MOV, MKV"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    if uploaded_video:
        with col2:
            st.markdown("### 👁️ Preview")
            st.video(uploaded_video)
        
        # Effects Section
        st.markdown("---")
        st.markdown("### ⚙️ Video Effects")
        
        tabs = st.tabs(["🎨 Basic Effects", "🔧 Advanced Settings"])
        
        with tabs[0]:
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("#### Motion Effects")
                background_theme = st.radio(
                    "🎭 Motion Background",
                    ["None", "Light Theme", "Dark Theme"],
                    horizontal=True
                )
                
                st.markdown("#### Direction")
                direction = st.radio(
                    "🔄 Video Direction",
                    ["Normal", "Reverse"],
                    horizontal=True
                )
            
            with col4:
                st.markdown("#### Speed Settings")
                speed_effect = st.radio(
                    "⏱️ Playback Speed",
                    ["Normal", "Speed Up", "Slow Motion"],
                    horizontal=True
                )
                
                st.markdown("#### Orientation")
                flip_type = st.radio(
                    "↔️ Flip Video",
                    ["None", "Right", "Left", "Up", "Down", "Horizontal", "Vertical"],
                    horizontal=True,
                    help="""
                    Right: تدوير 90 درجة يميناً
                    Left: تدوير 90 درجة يساراً
                    Up: قلب لأعلى
                    Down: قلب لأسفل
                    Horizontal: قلب أفقي
                    Vertical: قلب عمودي
                    """
                )
        
        with tabs[1]:
            if speed_effect != "Normal":
                st.markdown("#### 🎚️ Speed Control")
                speed = st.slider(
                    "Adjust Speed Factor",
                    min_value=1.0,
                    max_value=4.0,
                    value=2.0,
                    step=0.1,
                    help="Values > 1 speed up, values < 1 slow down"
                )
                st.info(f"Video will be {'sped up' if speed > 1 else 'slowed down'} by {speed}x")
        
        # Process Button
        st.markdown("---")
        col5, col6, col7 = st.columns([1, 2, 1])
        with col6:
            process_button = st.button(
                "🚀 Process Video",
                use_container_width=True,
                help="Click to apply selected effects"
            )
        
        if process_button:
            try:
                # Show processing status
                progress_bar = st.progress(0)
                status = st.empty()
                
                # Save uploaded video
                input_path = save_uploaded_file(uploaded_video)
                current_path = input_path
                
                # Apply effects
                if direction == "Reverse":
                    status.text("Reversing video...")
                    current_path = reverse_video(current_path)
                    progress_bar.progress(0.25)
                
                if speed_effect != "Normal":
                    status.text("Adjusting video speed...")
                    if speed_effect == "Speed Up":
                        current_path = speed_up_video(current_path, speed)
                    else:
                        current_path = slow_motion(current_path, speed)
                    progress_bar.progress()
                if flip_type != "None":
                    status.text("Flipping video...")
                    current_path = flip_video(current_path, flip_type)
                    progress_bar.progress(0.75)
                
                if background_theme != "None":
                    status.text("Applying motion effects...")
                    try:
                        frames = video_to_frames(current_path)
                        processed_frames = []
                        
                        for i in range(1, len(frames)):
                            try:
                                processed_frame = process_frame_for_motion(
                                    frames[i],
                                    frames[i-1],
                                    invert=(background_theme == "Light Theme")
                                )
                                if processed_frame is not None:
                                    processed_frames.append(processed_frame)
                                progress_bar.progress((i + 1) / len(frames))
                            except Exception as e:
                                st.error(f"Error processing frame {i}: {str(e)}")
                                continue
                        
                        if processed_frames:
                            final_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                            frames_to_video(processed_frames, final_output, 30, input_video_path=current_path)
                            current_path = final_output
                        else:
                            st.error("No frames were processed successfully")
                            
                    except Exception as e:
                        st.error(f"Error applying motion effects: {str(e)}")
                        return
                
                progress_bar.progress(1.0)
                status.empty()
                
                # Success message
                st.markdown("""
                    <div class='success-message'>
                        ✨ Video processed successfully!
                    </div>
                """, unsafe_allow_html=True)
                
                # Results section
                st.markdown("### 🎉 Results")
                result_col1, result_col2 = st.columns([2, 1])
                
                with result_col1:
                    st.video(current_path)
                
                with result_col2:
                    # Read the processed video file
                    with open(current_path, "rb") as f:
                        processed_video_data = f.read()
                    
                    st.download_button(
                        "📥 Download Processed Video",
                        data=processed_video_data,
                        file_name=f"enhanced_{uploaded_video.name}",
                        mime="video/mp4",
                        use_container_width=True
                    )
                    
                    # Show video information
                    st.markdown("#### 📊 Video Info")
                    cap = cv2.VideoCapture(current_path)
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
                
                # Cleanup
                try:
                    os.remove(input_path)
                    if current_path != input_path:
                        os.remove(current_path)
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
