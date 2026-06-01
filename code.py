import streamlit as st
import json
import os
from pathlib import Path
import time
import random

# Page configuration
st.set_page_config(
    page_title="English Course Platform",
    page_icon="📚",
    layout="wide"
)

# Custom CSS - clean and simple
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    h1, h2, h3 {
        color: #2c3e50 !important;
    }
    
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
        transition: 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #2980b9;
        transform: scale(1.02);
    }
    
    .course-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 4px solid #3498db;
    }
    
    .success-message {
        animation: fadeOut 3s ease-out forwards;
    }
    
    @keyframes fadeOut {
        0% { opacity: 1; }
        70% { opacity: 1; }
        100% { opacity: 0; display: none; }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'viewing_course' not in st.session_state:
    st.session_state.viewing_course = None
if 'notification' not in st.session_state:
    st.session_state.notification = None

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

# Convert PPT to HTML slides
def convert_ppt_to_html_slides(ppt_path):
    try:
        from pptx import Presentation
        
        prs = Presentation(ppt_path)
        slides_html = []
        
        for idx, slide in enumerate(prs.slides):
            html_content = f"""
            <div style="
                background: white;
                border-radius: 10px;
                padding: 30px;
                min-height: 400px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            ">
                <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    Slide {idx + 1}
                </h3>
                <div style="font-size: 18px; line-height: 1.6; margin-top: 20px;">
            """
            
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    if idx == 0 and shape == slide.shapes[0]:
                        html_content += f"<h2 style='color: #3498db;'>{shape.text}</h2>"
                    else:
                        html_content += f"<p>{shape.text}</p>"
            
            html_content += """
                </div>
            </div>
            """
            slides_html.append(html_content)
        
        return slides_html
    except:
        return None

# Display presentation
def display_presentation(course):
    # Back button
    if st.button("← Back to courses"):
        st.session_state.viewing_course = None
        st.rerun()
    
    st.markdown(f"## {course['title']}")
    st.caption(f"Level {course['level']} | Added: {course['upload_date']}")
    st.markdown("---")
    
    slides_html = convert_ppt_to_html_slides(course["path"])
    
    if slides_html:
        if 'slide_index' not in st.session_state:
            st.session_state.slide_index = 0
        
        # Simple navigation
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            if st.button("← Previous", use_container_width=True):
                if st.session_state.slide_index > 0:
                    st.session_state.slide_index -= 1
                    st.rerun()
        
        with col2:
            st.markdown(f"<p style='text-align: center;'>Slide {st.session_state.slide_index + 1} of {len(slides_html)}</p>", unsafe_allow_html=True)
            progress = (st.session_state.slide_index + 1) / len(slides_html)
            st.progress(progress)
        
        with col3:
            if st.button("Next →", use_container_width=True):
                if st.session_state.slide_index < len(slides_html) - 1:
                    st.session_state.slide_index += 1
                    st.rerun()
        
        st.markdown("---")
        st.markdown(slides_html[st.session_state.slide_index], unsafe_allow_html=True)
        
        # Download option
        with open(course["path"], "rb") as f:
            st.download_button(
                label="Download PowerPoint",
                data=f,
                file_name=course["filename"],
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
    else:
        st.error("Cannot display this PowerPoint. Please download it instead.")
        with open(course["path"], "rb") as f:
            st.download_button(
                label="Download PowerPoint",
                data=f,
                file_name=course["filename"],
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )

# Teacher mode
def teacher_mode(metadata):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Add New Course")
        
        level = st.selectbox("Level", ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"])
        
        title = st.text_input("Course Title", placeholder="e.g., Present Simple Tense")
        description = st.text_area("Description (optional)", placeholder="What will students learn?", height=100)
        
        uploaded_file = st.file_uploader(
            "Upload PowerPoint (.ppt or .pptx)", 
            type=["ppt", "pptx"]
        )
        
        if st.button("Save Course", use_container_width=True):
            if title and uploaded_file:
                # Create folder
                level_letter = level[0]
                level_number = level[1]
                course_folder = Path(f"courses/Level_{level_letter}/{level}")
                course_folder.mkdir(parents=True, exist_ok=True)
                
                # Save file
                save_path = course_folder / uploaded_file.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Save metadata
                course_key = f"{level}_{uploaded_file.name}"
                metadata[course_key] = {
                    "title": title,
                    "description": description if description else "",
                    "level": level,
                    "path": str(save_path),
                    "filename": uploaded_file.name,
                    "upload_date": time.strftime("%Y-%m-%d")
                }
                save_metadata(metadata)
                
                st.success(f"✓ Course '{title}' saved!")
                st.balloons()
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Please add a title and file")
    
    with col2:
        st.markdown("### Statistics")
        total_courses = len(metadata)
        st.metric("Total Courses", total_courses)
        
        if metadata:
            levels_count = {}
            for course in metadata.values():
                level = course["level"]
                levels_count[level] = levels_count.get(level, 0) + 1
            
            st.markdown("**Courses per level:**")
            for level in ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]:
                if level in levels_count:
                    st.text(f"{level}: {levels_count[level]} course(s)")
    
    st.markdown("---")
    st.markdown("### Your Courses")
    
    if metadata:
        # Filter
        filter_level = st.selectbox("Filter by level", ["All"] + sorted(set(c["level"] for c in metadata.values())))
        
        for key, course in metadata.items():
            if filter_level != "All" and course["level"] != filter_level:
                continue
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                        <div class="course-card">
                            <strong>{course['title']}</strong><br>
                            <small>Level {course['level']} | {course['upload_date']}</small>
                            {f"<br><small>{course['description']}</small>" if course['description'] else ""}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"View", key=f"view_{key}"):
                        st.session_state.viewing_course = course
                        st.rerun()
                
                with col2:
                    with open(course["path"], "rb") as f:
                        st.download_button(
                            label="Download",
                            data=f,
                            file_name=course["filename"],
                            key=f"down_{key}"
                        )
                
                with col3:
                    if st.button(f"Delete", key=f"del_{key}"):
                        if delete_course(key, course["path"]):
                            st.warning(f"Course deleted")
                            time.sleep(0.5)
                            st.rerun()
    else:
        st.info("No courses yet. Upload your first course!")

# Student mode
def student_mode(metadata):
    st.markdown("### Browse Courses")
    
    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("Select Level", ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"])
    
    available_courses = {k: v for k, v in metadata.items() if v["level"] == level}
    
    if available_courses:
        st.success(f"Found {len(available_courses)} course(s) for level {level}")
        
        for key, course in available_courses.items():
            with st.expander(course['title']):
                if course.get('description'):
                    st.markdown(f"**Description:** {course['description']}")
                st.caption(f"Added: {course['upload_date']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"View Course", key=f"view_{key}"):
                        st.session_state.viewing_course = course
                        st.rerun()
                
                with col2:
                    with open(course["path"], "rb") as f:
                        st.download_button(
                            label="Download",
                            data=f,
                            file_name=course["filename"],
                            key=f"down_{key}"
                        )
    else:
        st.info(f"No courses available for level {level} yet.")

# Main
def main():
    # Simple header
    st.markdown("<h1 style='text-align: center;'>📚 English Course Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Upload, manage, and share your English courses</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 👩‍🏫 Role")
        mode = st.radio(
            "Select your role",
            ["Teacher", "Student"],
            index=0
        )
        st.markdown("---")
        st.caption("© 2024 English Course Platform")
    
    metadata = load_metadata()
    
    if st.session_state.viewing_course is not None:
        display_presentation(st.session_state.viewing_course)
    else:
        if mode == "Teacher":
            teacher_mode(metadata)
        else:
            student_mode(metadata)

if __name__ == "__main__":
    init_folders()
    main()
