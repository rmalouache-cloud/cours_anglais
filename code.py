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

# Custom CSS with animations
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
        transition: all 0.3s ease;
    }
    
    .course-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(255,20,147,0.15);
    }
    
    @keyframes fadeInUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    @keyframes float {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-15px) rotate(5deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0) scale(1); }
        50% { transform: translateY(-10px) scale(1.1); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
    }
    
    @keyframes shimmer {
        0% { background-position: -200% center; }
        100% { background-position: 200% center; }
    }
    
    .floating-logo {
        animation: float 3s ease-in-out infinite;
        display: inline-block;
    }
    
    .spinning-icon {
        animation: spin 4s linear infinite;
        display: inline-block;
    }
    
    .bouncing-icon {
        animation: bounce 2s ease-in-out infinite;
        display: inline-block;
    }
    
    .pulsing-icon {
        animation: pulse 2s ease-in-out infinite;
        display: inline-block;
    }
    
    .rainbow-text {
        background: linear-gradient(45deg, #ff69b4, #ff1493, #ff69b4, #ff1493);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite;
        display: inline-block;
    }
    
    .hover-lift {
        transition: all 0.3s ease;
    }
    
    .hover-lift:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 10px 30px rgba(255,20,147,0.2);
    }
    
    /* Welcome section animation */
    .welcome-section {
        animation: fadeInUp 1s ease-out;
        text-align: center;
        padding: 40px 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize folders with sample data
def init_folders():
    levels = ["A", "B", "C"]
    sub_levels = ["1", "2", "3"]
    for level in levels:
        for sub in sub_levels:
            Path(f"courses/Level_{level}/{level}{sub}").mkdir(parents=True, exist_ok=True)
            Path(f"courses/Level_{level}/{level}{sub}/images").mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    Path("courses/pdf_pages").mkdir(parents=True, exist_ok=True)
    
    # Create sample metadata if it doesn't exist
    metadata_path = Path("data/courses_metadata.json")
    if not metadata_path.exists():
        sample_metadata = {
            "A1_sample_course": {
                "title": "Introduction to English - Sample",
                "description": "A beginner-friendly introduction to English language basics. Perfect for starting your English journey!",
                "level": "A1",
                "path": "",
                "filename": "sample.pdf",
                "upload_date": time.strftime("%Y-%m-%d %H:%M"),
                "type": "pdf",
                "is_sample": True
            },
            "A2_sample_course": {
                "title": "Everyday Conversations - Sample",
                "description": "Learn practical English for daily conversations, greetings, and common phrases.",
                "level": "A2",
                "path": "",
                "filename": "sample.pdf",
                "upload_date": time.strftime("%Y-%m-%d %H:%M"),
                "type": "pdf",
                "is_sample": True
            },
            "B1_sample_course": {
                "title": "Grammar Mastery - Sample",
                "description": "Master English grammar with clear explanations and practical examples.",
                "level": "B1",
                "path": "",
                "filename": "sample.pdf",
                "upload_date": time.strftime("%Y-%m-%d %H:%M"),
                "type": "pdf",
                "is_sample": True
            }
        }
        with open(metadata_path, "w") as f:
            json.dump(sample_metadata, f, indent=4)

# Load metadata
def load_metadata():
    metadata_path = Path("data/courses_metadata.json")
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
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

# Create HTML viewer
def create_html_viewer(images_base64, current_page, total_pages, course_title):
    """Generate complete HTML with fullscreen button at top and navigation below"""
    
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
                animation: fadeInUp 0.6s ease-out;
            }}
            
            @keyframes fadeInUp {{
                from {{ transform: translateY(20px); opacity: 0; }}
                to {{ transform: translateY(0); opacity: 1; }}
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
            
            .fullscreen-top {{
                display: flex;
                justify-content: flex-end;
                margin-bottom: 15px;
            }}
            
            .btn-fullscreen {{
                background: linear-gradient(45deg, #2196F3, #1976D2);
                color: white;
                border: none;
                border-radius: 25px;
                padding: 12px 30px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 16px;
                box-shadow: 0 4px 15px rgba(33,150,243,0.3);
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .btn-fullscreen:hover {{
                transform: scale(1.05);
                box-shadow: 0 6px 25px rgba(33,150,243,0.4);
                background: linear-gradient(45deg, #1976D2, #0D47A1);
            }}
            
            .btn-fullscreen:active {{
                transform: scale(0.98);
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
                transition: all 0.3s ease;
            }}
            
            .page-image:hover {{
                transform: scale(1.01);
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
                .btn-fullscreen {{
                    font-size: 14px;
                    padding: 10px 20px;
                }}
                .image-wrapper {{
                    min-height: 250px;
                }}
                .fullscreen-top {{
                    justify-content: center;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="presentation-container" id="presentationContainer">
            <div class="fullscreen-top">
                <button class="btn-fullscreen" id="fullscreenBtn">
                    🖥️ PLEIN ÉCRAN
                </button>
            </div>
            
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
            
            document.getElementById('fullscreenBtn').addEventListener('click', function() {{
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
            }});
            
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
    
    if st.button("◀ Back to Courses", use_container_width=False):
        st.session_state['viewing_course'] = None
        if 'pdf_images' in st.session_state:
            del st.session_state.pdf_images
        st.rerun()
    
    st.markdown(f"""
        <div style="text-align: center;">
            <h2>
                <span class="floating-logo">📖</span> 
                {course['title']} 
                <span class="floating-logo" style="animation-delay: 0.5s;">✨</span>
            </h2>
            <p style="color: #c2185b;">
                <span class="bouncing-icon">🎯</span> 
                Level {course['level']} 
                <span class="pulsing-icon">📅</span> 
                {course['upload_date']}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    course_key = f"{course['level']}_{course['filename']}".replace('.pdf', '')
    
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
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown(f"""
            <h3 style="text-align: center; color: #c2185b;">
                <span class="floating-logo">📄</span> 
                Page {st.session_state.current_page + 1} / {total_pages}
                <span class="floating-logo" style="animation-delay: 0.5s;">📄</span>
            </h3>
        """, unsafe_allow_html=True)
        progress = (st.session_state.current_page + 1) / total_pages
        st.progress(progress)
    
    st.markdown("---")
    
    html_viewer = create_html_viewer(
        images_base64,
        st.session_state.current_page,
        total_pages,
        course['title']
    )
    
    st.components.v1.html(html_viewer, height=780, scrolling=True)
    
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
    
    # Animated title
    st.markdown("""
        <div style="text-align: center; animation: fadeInUp 0.8s ease-out;">
            <h1>
                <span class="floating-logo">🌸</span> 
                <span class="rainbow-text">English Teacher's Platform</span> 
                <span class="floating-logo" style="animation-delay: 0.5s;">🌸</span>
            </h1>
            <p style="color: #c2185b; font-size: 18px;">
                <span class="bouncing-icon">✨</span> 
                Make learning beautiful and fun! 
                <span class="bouncing-icon" style="animation-delay: 0.3s;">✨</span>
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Animated icons
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px; font-size: 30px;">
            <span class="floating-logo">📖</span> 
            <span class="floating-logo" style="animation-delay: 0.2s;">📝</span> 
            <span class="floating-logo" style="animation-delay: 0.4s;">🎓</span> 
            <span class="floating-logo" style="animation-delay: 0.6s;">✏️</span> 
            <span class="floating-logo" style="animation-delay: 0.8s;">📕</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 20px 0;">
                <h3 style="color: #ff69b4;">
                    <span class="bouncing-icon">✨</span> 
                    Welcome! 
                    <span class="bouncing-icon" style="animation-delay: 0.3s;">✨</span>
                </h3>
                <div style="font-size: 30px;">
                    <span class="floating-logo">👩‍🏫</span>
                </div>
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
    
    # Welcome message
    if not metadata or all(c.get('is_sample', False) for c in metadata.values()):
        st.markdown("""
            <div class="welcome-section">
                <h2>
                    <span class="floating-logo">🎉</span> 
                    Welcome to Your English Platform! 
                    <span class="floating-logo" style="animation-delay: 0.5s;">🎉</span>
                </h2>
                <p style="font-size: 18px; color: #c2185b;">
                    Start by uploading your first course below! 
                    <span class="bouncing-icon">⬇️</span>
                </p>
                <div style="font-size: 50px; margin: 20px 0;">
                    <span class="floating-logo">📚</span>
                    <span class="floating-logo" style="animation-delay: 0.3s;">✨</span>
                    <span class="floating-logo" style="animation-delay: 0.6s;">🌟</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
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
        real_courses = [c for c in metadata.values() if not c.get('is_sample', False)]
        total_courses = len(real_courses)
        st.info(f"📚 **Total courses:** {total_courses}")
        
        if real_courses:
            levels_count = {}
            for course in real_courses:
                level = course["level"]
                levels_count[level] = levels_count.get(level, 0) + 1
            
            st.write("**Courses per level:**")
            for level, count in sorted(levels_count.items()):
                st.progress(min(count/10, 1.0), text=f"Level {level}: {count} courses")
    
    st.markdown("---")
    st.subheader("📚 Manage Your Courses")
    
    # Filter out sample courses from display
    real_courses = {k: v for k, v in metadata.items() if not v.get('is_sample', False)}
    
    if real_courses:
        filter_level = st.selectbox("Filter by level:", ["All"] + sorted(set(c["level"] for c in real_courses.values())))
        
        for key, course in real_courses.items():
            if filter_level != "All" and course["level"] != filter_level:
                continue
                
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    file_type = "📄" if course.get("type", "pdf") == "pdf" else "📄"
                    st.markdown(f"""
                        <div class="course-card hover-lift">
                            <strong><span class="floating-logo">{file_type}</span> {course['title']}</strong><br>
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
        st.info("""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 40px;">
                    <span class="floating-logo">🌸</span>
                    <span class="floating-logo" style="animation-delay: 0.3s;">📚</span>
                    <span class="floating-logo" style="animation-delay: 0.6s;">✨</span>
                </div>
                <p style="font-size: 18px; color: #c2185b;">
                    No courses yet. Upload your first course above! 
                    <span class="bouncing-icon">⬆️</span>
                </p>
            </div>
        """, unsafe_allow_html=True)
    
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
    
    # Show real courses only
    real_courses = {k: v for k, v in metadata.items() if not v.get('is_sample', False)}
    available_courses = {k: v for k, v in real_courses.items() if v["level"] == full_level}
    
    if available_courses:
        st.success(f"✨ Found {len(available_courses)} course(s) for Level {full_level} ✨")
        
        for key, course in available_courses.items():
            with st.expander(f"📖 {course['title']}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                        <div style="background: #fff0f5; padding: 15px; border-radius: 15px; transition: all 0.3s ease;">
                            <strong>💭 Description:</strong><br>
                            {course['description']}<br><br>
                            <strong>📅 Uploaded
