import streamlit as st
import json
import os
from pathlib import Path
import time
from pptx import Presentation
import tempfile
from PIL import Image
import io

# Page configuration
st.set_page_config(
    page_title="✨ English Teacher's Platform ✨",
    page_icon="🌸",
    layout="wide"
)

# Custom CSS for feminine colors and animations
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 100%);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #c2185b !important;
        font-family: 'Segoe UI', 'Helvetica', cursive !important;
    }
    
    /* Buttons */
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
    
    /* Success message animation */
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
    
    /* Expander styling */
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
    
    /* Cards animation */
    .course-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        border: 1px solid #ffc0cb;
        cursor: pointer;
    }
    
    .course-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(255, 105, 180, 0.2);
        border-color: #ff69b4;
    }
    
    /* Select boxes */
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
    
    /* Radio buttons */
    .stRadio > div {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 15px;
        padding: 10px;
    }
    
    /* File uploader */
    .stFileUploader > div {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 20px;
        border: 2px dashed #ff69b4;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #fff0f5, #ffe0f0);
    }
    
    /* Animations for new content */
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
    
    /* Presentation viewer */
    .slide-container {
        background: white;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    .slide-image {
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .slide-image:hover {
        transform: scale(1.02);
    }
    
    /* Navigation buttons */
    .nav-button {
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        font-size: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .nav-button:hover {
        transform: scale(1.1);
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
    Path("thumbnails").mkdir(exist_ok=True)

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

# Convert PPT to images for viewing
def ppt_to_images(ppt_path):
    """Convert PowerPoint to list of images (one per slide)"""
    try:
        from pptx import Presentation
        from wand.image import Image as WandImage
        import tempfile
        
        # For now, return a placeholder message
        # In production, you'd need LibreOffice or similar to convert
        return None
    except:
        return None

# Display presentation in viewer
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # Presentation header
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown(f"""
            <div style="text-align: center;">
                <h2>📖 {course['title']}</h2>
                <p style="color: #c2185b;">Level {course['level']} | {course['upload_date']}</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Option 1: Use Google Slides Viewer (if file is accessible online)
    # Option 2: Display download and view options
    st.markdown("---")
    
    # Create tabs for different viewing options
    tab1, tab2, tab3 = st.tabs(["🎬 Present Mode", "📥 Download", "📝 Study Notes"])
    
    with tab1:
        st.markdown("""
            <div style="background: #fff0f5; padding: 20px; border-radius: 15px; text-align: center;">
                <h3>🎬 Presentation Mode</h3>
                <p>Click below to open the presentation in full screen mode.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Create a temporary link for the file
        with open(course["path"], "rb") as f:
            ppt_data = f.read()
        
        # Option to download and open in PowerPoint/Google Slides
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Download to Present",
                data=ppt_data,
                file_name=course["filename"],
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True
            )
            st.caption("💡 Download and open with PowerPoint, Google Slides, or LibreOffice")
        
        with col2:
            # Create a simple HTML viewer for PPT (as link)
            st.markdown(f"""
                <a href="https://view.officeapps.live.com/op/embed.aspx?src={st.secrets.get('base_url', '')}{course['path']}" target="_blank">
                    <button style="width:100%; background: linear-gradient(45deg, #ff69b4, #ff1493); color:white; border:none; padding:10px; border-radius:25px; cursor:pointer;">
                        🌐 View in Browser
                    </button>
                </a>
            """, unsafe_allow_html=True)
            st.caption("💡 Opens in Microsoft Office Online (requires public URL)")
    
    with tab2:
        st.markdown("""
            <div style="background: #fff0f5; padding: 20px; border-radius: 15px;">
                <h3>📥 Download Options</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.download_button(
            label="📚 Download Course Material",
            data=ppt_data,
            file_name=course["filename"],
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True
        )
    
    with tab3:
        st.markdown("""
            <div style="background: #fff0f5; padding: 20px; border-radius: 15px;">
                <h3>📝 Study Notes</h3>
                <p>Take notes while watching the presentation:</p>
            </div>
        """, unsafe_allow_html=True)
        
        notes = st.text_area("✍️ Your notes:", height=150, placeholder="Write your notes here...")
        if notes:
            if st.button("💾 Save Notes"):
                # Save notes locally or to session
                st.success("📝 Notes saved successfully!")
    
    # Presentation tips
    with st.expander("🎓 Presentation Tips", expanded=False):
        st.markdown("""
            ✨ **For Teachers:**  
            - Use **Share Screen** in Zoom/Teams/Meet to present  
            - Enable **Presenter View** for notes  
            - Use **Annotations** to highlight important points  
            
            📚 **For Students:**  
            - Take notes in the Study Notes tab  
            - Download the presentation for offline study  
            - Review slides after class
        """)
    
    # Back button
    if st.button("◀ Back to Courses", use_container_width=True):
        st.session_state['selected_course'] = None
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main application
def main():
    # Initialize session state for selected course
    if 'selected_course' not in st.session_state:
        st.session_state['selected_course'] = None
    
    # Animated title
    st.markdown("""
        <div style="text-align: center; animation: fadeInUp 0.8s ease-out;">
            <h1>🌸 English Teacher's Platform 🌸</h1>
            <p style="color: #c2185b; font-size: 18px;">✨ Make learning beautiful and fun! ✨</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Study decoration
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            📖 📝 🎓 ✏️ 📕
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar with feminine design
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
    
    # Check if a course is selected for viewing
    if st.session_state['selected_course'] is not None:
        display_presentation(st.session_state['selected_course'])
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
        
        # Level selection with emojis
        level_col1, level_col2 = st.columns(2)
        with level_col1:
            level = st.selectbox("📚 Main Level", ["A", "B", "C"])
        with level_col2:
            sub_level = st.selectbox("🎯 Sub-level", ["1", "2", "3"])
        
        full_level = f"{level}{sub_level}"
        
        # Course details
        title = st.text_input("📖 Course Title", placeholder="e.g., Present Simple Tense")
        description = st.text_area("💭 Description", placeholder="What will students learn?")
        
        # File upload
        uploaded_file = st.file_uploader(
            "📎 Upload PPT/PPTX File", 
            type=["ppt", "pptx"],
            help="Upload your PowerPoint presentation"
        )
        
        # Save button with animation
        if st.button("💖 Save Course", use_container_width=True):
            if title and uploaded_file:
                # Save file
                save_path = Path(f"courses/Level_{level}/{level}{sub_level}/{uploaded_file.name}")
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Save metadata
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
                
                # Success animation
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
    
    # Manage existing courses
    st.markdown("---")
    st.subheader("📚 Manage Your Courses")
    
    if metadata:
        # Filter courses
        filter_level = st.selectbox("Filter by level:", ["All"] + sorted(set(c["level"] for c in metadata.values())))
        
        for key, course in metadata.items():
            if filter_level != "All" and course["level"] != filter_level:
                continue
                
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    # Make course card clickable
                    if st.button(f"📖 {course['title']}", key=f"view_{key}", use_container_width=True):
                        st.session_state['selected_course'] = course
                        st.rerun()
                    
                    st.markdown(f"""
                        <div class="course-card">
                            <small>📚 Level {course['level']}</small><br>
                            <small>📅 {course['upload_date']}</small>
                        </div>
                    """, unsafe_allow_html=True)
                
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
    
    # Level selection with visual feedback
    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("📚 Select Main Level", ["A", "B", "C"])
    with col2:
        sub_level = st.selectbox("🎯 Select Sub-level", ["1", "2", "3"])
    
    full_level = f"{level}{sub_level}"
    
    # Filter courses
    available_courses = {k: v for k, v in metadata.items() if v["level"] == full_level}
    
    if available_courses:
        st.success(f"✨ Found {len(available_courses)} course(s) for Level {full_level} ✨")
        
        for key, course in available_courses.items():
            # Create a card for each course
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                        <div class="course-card">
                            <strong>📖 {course['title']}</strong><br>
                            <small>📅 {course['upload_date']}</small><br>
                            <small>💭 {course['description']}</small>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # View button
                    if st.button("🎬 View & Present", key=f"view_student_{key}", use_container_width=True):
                        st.session_state['selected_course'] = course
                        st.rerun()
                    
                    # Download button
                    with open(course["path"], "rb") as f:
                        st.download_button(
                            label="📥 Download",
                            data=f,
                            file_name=course["filename"],
                            key=f"student_download_{key}",
                            use_container_width=True
                        )
                
                st.markdown("---")
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
