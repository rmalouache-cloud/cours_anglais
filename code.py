import streamlit as st
import json
import os
from pathlib import Path
import time
from PIL import Image
import io
import base64

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
    
    .slide-container {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    @keyframes fadeInUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Fullscreen styles */
    .fullscreen-enabled {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        z-index: 9999 !important;
        background: white !important;
        overflow-y: auto !important;
        padding: 20px !important;
    }
</style>

<script>
    function toggleFullscreen(elementId) {
        var elem = document.getElementById(elementId);
        if (!document.fullscreenElement) {
            elem.requestFullscreen().catch(err => {
                console.log(`Error attempting to enable fullscreen: ${err.message}`);
            });
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
            Path(f"courses/Level_{level}/{level}{sub}/images").mkdir(parents=True, exist_ok=True)
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
def delete_course(course_key, course_path, images_folder):
    try:
        if os.path.exists(course_path):
            os.remove(course_path)
        if os.path.exists(images_folder):
            import shutil
            shutil.rmtree(images_folder)
        metadata = load_metadata()
        if course_key in metadata:
            del metadata[course_key]
            save_metadata(metadata)
        return True
    except:
        return False

def extract_image_from_slide(slide, image_idx):
    """Extract image from slide and convert to base64"""
    try:
        for shape in slide.shapes:
            if hasattr(shape, "image"):
                image_bytes = shape.image.blob
                img = Image.open(io.BytesIO(image_bytes))
                # Resize if too large
                if img.width > 800:
                    ratio = 800 / img.width
                    new_size = (800, int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                return f'<img src="data:image/png;base64,{img_base64}" style="max-width: 100%; border-radius: 10px; margin: 10px 0;" />'
    except:
        pass
    return None

# Convert PPT to HTML slides with images
def convert_ppt_to_html_slides(ppt_path):
    """Convert PPT to HTML slides that preserve formatting and images"""
    try:
        from pptx import Presentation
        
        prs = Presentation(ppt_path)
        slides_html = []
        
        for idx, slide in enumerate(prs.slides):
            html_content = f"""
            <div id="slide_{idx}" class="slide-container" style="
                width: 100%;
                min-height: 500px;
                background: white;
                border-radius: 15px;
                padding: 40px;
                font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            ">
                <h2 style="color: #c2185b; border-bottom: 2px solid #ff69b4; padding-bottom: 10px; margin-bottom: 20px;">
                    Slide {idx + 1}
                </h2>
                <div style="font-size: 18px; line-height: 1.6;">
            """
            
            # Extract and organize content
            has_title = False
            content_items = []
            
            for shape in slide.shapes:
                # Check for images first
                if hasattr(shape, "image"):
                    img_html = extract_image_from_slide(slide, idx)
                    if img_html:
                        content_items.append(img_html)
                
                # Extract text
                if hasattr(shape, "text") and shape.text.strip():
                    text = shape.text.strip()
                    
                    # Check if it's a title (often larger font or first shape)
                    if hasattr(shape, "text_frame") and shape.text_frame.paragraphs:
                        first_para = shape.text_frame.paragraphs[0]
                        if first_para.font.size and first_para.font.size.pt >= 24:
                            content_items.append(f"<h3 style='color: #ff69b4; margin-top: 15px;'>{text}</h3>")
                            has_title = True
                        else:
                            content_items.append(f"<p style='margin: 10px 0;'>{text}</p>")
                    else:
                        content_items.append(f"<p style='margin: 10px 0;'>{text}</p>")
            
            # If no title detected, make first text item a title
            if not has_title and content_items:
                for i, item in enumerate(content_items):
                    if '<p' in item and 'margin' in item:
                        content_items[i] = item.replace('<p', '<h3', 1).replace('</p>', '</h3>')
                        content_items[i] = content_items[i].replace('margin: 10px 0;', 'color: #ff69b4; margin-top: 15px;')
                        break
            
            # Add all content to HTML
            for item in content_items:
                html_content += item
            
            # If no content at all
            if not content_items:
                html_content += "<p style='color: #999; text-align: center;'>No content on this slide</p>"
            
            html_content += """
                </div>
            </div>
            """
            slides_html.append(html_content)
        
        return slides_html
    except Exception as e:
        st.error(f"Error converting PPT: {str(e)}")
        return None

# Display presentation
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # Unique ID for fullscreen container
    container_id = f"presentation_container_{int(time.time())}"
    
    # Back button
    if st.button("◀ Back to Courses", use_container_width=False):
        st.session_state['viewing_course'] = None
        st.rerun()
    
    # Title
    st.markdown(f"""
        <div style="text-align: center;">
            <h2>📖 {course['title']}</h2>
            <p style="color: #c2185b;">Level {course['level']} | {course['upload_date']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Convert PPT to HTML slides
    slides_html = convert_ppt_to_html_slides(course["path"])
    
    if slides_html:
        # Initialize slide index
        if 'slide_index' not in st.session_state:
            st.session_state.slide_index = 0
        
        # Navigation buttons
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("◀◀ PREVIOUS", use_container_width=True):
                if st.session_state.slide_index > 0:
                    st.session_state.slide_index -= 1
                    st.rerun()
        
        with col2:
            st.markdown(f"<h3 style='text-align: center;'>Slide {st.session_state.slide_index + 1} / {len(slides_html)}</h3>", unsafe_allow_html=True)
        
        with col3:
            progress = (st.session_state.slide_index + 1) / len(slides_html)
            st.progress(progress)
        
        with col4:
            if st.button("NEXT ▶▶", use_container_width=True):
                if st.session_state.slide_index < len(slides_html) - 1:
                    st.session_state.slide_index += 1
                    st.rerun()
        
        with col5:
            # Working fullscreen button with JavaScript
            fullscreen_html = f"""
                <button onclick="
                    var elem = document.getElementById('{container_id}');
                    if (elem.requestFullscreen) {{
                        elem.requestFullscreen();
                    }} else if (elem.webkitRequestFullscreen) {{
                        elem.webkitRequestFullscreen();
                    }} else if (elem.msRequestFullscreen) {{
                        elem.msRequestFullscreen();
                    }}
                " style="
                    background: linear-gradient(45deg, #ff69b4, #ff1493);
                    color: white;
                    border: none;
                    border-radius: 25px;
                    padding: 10px 20px;
                    font-weight: bold;
                    cursor: pointer;
                    width: 100%;
                    font-size: 16px;
                ">
                    🖥️ FULLSCREEN
                </button>
            """
            st.markdown(fullscreen_html, unsafe_allow_html=True)
        
        # Display current slide in container
        st.markdown("---")
        st.markdown(f'<div id="{container_id}">', unsafe_allow_html=True)
        st.markdown(slides_html[st.session_state.slide_index], unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Navigation hint
        st.info("💡 **Tip:** Use the buttons above to navigate slides, or click FULLSCREEN for better viewing")
        
        # Keyboard navigation using JavaScript
        keyboard_js = f"""
        <script>
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'ArrowLeft') {{
                    var prevButton = document.querySelector('button[kind="secondary"]:contains("◀◀ PREVIOUS")');
                    if (prevButton) prevButton.click();
                }} else if (e.key === 'ArrowRight') {{
                    var nextButton = document.querySelector('button[kind="secondary"]:contains("NEXT ▶▶")');
                    if (nextButton) nextButton.click();
                }}
            }});
        </script>
        """
        st.markdown(keyboard_js, unsafe_allow_html=True)
        
        # Download option
        with st.expander("📥 Download Original PowerPoint", expanded=False):
            with open(course["path"], "rb") as f:
                st.download_button(
                    label="Download PPT File",
                    data=f,
                    file_name=course["filename"],
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )
    
    else:
        st.error("❌ Cannot display this PowerPoint. Please make sure the file is valid and has content.")
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
                                key=f"down_btn_{key}"
                            )
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{key}"):
                        course_folder = Path(course["path"]).parent
                        images_folder = course_folder / "images"
                        if delete_course(key, course["path"], images_folder):
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
                
                if st.button(f"💡 Get a tip", key=f"tip_{key}"):
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
