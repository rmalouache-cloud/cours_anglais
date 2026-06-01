import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
import base64

# Page configuration
st.set_page_config(
    page_title="English Course Platform",
    page_icon="📚",
    layout="wide"
)

# Create necessary folders
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "cours_metadata.json"

# Create data folder if it doesn't exist
DATA_FILE.parent.mkdir(exist_ok=True)

# Level structure (each level has 3 sub-levels)
LEVEL_STRUCTURE = {
    "A": ["A1", "A2", "A3"],
    "B": ["B1", "B2", "B3"],
    "C": ["C1", "C2", "C3"]
}

# Function to load course metadata
def load_metadata():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Function to save metadata
def save_metadata(metadata):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

# Initialize session state
if 'cours_metadata' not in st.session_state:
    st.session_state.cours_metadata = load_metadata()

# Function for level descriptions
def get_level_description(letter, sub_level):
    descriptions = {
        "A": {"A1": "🔰 Beginner Complete", "A2": "📖 Elementary", "A3": "🗣️ Pre-Intermediate"},
        "B": {"B1": "💬 Intermediate", "B2": "📝 Upper Intermediate", "B3": "🎯 Advanced Intermediate"},
        "C": {"C1": "⚡ Advanced", "C2": "🎓 Proficiency", "C3": "🏆 Mastery"}
    }
    return descriptions.get(letter, {}).get(sub_level, "")

# Title
st.title("📚 English Course Platform")
st.markdown("---")

# Sidebar for navigation
with st.sidebar:
    st.header("🎯 Level Navigation")
    
    # Main level selection
    main_level = st.radio(
        "Choose your level",
        ["A (Beginner)", "B (Intermediate)", "C (Advanced)"],
        index=0,
        horizontal=True
    )
    
    letter = main_level[0]
    sub_levels = LEVEL_STRUCTURE[letter]
    
    sub_level = st.selectbox(
        f"Sub-level {letter}",
        sub_levels,
        format_func=lambda x: f"{x} - {get_level_description(letter, x)}"
    )
    
    # Progress indicator
    st.markdown("---")
    level_index = sub_levels.index(sub_level) + 1
    st.progress(level_index / len(sub_levels))
    st.caption(f"Progress in level {letter}: {level_index}/3")
    
    st.markdown("---")
    st.info("👩‍🏫 **Teacher Mode**: Add your PPT courses\n\n📖 **Course Mode**: Display and share")

# Main area with 2 columns
col1, col2 = st.columns([1, 2])

# COLUMN 1: Course Management
with col1:
    st.subheader(f"📤 {sub_level} - Course Management")
    st.caption(get_level_description(letter, sub_level))
    
    # Upload form
    with st.expander("➕ Add New Course", expanded=True):
        course_title = st.text_input("Course Title", placeholder="e.g., Lesson 1 - Present Simple")
        
        ppt_file = st.file_uploader(
            "Choose a PowerPoint file (.ppt or .pptx)",
            type=['ppt', 'pptx'],
            help="Upload your PowerPoint presentation"
        )
        
        description = st.text_area("Course Description", placeholder="Briefly describe the course content...", height=100)
        
        tags = st.text_input("Tags (comma separated)", placeholder="grammar, vocabulary, exercises, speaking")
        
        duration = st.number_input("Estimated Duration (minutes)", min_value=5, max_value=180, value=30, step=5)
        
        if st.button("💾 Save Course", type="primary", use_container_width=True):
            if course_title and ppt_file:
                # Convert file to base64 for storage in JSON
                file_bytes = ppt_file.read()
                file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                
                # Create metadata
                course_info = {
                    "id": f"{letter}_{sub_level}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "title": course_title,
                    "file_base64": file_base64,
                    "filename": ppt_file.name,
                    "description": description,
                    "tags": [tag.strip() for tag in tags.split(",")] if tags else [],
                    "duration": duration,
                    "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "presentation",
                    "level": f"{letter}{sub_level[1:]}"
                }
                
                # Save to metadata
                key = f"{letter}/{sub_level}"
                if key not in st.session_state.cours_metadata:
                    st.session_state.cours_metadata[key] = []
                
                st.session_state.cours_metadata[key].append(course_info)
                save_metadata(st.session_state.cours_metadata)
                
                st.success(f"✅ Course '{course_title}' saved successfully!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Please fill in the title and select a PPT file")
    
    # List of existing courses
    st.subheader("📋 Available Courses")
    
    key = f"{letter}/{sub_level}"
    course_list = st.session_state.cours_metadata.get(key, [])
    
    if course_list:
        st.caption(f"📊 {len(course_list)} course(s) available")
        
        for i, course in enumerate(course_list):
            with st.container():
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"**📌 {course['title']}**")
                    st.caption(f"⏱️ {course['duration']} min | 📅 {course['date_added'].split()[0]}")
                    if course.get('tags'):
                        st.caption(f"🏷️ {', '.join(course['tags'][:3])}")
                with col_b:
                    if st.button("🗑️", key=f"del_{letter}_{sub_level}_{i}", help="Delete this course"):
                        st.session_state.cours_metadata[key].pop(i)
                        save_metadata(st.session_state.cours_metadata)
                        st.rerun()
                st.divider()
    else:
        st.info("📭 No courses for this level")
        st.caption("👆 Click 'Add New Course' to get started")

# COLUMN 2: Course Display
with col2:
    st.subheader(f"📖 {sub_level} - Course Display")
    st.caption("Screen sharing mode - Enable presentation mode below")
    
    presentation_mode = st.toggle("🎬 Presentation Mode (optimized for screen sharing)", value=False)
    
    if course_list:
        course_titles = [c["title"] for c in course_list]
        
        # Search if many courses
        if len(course_list) > 5:
            search = st.text_input("🔍 Search courses", placeholder="Title or tags...")
            if search:
                course_titles = [c["title"] for c in course_list 
                              if search.lower() in c["title"].lower() 
                              or any(search.lower() in tag.lower() for tag in c.get("tags", []))]
        
        selected_course_title = st.selectbox("Choose a course to display", course_titles)
        current_course = next((c for c in course_list if c["title"] == selected_course_title), None)
        
        if current_course:
            if presentation_mode:
                # Presentation mode
                st.markdown("""
                <style>
                .presentation-container {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem;
                    border-radius: 15px;
                    color: white;
                }
                .presentation-content {
                    background-color: white;
                    padding: 2rem;
                    border-radius: 10px;
                    color: #333;
                    margin-top: 1rem;
                }
                .course-title {
                    color: white;
                    text-align: center;
                    font-size: 2rem;
                    margin-bottom: 0.5rem;
                }
                .course-info {
                    text-align: center;
                    color: rgba(255,255,255,0.9);
                    margin-bottom: 1rem;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="presentation-container">
                    <h1 class="course-title">{current_course['title']}</h1>
                    <div class="course-info">
                        {sub_level} • {current_course['duration']} min • Added on {current_course['date_added'].split()[0]}
                    </div>
                """, unsafe_allow_html=True)
                
                if current_course.get('description'):
                    st.markdown(f"""
                    <div style="background-color: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        📝 {current_course['description']}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('<div class="presentation-content">', unsafe_allow_html=True)
                
                # Display the PPT (decoded from base64)
                if current_course.get('file_base64'):
                    st.info(f"📊 File: {current_course['filename']}")
                    
                    # Download button
                    file_bytes = base64.b64decode(current_course['file_base64'])
                    st.download_button(
                        label="📥 Download Presentation",
                        data=file_bytes,
                        file_name=current_course['filename'],
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                    
                    st.success("💡 **Screen Sharing Tips:**")
                    st.caption("1. Download the PowerPoint file")
                    st.caption("2. Open it with PowerPoint")
                    st.caption("3. Start slideshow (press F5)")
                    st.caption("4. Share your screen in your video conferencing tool")
                    
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.info("💡 **Tip:** Press **F11** for full screen browser mode")
                
            else:
                # Normal mode
                st.markdown(f"### 📄 {current_course['title']}")
                
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("Level", sub_level)
                with col_info2:
                    st.metric("Duration", f"{current_course['duration']} min")
                with col_info3:
                    st.metric("Added on", current_course['date_added'].split()[0])
                
                if current_course.get('description'):
                    st.markdown("**Description:**")
                    st.info(current_course['description'])
                
                if current_course.get('tags'):
                    st.markdown("**Tags:**")
                    st.markdown(", ".join([f"`{tag}`" for tag in current_course['tags']]))
                
                st.markdown("---")
                
                # Download link
                if current_course.get('file_base64'):
                    file_bytes = base64.b64decode(current_course['file_base64'])
                    st.download_button(
                        label="📥 Download Presentation",
                        data=file_bytes,
                        file_name=current_course['filename'],
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                    
                    st.success("💡 **To share your screen:**")
                    st.caption("1. Download the PPT file")
                    st.caption("2. Open with PowerPoint")
                    st.caption("3. Start the slideshow (F5)")
                    st.caption("4. Share your screen in your video call")
    else:
        st.info("👆 **No courses available**")
        st.caption("Add your first course by uploading a PPT file in the left column")

# Footer
st.markdown("---")
st.caption(f"✨ English Course Platform - Levels A1→A3, B1→B3, C1→C3 | Courses are permanently saved")
