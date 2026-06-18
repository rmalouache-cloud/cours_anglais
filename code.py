import streamlit as st
import json
import os
from pathlib import Path
import time
from PIL import Image
import io
import base64
import shutil
import fitz  # PyMuPDF

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
    Path("courses/pdf_pages").mkdir(parents=True, exist_ok=True)

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
def delete_course(course_key, course_path, images_folder, pdf_pages_folder=None):
    try:
        if os.path.exists(course_path):
            os.remove(course_path)
        if os.path.exists(images_folder):
            shutil.rmtree(images_folder)
        if pdf_pages_folder and os.path.exists(pdf_pages_folder):
            shutil.rmtree(pdf_pages_folder)
        metadata = load_metadata()
        if course_key in metadata:
            del metadata[course_key]
            save_metadata(metadata)
        return True
    except:
        return False

# Convert PDF to images using PyMuPDF
def convert_pdf_to_images(pdf_path, output_folder):
    """Convert PDF pages to images using PyMuPDF"""
    try:
        pdf_document = fitz.open(pdf_path)
        
        image_paths = []
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            if img.width > 1200:
                ratio = 1200 / img.width
                new_size = (1200, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            image_path = os.path.join(output_folder, f"page_{page_num + 1}.png")
            img.save(image_path, "PNG", optimize=True)
            image_paths.append(image_path)
        
        pdf_document.close()
        return image_paths
        
    except Exception as e:
        st.error(f"Erreur lors de la conversion du PDF : {str(e)}")
        return None

# Convert PDF to base64 images
def convert_pdf_to_base64_images(pdf_path, course_key):
    """Convert PDF to base64 images for HTML display"""
    try:
        pdf_pages_folder = Path(f"courses/pdf_pages/{course_key}")
        pdf_pages_folder.mkdir(parents=True, exist_ok=True)
        
        # Check if images already exist
        existing_images = list(pdf_pages_folder.glob("page_*.png"))
        if existing_images:
            image_paths = sorted([str(img) for img in existing_images])
        else:
            image_paths = convert_pdf_to_images(pdf_path, str(pdf_pages_folder))
            if not image_paths:
                return None
        
        # Convert images to base64
        images_base64 = []
        for img_path in image_paths:
            with open(img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
                images_base64.append(img_data)
        
        return images_base64
        
    except Exception as e:
        st.error(f"Erreur lors du traitement du PDF : {str(e)}")
        return None

# Create HTML viewer avec navigation en dessous
def create_html_viewer(images_base64, current_page, total_pages, course_title):
    """Generate HTML with navigation below"""
    
    # Get current image
    current_img = images_base64[current_page]
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 100%);
                padding: 20px;
            }}
            
            .presentation-container {{
                max-width: 1100px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }}
            
            .presentation-container:fullscreen {{
                max-width: 100%;
                width: 100vw;
                height: 100vh;
                border-radius: 0;
                padding: 20px;
                overflow-y: auto;
                background: white;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            
            .presentation-container:-webkit-full-screen {{
                max-width: 100%;
                width: 100vw;
                height: 100vh;
                border-radius: 0;
                padding: 20px;
                overflow-y: auto;
                background: white;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            
            .presentation-container:-moz-full-screen {{
                max-width: 100%;
                width: 100vw;
                height: 100vh;
                border-radius: 0;
                padding: 20px;
                overflow-y: auto;
                background: white;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                flex-wrap: wrap;
                gap: 10px;
            }}
            
            h1 {{
                color: #c2185b;
                font-size: 22px;
                margin: 0;
            }}
            
            .page-info {{
                color: #c2185b;
                font-weight: bold;
                font-size: 15px;
                background: #ffe6f0;
                padding: 6px 16px;
                border-radius: 20px;
            }}
            
            .progress-bar {{
                width: 100%;
                height: 6px;
                background: #f0f0f0;
                border-radius: 3px;
                overflow: hidden;
                margin: 10px 0 20px 0;
            }}
            
            .progress-fill {{
                width: {((current_page + 1) / total_pages) * 100}%;
                height: 100%;
                background: linear-gradient(45deg, #ff69b4, #ff1493);
                transition: width 0.3s ease;
            }}
            
            .image-wrapper {{
                width: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 400px;
                background: #fafafa;
                border-radius: 12px;
                padding: 10px;
                margin-bottom: 20px;
            }}
            
            .page-image {{
                max-width: 100%;
                max-height: 70vh;
                object-fit: contain;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                user-select: none;
            }}
            
            .nav-buttons {{
                display: flex;
                justify-content: center;
                gap: 15px;
                margin: 15px 0 0 0;
                flex-wrap: wrap;
            }}
            
            .btn-nav {{
                background: linear-gradient(45deg, #ff69b4, #ff1493);
                color: white;
                border: none;
                border-radius: 25px;
                padding: 12px 30px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 16px;
                min-width: 140px;
            }}
            
            .btn-nav:hover:not(:disabled) {{
                transform: scale(1.05);
                box-shadow: 0 5px 15px rgba(255,20,147,0.3);
            }}
            
            .btn-nav:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }}
            
            @media (max-width: 768px) {{
                body {{
                    padding: 10px;
                }}
                .presentation-container {{
                    padding: 15px;
                }}
                h1 {{
                    font-size: 18px;
                }}
                .btn-nav {{
                    padding: 10px 20px;
                    font-size: 14px;
                    min-width: 100px;
                }}
                .image-wrapper {{
                    min-height: 250px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="presentation-container" id="presentationContainer">
            <div class="header">
                <h1>📖 {course_title}</h1>
                <div class="page-info" id="pageInfo">
                    Page {current_page + 1} / {total_pages}
                </div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            
            <div class="image-wrapper">
                <img id="pageImage" class="page-image" src="data:image/png;base64,{current_img}" alt="Page {current_page + 1}" />
            </div>
            
            <div class="nav-buttons">
                <button class="btn-nav" id="prevBtn" {"disabled" if current_page == 0 else ""}>
                    ◀◀ PRÉCÉDENT
                </button>
                <button class="btn-nav" id="nextBtn" {"disabled" if current_page == total_pages - 1 else ""}>
                    SUIVANT ▶▶
                </button>
            </div>
        </div>
        
        <script>
            const imagesBase64 = {json.dumps(images_base64)};
            let currentPage = {current_page};
            const totalPages = {total_pages};
            
            const pageImage = document.getElementById('pageImage');
            const pageInfo = document.getElementById('pageInfo');
            const progressFill = document.getElementById('progressFill');
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            const container = document.getElementById('presentationContainer');
            
            function updatePage(index) {{
                if (index < 0 || index >= totalPages) return;
                
                currentPage = index;
                pageImage.src = 'data:image/png;base64,' + imagesBase64[index];
                pageInfo.textContent = 'Page ' + (index + 1) + ' / ' + totalPages;
                
                const progressPercent = ((index + 1) / totalPages) * 100;
                progressFill.style.width = progressPercent + '%';
                
                prevBtn.disabled = (index === 0);
                nextBtn.disabled = (index === totalPages - 1);
            }}
            
            prevBtn.addEventListener('click', function() {{
                if (currentPage > 0) updatePage(currentPage - 1);
            }});
            
            nextBtn.addEventListener('click', function() {{
                if (currentPage < totalPages - 1) updatePage(currentPage + 1);
            }});
            
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'ArrowLeft' && currentPage > 0) {{
                    updatePage(currentPage - 1);
                    e.preventDefault();
                }} else if (e.key === 'ArrowRight' && currentPage < totalPages - 1) {{
                    updatePage(currentPage + 1);
                    e.preventDefault();
                }}
            }});
            
            // Fonction pour le fullscreen
            window.toggleFullscreen = function() {{
                if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.mozFullScreenElement) {{
                    if (container.requestFullscreen) {{
                        container.requestFullscreen();
                    }} else if (container.webkitRequestFullscreen) {{
                        container.webkitRequestFullscreen();
                    }} else if (container.msRequestFullscreen) {{
                        container.msRequestFullscreen();
                    }} else if (container.mozRequestFullScreen) {{
                        container.mozRequestFullScreen();
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
            }};
            
            document.addEventListener('fullscreenchange', function() {{
                if (document.fullscreenElement) {{
                    document.querySelector('.presentation-container').style.maxWidth = '100%';
                }} else {{
                    document.querySelector('.presentation-container').style.maxWidth = '1100px';
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return html_code

# Display PDF presentation
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # Back button
    if st.button("◀ Back to Courses", use_container_width=False):
        st.session_state['viewing_course'] = None
        if 'pdf_images' in st.session_state:
            del st.session_state.pdf_images
        st.rerun()
    
    # Title
    st.markdown(f"""
        <div style="text-align: center;">
            <h2>📖 {course['title']}</h2>
            <p style="color: #c2185b;">Level {course['level']} | {course['upload_date']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Generate unique key for this course
    course_key = f"{course['level']}_{course['filename']}".replace('.pdf', '')
    
    # Check if we have PDF images cached
    if 'pdf_images' not in st.session_state or st.session_state.get('current_pdf_key') != course_key:
        with st.spinner("🔄 Conversion du PDF en cours..."):
            images_base64 = convert_pdf_to_base64_images(course["path"], course_key)
            if images_base64:
                st.session_state.pdf_images = images_base64
                st.session_state.current_pdf_key = course_key
                st.session_state.current_page = 0
            else:
                st.error("❌ Impossible d'afficher ce PDF. Veuillez vérifier que le fichier est valide.")
                with open(course["path"], "rb") as f:
                    st.download_button(
                        label="📥 Télécharger le PDF",
                        data=f,
                        file_name=course["filename"],
                        mime="application/pdf"
                    )
                return
    
    images_base64 = st.session_state.pdf_images
    total_pages = len(images_base64)
    
    # Initialize page index
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    
    # Affichage du numéro de page et progression
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        st.write("")
    
    with col2:
        st.markdown(f"<h3 style='text-align: center; color: #c2185b;'>Page {st.session_state.current_page + 1} / {total_pages}</h3>", unsafe_allow_html=True)
        progress = (st.session_state.current_page + 1) / total_pages
        st.progress(progress)
    
    with col3:
        st.write("")
    
    st.markdown("---")
    
    # BOUTON FULLSCREEN avec st.components.v1.html() (fonctionne !)
    fullscreen_button_html = """
    <div style="display: flex; justify-content: center; margin: 10px 0;">
        <button onclick="
            var iframes = document.querySelectorAll('iframe');
            for (var i = 0; i < iframes.length; i++) {
                try {
                    if (iframes[i].contentWindow && iframes[i].contentWindow.toggleFullscreen) {
                        iframes[i].contentWindow.toggleFullscreen();
                        break;
                    }
                } catch(e) {}
            }
        " style="
            background: linear-gradient(45deg, #2196F3, #1976D2);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 14px 40px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 18px;
            box-shadow: 0 4px 15px rgba(33,150,243,0.3);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            width: 100%;
            max-width: 400px;
        "
        onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 6px 25px rgba(33,150,243,0.4)';"
        onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 4px 15px rgba(33,150,243,0.3)';"
        >
            🖥️ PLEIN ÉCRAN
        </button>
    </div>
    """
    st.components.v1.html(fullscreen_button_html, height=80)
    
    st.markdown("---")
    
    # Create HTML viewer avec navigation en dessous
    html_viewer = create_html_viewer(
        images_base64,
        st.session_state.current_page,
        total_pages,
        course['title']
    )
    
    # Display the HTML component
    st.components.v1.html(html_viewer, height=750, scrolling=True)
    
    # Download option
    with st.expander("📥 Télécharger le PDF original", expanded=False):
        with open(course["path"], "rb") as f:
            st.download_button(
                label="Télécharger le fichier PDF",
                data=f,
                file_name=course["filename"],
                mime="application/pdf"
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
            "📎 Upload PDF File", 
            type=["pdf"],
            help="Upload your PDF document"
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
                    "upload_date": time.strftime("%Y-%m-%d %H:%M"),
                    "type": "pdf"
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
                    file_type = "📄" if course.get("type", "pdf") == "pdf" else "📄"
                    st.markdown(f"""
                        <div class="course-card">
                            <strong>{file_type} {course['title']}</strong><br>
                            <small>🎯 Level {course['level']}</small><br>
                            <small>📅 {course['upload_date']}</small><br>
                            <small>💭 {course['description']}</small>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🎬 View & Present", key=f"view_{key}"):
                        if 'pdf_images' in st.session_state:
                            del st.session_state.pdf_images
                        if 'current_pdf_key' in st.session_state:
                            del st.session_state.current_pdf_key
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
                        course_folder = Path(course["path"]).parent
                        images_folder = course_folder / "images"
                        pdf_pages_folder = Path(f"courses/pdf_pages/{key.replace('.pdf', '')}")
                        if delete_course(key, course["path"], images_folder, pdf_pages_folder):
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
                            <strong>🎯 Level:</strong> {course['level']}<br>
                            <strong>📄 Type:</strong> PDF Document
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🎬 View Course", key=f"view_student_{key}"):
                        if 'pdf_images' in st.session_state:
                            del st.session_state.pdf_images
                        if 'current_pdf_key' in st.session_state:
                            del st.session_state.current_pdf_key
                        st.session_state.viewing_course = course
                        st.rerun()
                
                with col2:
                    with open(course["path"], "rb") as f:
                        st.download_button(
                            label="📥 Download Course",
                            data=f,
                            file_name=course["filename"],
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"student_download_{key}"
                        )
                
                if st.button(f"💡 Get a tip", key=f"tip_{key}"):
                    tips = [
                        "✨ Take notes while reading!",
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
