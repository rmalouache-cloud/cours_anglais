import streamlit as st
import json
import os
from pathlib import Path
import time
from pptx import Presentation
from PIL import Image
import io
import tempfile
import subprocess

# Page configuration
st.set_page_config(
    page_title="✨ English Teacher's Platform ✨",
    page_icon="🌸",
    layout="wide"
)

# Custom CSS for feminine colors and animations
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 100%);
    }
    
    h1, h2, h3 {
        color: #c2185b !important;
        font-family: 'Segoe UI', 'Helvetica', cursive !important;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 10px 25px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 105, 180, 0.3);
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        background: linear-gradient(45deg, #ff1493, #c2185b);
        box-shadow: 0 6px 20px rgba(255, 20, 147, 0.4);
        transition: all 0.3s ease;
    }
    
    .stAlert {
        animation: slideIn 0.5s ease-out;
        background: linear-gradient(90deg, #ffe0f0, #fff0f5);
        border-left: 5px solid #ff69b4;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(-100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #fff0f5, #ffe6f0);
        border-radius: 15px;
        color: #c2185b;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(90deg, #ffe0f0, #ffd9e8);
        transform: translateX(5px);
    }
    
    .course-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        border: 1px solid #ffc0cb;
    }
    
    .course-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(255, 105, 180, 0.2);
        border-color: #ff69b4;
    }
    
    .stSelectbox > div > div {
        background-color: white;
        border-radius: 15px;
        border: 2px solid #ffc0cb;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #ff69b4;
        box-shadow: 0 0 10px rgba(255, 105, 180, 0.3);
    }
    
    .stRadio > div {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 15px;
        padding: 10px;
    }
    
    .stFileUploader > div {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 20px;
        border: 2px dashed #ff69b4;
    }
    
    .css-1d391kg {
        background: linear-gradient(180deg, #fff0f5, #ffe0f0);
    }
    
    @keyframes fadeInUp {
        from {
            transform: translateY(20px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    .heart {
        animation: heartbeat 1.5s ease infinite;
    }
    
    @keyframes heartbeat {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    .slide-container {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .slide-image {
        max-width: 100%;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .fullscreen-slide {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: white;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }
    
    .fullscreen-slide img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }
</style>
""", unsafe_allow_html=True)

# Initialize folders
def init_folders():
    levels = ["A", "B", "C"]
    sub_levels = ["1", "2", "3"]
    for level in levels:
        for sub in sub_levels:
            Path(f"courses/Level_{level}/{level}{sub}").mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    Path("slides_images").mkdir(exist_ok=True)

# Load metadata
def load_metadata():
    if os.path.exists("data/courses_metadata.json"):
        with open("data/courses_metadata.json", "r") as f:
            return json.load(f)
    return {}

# Save metadata
def save_metadata(metadata):
    with open("data/courses_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

# Delete course
def delete_course(course_key, course_path):
    try:
        if os.path.exists(course_path):
            os.remove(course_path)
        metadata = load_metadata()
        if course_key in metadata:
            del metadata[course_key]
            save_metadata(metadata)
        return True
    except:
        return False

# Convert PPT to images using python-pptx + pillow (simple method)
def ppt_to_images_simple(ppt_path):
    """Extract images from PowerPoint slides"""
    try:
        from pptx import Presentation
        from io import BytesIO
        
        prs = Presentation(ppt_path)
        images = []
        
        # For each slide, create an image representation
        for idx, slide in enumerate(prs.slides):
            # Create a temporary HTML representation
            slide_html = f"""
            <div style="
                width: 960px;
                min-height: 540px;
                background: white;
                padding: 40px;
                font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            ">
                <h2 style="color: #c2185b; margin-bottom: 30px;">Slide {idx + 1}</h2>
                <div style="font-size: 18px; line-height: 1.6;">
            """
            
            # Extract text from shapes
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_html += f"<p>{shape.text}</p>"
            
            slide_html += """
                </div>
            </div>
            """
            images.append(slide_html)
        
        return images
    except Exception as e:
        return None

# Display presentation with images
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # Header with back button
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("◀ Back to Courses", use_container_width=True):
            st.session_state['viewing_course'] = None
            st.rerun()
    
    with col2:
        st.markdown(f"""
            <div style="text-align: center;">
                <h2>📖 {course['title']}</h2>
                <p style="color: #c2185b;">Level {course['level']} | {course['upload_date']}</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Offer download and open in PowerPoint option for full quality
    st.info("""
        💡 **For best quality with images and colors:**
        - Download the PowerPoint file below
        - Open with PowerPoint, Google Slides, or LibreOffice
        - Use **F11** for fullscreen presentation
    """)
    
    # Download button for the original PPT
    with open(course["path"], "rb") as f:
        st.download_button(
            label="📥 Download PowerPoint (Full Quality)",
            data=f,
            file_name=course["filename"],
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Try to extract and display slide content
    try:
        from pptx import Presentation
        prs = Presentation(course["path"])
        
        if 'slide_index' not in st.session_state:
            st.session_state.slide_index = 0
        
        # Navigation
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("◀ Previous", use_container_width=True):
                if st.session_state.slide_index > 0:
                    st.session_state.slide_index -= 1
                    st.rerun()
        
        with col2:
            total_slides = len(prs.slides)
            st.write(f"**Slide {st.session_state.slide_index + 1}** of {total_slides}")
        
        with col3:
            progress = (st.session_state.slide_index + 1) / total_slides
            st.progress(progress)
        
        with col4:
            st.markdown("""
                <a href="#" onclick="document.documentElement.requestFullscreen(); return false;">
                    <button style="width:100%; background: linear-gradient(45deg, #ff69b4, #ff1493); color:white; border:none; padding:10px; border-radius:25px; cursor:pointer;">
                        🖥️ Fullscreen (F11)
                    </button>
                </a>
            """, unsafe_allow_html=True)
        
        # Display current slide content
        slides_list = list(prs.slides)
        current_slide = slides_list[st.session_state.slide_index]
        
        # Build slide content
        slide_content = []
        for shape in current_slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_content.append(shape.text)
        
        st.markdown(f"""
            <div class="slide-container">
                <h3 style="color: #ff69b4; text-align: center; margin-bottom: 30px;">Slide {st.session_state.slide_index + 1}</h3>
                <div style="font-size: 24px; line-height: 1.6; text-align: left;">
                    {'<br><br>'.join(slide_content) if slide_content else '<p style="text-align:center;">📊 Slide content - Download PowerPoint to see full formatting, images and colors!</p>'}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.caption("💡 **Tip:** Download the PowerPoint file above and open in PowerPoint/Google Slides to see all images, colors, and formatting!")
        
    except Exception as e:
        st.error(f"Error displaying slide: {e}")
        st.info("📥 Please download the PowerPoint file to view the complete presentation with images and colors.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main application
def main():
    if 'viewing_course' not in st.session_state:
        st.session_state.viewing_course = None
    
    st.markdown("""
        <div style="text-align: center; animation: fadeInUp 0.8s ease-out;">
            <h1>🌸 English Teacher's Platform 🌸</h1>
            <p style="color: #c2185b; font-size: 18px;">✨ Make learning beautiful and fun! ✨</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;" class="heart">
            📖 📝 🎓 ✏️ 📕
        </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 20px 0;">
                <h3 style="color: #ff69b4;">✨ Welcome! ✨</h3>
                <div style="font-size: 30px;">👩‍🏫</div>
            </div>
        """, unsafe_allow_html=True)
        
        mode = st.radio(
            "Choose your role:",
            ["👩‍🏫 Teacher", "👧 Student"],
            index=0
        )
        
        st.markdown("---")
        st.caption("🌸 Made with love for English teachers 🌸")
    
    metadata = load_metadata()
    
    if st.session_state.viewing_course is not None:
        display_presentation(st.session_state.viewing_course)
    else:
        if mode == "👩‍🏫 Teacher":
            teacher_mode(metadata)
        else:
            student_mode(metadata)

def teacher_mode(metadata):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🌸 Upload New Course")
        
        level_col1, level_col2 = st.columns(2)
        with level_col1:
            level = st.selectbox("📚 Main Level", ["A", "B", "C"])
        with level_col2:
            sub_level = st.selectbox("🎯 Sub-level", ["1", "2", "3"])
        
        full_level = f"{level}{sub_level}"
        
        title = st.text_input("📖 Course Title", placeholder="e.g., Present Simple Tense")
        description = st.text_area("💭 Description", placeholder="What will students learn?")
        
        uploaded_file = st.file_uploader(
            "📎 Upload PPT/PPTX File", 
            type=["ppt", "pptx"],
            help="Upload your PowerPoint presentation"
        )
        
        if st.button("💖 Save Course", use_container_width=True):
            if title and uploaded_file:
                save_path = Path(f"courses/Level_{level}/{level}{sub_level}/{uploaded_file.name}")
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                course_key = f"{full_level}_{uploaded_file.name}"
                metadata[course_key] = {
                    "title": title,
                    "description": description if description else "No description",
                    "level": full_level,
                    "path": str(save_path),
                    "filename": uploaded_file.name,
                    "upload_date": time.strftime("%Y-%m-%d %H:%M")
                }
                save_metadata(metadata)
                
                st.balloons()
                st.success(f"✨ Course '{title}' saved successfully! ✨")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("💔 Please add a title and file!")
    
    with col2:
        st.subheader("📊 Quick Stats")
        total_courses = len(metadata)
        st.info(f"📚 **Total courses:** {total_courses}")
        
        if metadata:
            levels_count = {}
            for course in metadata.values():
                level = course["level"]
                levels_count[level] = levels_count.get(level, 0) + 1
            
            st.write("**Courses per level:**")
            for level, count in sorted(levels_count.items()):
                st.progress(min(count/10, 1.0), text=f"Level {level}: {count} courses")
    
    st.markdown("---")
    st.subheader("📚 Manage Your Courses")
    
    if metadata:
        filter_level = st.selectbox("Filter by level:", ["All"] + sorted(set(c["level"] for c in metadata.values())))
        
        for key, course in metadata.items():
            if filter_level != "All" and course["level"] != filter_level:
                continue
                
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                        <div class="course-card">
                            <strong>📘 {course['title']}</strong><br>
                            <small>🎯 Level {course['level']}</small><br>
                            <small>📅 {course['upload_date']}</small><br>
                            <small>💭 {course['description']}</small>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🎬 View & Present", key=f"view_{key}"):
                        st.session_state.viewing_course = course
                        st.rerun()
                
                with col2:
                    if st.button(f"📥 Download", key=f"down_{key}"):
                        with open(course["path"], "rb") as f:
                            st.download_button(
                                label="Click to download",
                                data=f,
                                file_name=course["filename"],
                                key=f"down_btn_{key}",
                                hidden=True
                            )
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{key}"):
                        if delete_course(key, course["path"]):
                            st.warning(f"💔 Course '{course['title']}' deleted")
                            time.sleep(0.5)
                            st.rerun()
    else:
        st.info("🌸 No courses yet. Upload your first course above!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def student_mode(metadata):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    st.subheader("🎓 Browse Your Courses")
    
    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("📚 Select Main Level", ["A", "B", "C"])
    with col2:
        sub_level = st.selectbox("🎯 Select Sub-level", ["1", "2", "3"])
    
    full_level = f"{level}{sub_level}"
    
    available_courses = {k: v for k, v in metadata.items() if v["level"] == full_level}
    
    if available_courses:
        st.success(f"✨ Found {len(available_courses)} course(s) for Level {full_level} ✨")
        
        for key, course in available_courses.items():
            with st.expander(f"📖 {course['title']}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                        <div style="background: #fff0f5; padding: 15px; border-radius: 15px;">
                            <strong>💭 Description:</strong><br>
                            {course['description']}<br><br>
                            <strong>📅 Uploaded:</strong> {course['upload_date']}<br>
                            <strong>🎯 Level:</strong> {course['level']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🎬 View Course", key=f"view_student_{key}"):
                        st.session_state.viewing_course = course
                        st.rerun()
                
                with col2:
                    with open(course["path"], "rb") as f:
                        st.download_button(
                            label="📥 Download Course",
                            data=f,
                            file_name=course["filename"],
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True,
                            key=f"student_download_{key}"
                        )
                
                if st.button(f"💡 Get a tip for this course", key=f"tip_{key}"):
                    tips = [
                        "✨ Take notes while watching!",
                        "💕 Practice with a friend!",
                        "⭐ Review key vocabulary after!",
                        "🌸 Ask questions if something is unclear!"
                    ]
                    import random
                    st.info(f"💖 Tip: {random.choice(tips)}")
    else:
        st.warning(f"💔 No courses available for Level {full_level} yet.")
        st.markdown("""
            <div style="text-align: center; padding: 40px;">
                <div style="font-size: 50px;">📚✨</div>
                <p style="color: #c2185b;">Ask your teacher to upload courses for this level!</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    init_folders()
    main()
