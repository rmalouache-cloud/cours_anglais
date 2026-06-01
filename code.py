import streamlit as st
import json
import os
from pathlib import Path
import time
import base64
from PIL import Image
import io

# Page configuration
st.set_page_config(
    page_title="✨ English Teacher's Platform ✨",
    page_icon="🌸",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 100%);
    }
    
    h1, h2, h3 {
        color: #c2185b !important;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 12px 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
    
    .course-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border: 1px solid #ffc0cb;
    }
    
    .course-card:hover {
        transform: translateY(-5px);
    }
    
    @keyframes fadeInUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    .slide-content {
        font-family: 'Segoe UI', Arial, sans-serif;
        line-height: 1.6;
    }
    
    .slide-content table {
        border-collapse: collapse;
        width: 100%;
        margin: 15px 0;
    }
    
    .slide-content td, .slide-content th {
        border: 1px solid #ddd;
        padding: 8px;
    }
    
    .slide-content img {
        max-width: 100%;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>

<script>
    function toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }
</script>
""", unsafe_allow_html=True)

# Initialize folders
def init_folders():
    levels = ["A", "B", "C"]
    sub_levels = ["1", "2", "3"]
    for level in levels:
        for sub in sub_levels:
            Path(f"courses/Level_{level}/{level}{sub}").mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(exist_ok=True)

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

# Extract all text from PPT
def extract_ppt_content(ppt_path):
    """Extract all content from PPT (text, images, tables)"""
    try:
        from pptx import Presentation
        import html
        
        prs = Presentation(ppt_path)
        slides_content = []
        
        for slide_idx, slide in enumerate(prs.slides):
            slide_html = f"""
            <div style="
                background: white;
                border-radius: 15px;
                padding: 40px;
                min-height: 500px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            ">
                <div style="border-bottom: 3px solid #ff69b4; margin-bottom: 20px; padding-bottom: 10px;">
                    <span style="color: #ff69b4; font-size: 14px;">Slide {slide_idx + 1}</span>
                </div>
                <div class="slide-content">
            """
            
            # Extract text from shapes
            for shape in slide.shapes:
                # Text content
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        para_text = ""
                        for run in paragraph.runs:
                            para_text += html.escape(run.text)
                        if para_text.strip():
                            # Check if it's a title (large text or first shape)
                            if slide_idx == 0 and shape == slide.shapes[0]:
                                slide_html += f"<h2 style='color: #ff69b4;'>{para_text}</h2>"
                            else:
                                slide_html += f"<p style='margin: 10px 0;'>{para_text}</p>"
                
                # Images
                try:
                    if shape.shape_type == 13:  # Picture
                        image = shape.image
                        img_base64 = base64.b64encode(image.blob).decode('utf-8')
                        slide_html += f"""
                            <div style="text-align: center; margin: 15px 0;">
                                <img src="data:image/{image.ext};base64,{img_base64}" 
                                     style="max-width: 100%; border-radius: 10px;">
                            </div>
                        """
                except:
                    pass
                
                # Tables
                if shape.has_table:
                    table = shape.table
                    slide_html += '<table style="width: 100%; border-collapse: collapse;">'
                    for row in table.rows:
                        slide_html += '<tr>'
                        for cell in row.cells:
                            slide_html += f'<td style="border: 1px solid #ddd; padding: 8px;">{html.escape(cell.text)}</td>'
                        slide_html += '</tr>'
                    slide_html += '</table>'
            
            slide_html += """
                </div>
            </div>
            """
            slides_content.append(slide_html)
        
        return slides_content
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Display presentation
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # Navigation bar
    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
    
    with col1:
        if st.button("◀ Back", use_container_width=True):
            st.session_state['viewing_course'] = None
            st.rerun()
    
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>{course['title']}</h3>", unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"<p style='text-align: center;'>Level {course['level']}</p>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <button onclick="toggleFullscreen()" style="
                background: linear-gradient(45deg, #ff69b4, #ff1493);
                color: white;
                border: none;
                border-radius: 25px;
                padding: 8px 16px;
                font-weight: bold;
                cursor: pointer;
                width: 100%;
            ">
                🖥️ FULLSCREEN
            </button>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Extract PPT content
    slides = extract_ppt_content(course["path"])
    
    if slides:
        # Initialize slide index
        if 'slide_index' not in st.session_state:
            st.session_state.slide_index = 0
        
        # Slide navigation
        nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
        
        with nav_col1:
            if st.button("◀◀ PREVIOUS", use_container_width=True):
                if st.session_state.slide_index > 0:
                    st.session_state.slide_index -= 1
                    st.rerun()
        
        with nav_col2:
            st.markdown(f"<p style='text-align: center; font-size: 18px;'>Slide {st.session_state.slide_index + 1} of {len(slides)}</p>", unsafe_allow_html=True)
            progress = (st.session_state.slide_index + 1) / len(slides)
            st.progress(progress)
        
        with nav_col3:
            if st.button("NEXT ▶▶", use_container_width=True):
                if st.session_state.slide_index < len(slides) - 1:
                    st.session_state.slide_index += 1
                    st.rerun()
        
        st.markdown("---")
        
        # Display current slide
        st.markdown(slides[st.session_state.slide_index], unsafe_allow_html=True)
        
        # Keyboard navigation hint
        st.info("💡 **Tip:** Click FULLSCREEN button and use ◀ ▶ buttons to navigate")
        
    else:
        st.error("❌ Cannot display PowerPoint. Please check the file format.")
        # Fallback: download button
        with open(course["path"], "rb") as f:
            st.download_button(
                label="📥 Download PowerPoint",
                data=f,
                file_name=course["filename"],
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main application
def main():
    if 'viewing_course' not in st.session_state:
        st.session_state.viewing_course = None
    
    # Title
    st.markdown("""
        <div style="text-align: center; animation: fadeInUp 0.8s ease-out;">
            <h1>🌸 English Teacher's Platform 🌸</h1>
            <p style="color: #c2185b; font-size: 18px;">✨ Make learning beautiful and fun! ✨</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px; font-size: 30px;">
            📖 📝 🎓 ✏️ 📕
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
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
                course_folder = Path(f"courses/Level_{level}/{level}{sub_level}")
                course_folder.mkdir(parents=True, exist_ok=True)
                
                save_path = course_folder / uploaded_file.name
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
                    
                    if st.button(f"🎬 View", key=f"view_{key}"):
                        st.session_state.viewing_course = course
                        st.rerun()
                
                with col2:
                    if st.button(f"📥 Download", key=f"down_{key}"):
                        with open(course["path"], "rb") as f:
                            st.download_button(
                                label="Click",
                                data=f,
                                file_name=course["filename"],
                                key=f"down_btn_{key}",
                                hidden=True
                            )
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{key}"):
                        if delete_course(key, course["path"]):
                            st.warning(f"Course deleted")
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
                    
                    if st.button(f"🎬 View", key=f"view_student_{key}"):
                        st.session_state.viewing_course = course
                        st.rerun()
                
                with col2:
                    if st.button(f"💡 Tip", key=f"tip_{key}"):
                        tips = ["✨ Take notes!", "💕 Practice daily!", "⭐ Review vocabulary!"]
                        import random
                        st.info(random.choice(tips))
    else:
        st.warning(f"💔 No courses available for Level {full_level} yet.")
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    init_folders()
    main()
