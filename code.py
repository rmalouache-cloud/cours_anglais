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
    
    @keyframes fadeInUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
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

def extract_image_from_slide(slide):
    """Extract all images from slide"""
    images = []
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
                images.append(f'<img src="data:image/png;base64,{img_base64}" style="max-width: 100%; border-radius: 10px; margin: 10px 0; display: block;" />')
    except:
        pass
    return images

# Convert PPT to slides data
def convert_ppt_to_slides_data(ppt_path):
    """Extract all content from PPT"""
    try:
        from pptx import Presentation
        
        prs = Presentation(ppt_path)
        slides_data = []
        
        for idx, slide in enumerate(prs.slides):
            slide_content = {
                'number': idx + 1,
                'texts': [],
                'images': []
            }
            
            # Extract images
            slide_content['images'] = extract_image_from_slide(slide)
            
            # Extract text
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text = shape.text.strip()
                    # Check if it's a title
                    is_title = False
                    if hasattr(shape, "text_frame") and shape.text_frame.paragraphs:
                        first_para = shape.text_frame.paragraphs[0]
                        if first_para.font.size and first_para.font.size.pt >= 24:
                            is_title = True
                    slide_content['texts'].append({
                        'text': text,
                        'is_title': is_title
                    })
            
            slides_data.append(slide_content)
        
        return slides_data
    except Exception as e:
        st.error(f"Error converting PPT: {str(e)}")
        return None

# Create HTML viewer with working fullscreen and navigation
def create_html_viewer(slides_data, current_slide, total_slides, course_title):
    """Generate HTML with working fullscreen and navigation"""
    
    # Get current slide data
    slide = slides_data[current_slide]
    
    # Build HTML for current slide
    slide_html = f'<div style="font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto;">'
    
    # Add title
    slide_html += f'<h2 style="color: #c2185b; border-bottom: 2px solid #ff69b4; padding-bottom: 10px;">Slide {current_slide + 1} / {total_slides}</h2>'
    
    # Add content
    slide_html += '<div style="font-size: 18px; line-height: 1.6;">'
    
    # Add texts
    for text_item in slide['texts']:
        if text_item['is_title']:
            slide_html += f'<h3 style="color: #ff69b4; margin-top: 20px;">{text_item["text"]}</h3>'
        else:
            slide_html += f'<p style="margin: 10px 0;">{text_item["text"]}</p>'
    
    # Add images
    for img in slide['images']:
        slide_html += img
    
    if not slide['texts'] and not slide['images']:
        slide_html += '<p style="color: #999; text-align: center;">No content on this slide</p>'
    
    slide_html += '</div></div>'
    
    # Create full HTML page with working navigation
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 100%);
            }}
            
            .presentation-container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }}
            
            .slide-content {{
                margin: 20px 0;
                min-height: 400px;
            }}
            
            .nav-buttons {{
                display: flex;
                justify-content: space-between;
                gap: 10px;
                margin: 20px 0;
            }}
            
            button {{
                background: linear-gradient(45deg, #ff69b4, #ff1493);
                color: white;
                border: none;
                border-radius: 25px;
                padding: 12px 25px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 16px;
                flex: 1;
            }}
            
            button:hover:not(:disabled) {{
                transform: scale(1.05);
                box-shadow: 0 5px 15px rgba(255,20,147,0.3);
            }}
            
            button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            
            .fullscreen-btn {{
                background: linear-gradient(45deg, #2196F3, #1976D2);
                width: 100%;
                margin-top: 10px;
            }}
            
            .progress-bar {{
                width: 100%;
                height: 10px;
                background: #f0f0f0;
                border-radius: 5px;
                overflow: hidden;
                margin: 20px 0;
            }}
            
            .progress-fill {{
                width: {((current_slide + 1) / total_slides) * 100}%;
                height: 100%;
                background: linear-gradient(45deg, #ff69b4, #ff1493);
                transition: width 0.3s ease;
            }}
            
            .slide-info {{
                text-align: center;
                margin: 10px 0;
                color: #c2185b;
                font-weight: bold;
                font-size: 16px;
            }}
            
            /* Fullscreen styles */
            .presentation-container:fullscreen {{
                background: white;
                padding: 40px;
                overflow-y: auto;
                max-width: none;
                height: 100vh;
            }}
            
            .presentation-container:-webkit-full-screen {{
                background: white;
                padding: 40px;
                overflow-y: auto;
                max-width: none;
                height: 100vh;
            }}
            
            .presentation-container:-moz-full-screen {{
                background: white;
                padding: 40px;
                overflow-y: auto;
                max-width: none;
                height: 100vh;
            }}
            
            .slide-number {{
                text-align: center;
                margin-top: 20px;
                color: #999;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="presentation-container" id="presentationContainer">
            <h1 style="text-align: center; color: #c2185b;">📖 {course_title}</h1>
            
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
            
            <div class="slide-info">
                Slide {current_slide + 1} of {total_slides}
            </div>
            
            <div class="slide-content" id="slideContent">
                {slide_html}
            </div>
            
            <div class="nav-buttons">
                <button id="prevBtn" {"disabled" if current_slide == 0 else ""}>
                    ◀◀ PREVIOUS
                </button>
                <button id="nextBtn" {"disabled" if current_slide == total_slides - 1 else ""}>
                    NEXT ▶▶
                </button>
            </div>
            
            <button class="fullscreen-btn" id="fullscreenBtn">
                🖥️ TOGGLE FULLSCREEN
            </button>
            
            <div class="slide-number">
                💡 Tip: Use the buttons above to navigate
            </div>
        </div>
        
        <script>
            // Store current slide index
            let currentSlideIndex = {current_slide};
            const totalSlides = {total_slides};
            
            // Get all slide data from Python
            const slidesData = {json.dumps(slides_data)};
            
            // Function to update slide content
            function updateSlide(index) {{
                const slide = slidesData[index];
                const slideContent = document.getElementById('slideContent');
                const progressFill = document.querySelector('.progress-fill');
                const slideInfo = document.querySelector('.slide-info');
                const prevBtn = document.getElementById('prevBtn');
                const nextBtn = document.getElementById('nextBtn');
                
                // Update progress
                const progressPercent = ((index + 1) / totalSlides) * 100;
                progressFill.style.width = progressPercent + '%';
                
                // Update slide info
                slideInfo.innerHTML = `Slide ${{index + 1}} of ${{totalSlides}}`;
                
                // Build new slide HTML
                let slideHtml = `<div style="font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto;">`;
                slideHtml += `<h2 style="color: #c2185b; border-bottom: 2px solid #ff69b4; padding-bottom: 10px;">Slide ${{index + 1}} / ${{totalSlides}}</h2>`;
                slideHtml += `<div style="font-size: 18px; line-height: 1.6;">`;
                
                // Add texts
                for (const textItem of slide.texts) {{
                    if (textItem.is_title) {{
                        slideHtml += `<h3 style="color: #ff69b4; margin-top: 20px;">${{textItem.text}}</h3>`;
                    }} else {{
                        slideHtml += `<p style="margin: 10px 0;">${{textItem.text}}</p>`;
                    }}
                }}
                
                // Add images
                for (const img of slide.images) {{
                    slideHtml += img;
                }}
                
                if (slide.texts.length === 0 && slide.images.length === 0) {{
                    slideHtml += '<p style="color: #999; text-align: center;">No content on this slide</p>';
                }}
                
                slideHtml += `</div></div>`;
                
                // Update content
                slideContent.innerHTML = slideHtml;
                
                // Update button states
                prevBtn.disabled = (index === 0);
                nextBtn.disabled = (index === totalSlides - 1);
                
                // Update current index
                currentSlideIndex = index;
            }}
            
            // Previous button
            document.getElementById('prevBtn').addEventListener('click', function() {{
                if (currentSlideIndex > 0) {{
                    updateSlide(currentSlideIndex - 1);
                }}
            }});
            
            // Next button
            document.getElementById('nextBtn').addEventListener('click', function() {{
                if (currentSlideIndex < totalSlides - 1) {{
                    updateSlide(currentSlideIndex + 1);
                }}
            }});
            
            // Fullscreen button
            document.getElementById('fullscreenBtn').addEventListener('click', function() {{
                var elem = document.getElementById('presentationContainer');
                if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.mozFullScreenElement) {{
                    if (elem.requestFullscreen) {{
                        elem.requestFullscreen();
                    }} else if (elem.webkitRequestFullscreen) {{
                        elem.webkitRequestFullscreen();
                    }} else if (elem.msRequestFullscreen) {{
                        elem.msRequestFullscreen();
                    }} else if (elem.mozRequestFullScreen) {{
                        elem.mozRequestFullScreen();
                    }}
                }} else {{
                    if (document.exitFullscreen) {{
                        document.exitFullscreen();
                    }} else if (document.webkitExitFullscreen) {{
                        document.webkitExitFullscreen();
                    }} else if (document.msExitFullscreen) {{
                        document.msExitFullscreen();
                    }} else if (document.mozCancelFullScreen) {{
                        document.mozCancelFullScreen();
                    }}
                }}
            }});
            
            // Keyboard navigation
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'ArrowLeft') {{
                    if (currentSlideIndex > 0) {{
                        updateSlide(currentSlideIndex - 1);
                    }}
                }} else if (e.key === 'ArrowRight') {{
                    if (currentSlideIndex < totalSlides - 1) {{
                        updateSlide(currentSlideIndex + 1);
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return html_code

# Display presentation with custom component
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # Back button
    if st.button("◀ Back to Courses", use_container_width=False):
        st.session_state['viewing_course'] = None
        st.rerun()
    
    # Convert PPT to slides data
    if 'slides_data' not in st.session_state or st.session_state.get('current_course_path') != course["path"]:
        slides_data = convert_ppt_to_slides_data(course["path"])
        if slides_data:
            st.session_state.slides_data = slides_data
            st.session_state.current_course_path = course["path"]
        else:
            st.error("❌ Cannot display this PowerPoint. Please make sure the file is valid.")
            return
    
    slides_data = st.session_state.slides_data
    total_slides = len(slides_data)
    
    # Create and display HTML viewer with all functionality built-in
    html_viewer = create_html_viewer(
        slides_data, 
        0,  # Start from first slide
        total_slides,
        course['title']
    )
    
    # Display the HTML component
    st.components.v1.html(html_viewer, height=700, scrolling=True)
    
    # Download option
    with st.expander("📥 Download Original PowerPoint", expanded=False):
        with open(course["path"], "rb") as f:
            st.download_button(
                label="Download PPT File",
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
                        # Reset slide data when viewing new course
                        if 'slides_data' in st.session_state:
                            del st.session_state.slides_data
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
                        # Reset slide data when viewing new course
                        if 'slides_data' in st.session_state:
                            del st.session_state.slides_data
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
