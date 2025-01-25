import streamlit as st
import cv2
import numpy as np
import tempfile
import os
import subprocess

# Frame processing functions
def process_frame_for_motion(frame, prev_frame, invert=False):
    """Process frame for motion detection"""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray_frame, gray_prev_frame)
    _, motion_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    result = cv2.bitwise_not(motion_mask) if not invert else motion_mask
    return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

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

def frames_to_video(frames, output_path, fps):
    """Convert frames to video"""
    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    for frame in frames:
        out.write(frame)
    out.release()

def extract_audio(video_path, audio_output_path):
    """Extract audio from video"""
    command = f"ffmpeg -i {video_path} -q:a 0 -map a {audio_output_path} -y"
    subprocess.call(command, shell=True)

def merge_audio_video(video_path, audio_path, output_path):
    """Merge audio and video"""
    command = f"ffmpeg -i {video_path} -i {audio_path} -c:v copy -c:a aac -strict experimental {output_path} -y"
    subprocess.call(command, shell=True)

def speed_up_video(video_path, speed_factor):
    """Speed up video"""
    if speed_factor <= 1:
        return video_path
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Select frames with the new speed factor
    frames = []
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % int(speed_factor) == 0:
            frames.append(frame)
        frame_count += 1
    
    # Create a new video writer with the original FPS
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (frame_width, frame_height))
    
    for frame in frames:
        out.write(frame)
    
    cap.release()
    out.release()
    return temp_output

def slow_motion(video_path, speed_factor):
    """Add slow motion effect"""
    if speed_factor <= 1:
        return video_path
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Duplicate frames to create slow motion effect
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Duplicate each frame multiple times based on speed factor
        for _ in range(int(speed_factor)):
            frames.append(frame)
    
    # Create a new video writer with reduced FPS
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps // int(speed_factor), (frame_width, frame_height))
    
    for frame in frames:
        out.write(frame)
    
    cap.release()
    out.release()
    return temp_output

def reverse_video(video_path):
    """Reverse video direction"""
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (frame_width, frame_height))
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

def save_uploaded_file(uploaded_file):
    """Save uploaded file"""
    temp_dir = tempfile.mkdtemp()
    if uploaded_file is not None:
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

def flip_video(video_path, flip_type):
    """Flip video based on specified type"""
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (frame_width, frame_height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Determine flip type
        if flip_type == "Horizontal Right":
            flipped_frame = cv2.flip(frame, 1)  # Horizontal flip
        elif flip_type == "Horizontal Left":
            flipped_frame = cv2.flip(frame, 1)  # Horizontal flip
        elif flip_type == "Vertical Right":
            flipped_frame = cv2.flip(frame, 0)  # Vertical flip
        elif flip_type == "Vertical Left":
            flipped_frame = cv2.flip(frame, 0)  # Vertical flip
        else:
            flipped_frame = frame
        
        out.write(flipped_frame)
    
    cap.release()
    out.release()
    return temp_output

def grayscale_video(video_path):
    """Convert video to grayscale"""
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (frame_width, frame_height), isColor=False)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        out.write(cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR))
    
    cap.release()
    out.release()
    return temp_output

def blur_video(video_path, blur_strength=15):
    """Add blur effect to video"""
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (frame_width, frame_height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        blurred_frame = cv2.GaussianBlur(frame, (blur_strength, blur_strength), 0)
        out.write(blurred_frame)
    
    cap.release()
    out.release()
    return temp_output

def main():
    st.set_page_config(page_title="Advanced Video Editor", layout="wide")
    
    st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1 style='font-size: 2.5rem; font-weight: 600;'>🎬 Advanced Video Editor</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Video upload area
    uploaded_video = st.file_uploader("Upload Video", type=['mp4', 'avi', 'mov', 'mkv'])
    
    if uploaded_video:
        # Save uploaded video to a temporary file
        input_path = save_uploaded_file(uploaded_video)
        
        # Extract audio from the original video and store it in a variable
        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
        extract_audio(input_path, audio_path)
        
        # Display uploaded video
        st.video(uploaded_video)
        
        # Effects list
        st.markdown("### Available Effects")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            background_theme = st.radio(
                "Motion Background",
                ["None", "Dark", "Light"],  # Corrected order
                horizontal=True
            )
        
        with col2:
            speed_effect = st.radio(
                "Playback Speed",
                ["None", "Speed Up", "Slow Down"],
                horizontal=True
            )
        
        with col3:
            direction = st.radio(
                "Video Direction",
                ["None", "Forward", "Reverse"],
                horizontal=True
            )
        
        with col4:
            flip_type = st.radio(
                "Flip Video",
                ["None", "→", "←", "↑", "↓"],  # Replaced with arrows
                horizontal=True
            )
        
        # Additional effects
        st.markdown("### Additional Effects")
        col5, col6 = st.columns(2)
        
        with col5:
            grayscale_effect = st.checkbox("Remove Colors (Grayscale)")
        
        with col6:
            blur_effect = st.checkbox("Add Blur Effect")
            if blur_effect:
                blur_strength = st.slider("Blur Strength", 1, 30, 15)
        
        # Speed control
        if speed_effect != "None":
            speed = st.slider("Speed Factor", 1.0, 4.0, 2.0, 0.1)
            st.caption(f"Speed Multiplier: {speed}x")
        
        # Apply effects button
        if st.button("Apply Effects", type="primary"):
            with st.spinner("Processing..."):
                try:
                    # Apply effects in order
                    current_path = input_path
                    
                    # Speed and direction effects
                    if direction == "Reverse":
                        current_path = reverse_video(current_path)
                    if speed_effect == "Speed Up":
                        current_path = speed_up_video(current_path, speed)
                    elif speed_effect == "Slow Down":
                        current_path = slow_motion(current_path, speed)
                    
                    # Flip effect
                    if flip_type != "None":
                        # Map arrows to flip types
                        flip_mapping = {
                            "→": "Horizontal Right",
                            "←": "Horizontal Left",
                            "↑": "Vertical Right",
                            "↓": "Vertical Left"
                        }
                        current_path = flip_video(current_path, flip_mapping[flip_type])
                    
                    # Motion detection effect
                    if background_theme != "None":
                        frames = video_to_frames(current_path)
                        processed_frames = []
                        
                        progress_bar = st.progress(0)
                        for i in range(1, len(frames)):
                            processed_frame = process_frame_for_motion(
                                frames[i], 
                                frames[i-1], 
                                invert=(background_theme == "Light")
                            )
                            processed_frames.append(processed_frame)
                            progress_bar.progress(i / (len(frames) - 1))
                        
                        final_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                        frames_to_video(processed_frames, final_output, 30)
                        current_path = final_output
                    
                    # Additional effects
                    if grayscale_effect:
                        current_path = grayscale_video(current_path)
                    
                    if blur_effect:
                        current_path = blur_video(current_path, blur_strength)
                    
                    # Merge audio back with the processed video
                    final_output_with_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    merge_audio_video(current_path, audio_path, final_output_with_audio)
                    
                    st.success("Video processed successfully!")
                    st.video(final_output_with_audio)
                    
                    # Download button
                    with open(final_output_with_audio, "rb") as f:
                        st.download_button(
                            "Download Processed Video",
                            f,
                            file_name=f"processed_{uploaded_video.name}",
                            mime="video/mp4"
                        )
                    
                    # Clean up temporary files
                    os.remove(input_path)
                    os.remove(audio_path)
                    os.remove(current_path)
                    os.remove(final_output_with_audio)
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()