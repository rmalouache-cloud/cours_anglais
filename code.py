import streamlit as st
import json
import os
from pathlib import Path
import time
from PIL import Image
import io
import base64
import fitz  # PyMuPDF
from supabase import create_client, Client

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="✨ English Teacher's Platform ✨",
    page_icon="🌸",
    layout="wide"
)

# ==============================
# CUSTOM CSS  (identique à ton original)
# ==============================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 100%);
    }
    h1, h2, h3 { color: #c2185b !important; }
    .stButton > button {
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 12px 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover { transform: scale(1.05); }
    .course-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border: 1px solid #ffc0cb;
    }
    .course-card:hover { transform: translateY(-5px); }
    @keyframes fadeInUp {
        from { transform: translateY(20px); opacity: 0; }
        to   { transform: translateY(0);    opacity: 1; }
    }
    .fade-in { animation: fadeInUp 0.6s ease-out; }
</style>
""", unsafe_allow_html=True)

# ==============================
# SUPABASE  (stockage permanent)
# ==============================
BUCKET = "courses"

@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

# ── Metadata (table Supabase) ──────────────────────────────────────────────
def load_metadata() -> dict:
    try:
        rows = get_supabase().table("courses").select("*").execute().data
        return {r["id"]: r for r in rows}
    except Exception as e:
        st.error(f"❌ Cannot load courses: {e}")
        return {}

def save_course(course_id: str, data: dict):
    get_supabase().table("courses").upsert({"id": course_id, **data}).execute()

def remove_course(course_id: str):
    get_supabase().table("courses").delete().eq("id", course_id).execute()

# ── File storage (bucket Supabase) ────────────────────────────────────────
def upload_pdf(file_bytes: bytes, storage_path: str):
    get_supabase().storage.from_(BUCKET).upload(
        storage_path, file_bytes,
        {"content-type": "application/pdf", "upsert": "true"}
    )

def download_pdf(storage_path: str) -> bytes:
    return get_supabase().storage.from_(BUCKET).download(storage_path)

def delete_pdf(storage_path: str):
    get_supabase().storage.from_(BUCKET).remove([storage_path])

# ==============================
# PDF → BASE64 IMAGES  (PyMuPDF, en mémoire)
# ==============================
def pdf_bytes_to_base64_images(pdf_bytes: bytes) -> list:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images_b64 = []
    for page in doc:
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        if img.width > 1200:
            ratio = 1200 / img.width
            img = img.resize((1200, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        images_b64.append(base64.b64encode(buf.getvalue()).decode())
    doc.close()
    return images_b64

# ==============================
# HTML VIEWER  (identique à ton original — fullscreen inclus)
# ==============================
def create_html_viewer(images_base64, current_page, total_pages, course_title):
    current_img = images_base64[current_page]
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
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
            .presentation-container:fullscreen,
            .presentation-container:-webkit-full-screen,
            .presentation-container:-moz-full-screen {{
                max-width:100%; width:100vw; height:100vh;
                border-radius:0; padding:20px; overflow-y:auto;
                background:white; display:flex; flex-direction:column;
                justify-content:center;
            }}
            .fullscreen-top {{
                display:flex; justify-content:flex-end; margin-bottom:15px;
            }}
            .btn-fullscreen {{
                background: linear-gradient(45deg, #2196F3, #1976D2);
                color:white; border:none; border-radius:25px;
                padding:12px 30px; font-weight:bold; cursor:pointer;
                transition:all 0.3s ease; font-size:16px;
                box-shadow:0 4px 15px rgba(33,150,243,0.3);
                display:flex; align-items:center; gap:10px;
            }}
            .btn-fullscreen:hover {{
                transform:scale(1.05);
                box-shadow:0 6px 25px rgba(33,150,243,0.4);
                background:linear-gradient(45deg,#1976D2,#0D47A1);
            }}
            .header {{
                display:flex; justify-content:space-between;
                align-items:center; margin-bottom:15px;
                flex-wrap:wrap; gap:10px;
            }}
            h1 {{ color:#c2185b; font-size:22px; margin:0; }}
            .page-info {{
                color:#c2185b; font-weight:bold; font-size:15px;
                background:#ffe6f0; padding:6px 16px; border-radius:20px;
            }}
            .progress-bar {{
                width:100%; height:6px; background:#f0f0f0;
                border-radius:3px; overflow:hidden; margin:10px 0 20px 0;
            }}
            .progress-fill {{
                width:{((current_page + 1) / total_pages) * 100}%;
                height:100%;
                background:linear-gradient(45deg, #ff69b4, #ff1493);
                transition:width 0.3s ease;
            }}
            .image-wrapper {{
                width:100%; display:flex; justify-content:center;
                align-items:center; min-height:400px;
                background:#fafafa; border-radius:12px;
                padding:10px; margin-bottom:20px;
            }}
            .page-image {{
                max-width:100%; max-height:70vh;
                object-fit:contain; border-radius:8px;
                box-shadow:0 4px 15px rgba(0,0,0,0.08);
                user-select:none;
            }}
            .nav-buttons {{
                display:flex; justify-content:center;
                gap:15px; margin:15px 0 0 0; flex-wrap:wrap;
            }}
            .btn-nav {{
                background:linear-gradient(45deg, #ff69b4, #ff1493);
                color:white; border:none; border-radius:25px;
                padding:12px 30px; font-weight:bold; cursor:pointer;
                transition:all 0.3s ease; font-size:16px; min-width:140px;
            }}
            .btn-nav:hover:not(:disabled) {{
                transform:scale(1.05);
                box-shadow:0 5px 15px rgba(255,20,147,0.3);
            }}
            .btn-nav:disabled {{ opacity:0.5; cursor:not-allowed; transform:none; }}
            @media (max-width:768px) {{
                body {{ padding:10px; }}
                .presentation-container {{ padding:15px; }}
                h1 {{ font-size:18px; }}
                .btn-nav {{ padding:10px 20px; font-size:14px; min-width:100px; }}
                .btn-fullscreen {{ font-size:14px; padding:10px 20px; }}
                .image-wrapper {{ min-height:250px; }}
                .fullscreen-top {{ justify-content:center; }}
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
                <img id="pageImage" class="page-image"
                     src="data:image/png;base64,{current_img}"
                     alt="Page {current_page + 1}" />
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
            let currentPage   = {current_page};
            const totalPages  = {total_pages};
            const pageImage   = document.getElementById('pageImage');
            const pageInfo    = document.getElementById('pageInfo');
            const progressFill= document.getElementById('progressFill');
            const prevBtn     = document.getElementById('prevBtn');
            const nextBtn     = document.getElementById('nextBtn');
            const container   = document.getElementById('presentationContainer');

            function updatePage(index) {{
                if (index < 0 || index >= totalPages) return;
                currentPage = index;
                pageImage.src = 'data:image/png;base64,' + imagesBase64[index];
                pageInfo.textContent = 'Page ' + (index+1) + ' / ' + totalPages;
                progressFill.style.width = ((index+1)/totalPages*100) + '%';
                prevBtn.disabled = (index === 0);
                nextBtn.disabled = (index === totalPages-1);
            }}

            prevBtn.addEventListener('click', function() {{
                if (currentPage > 0) updatePage(currentPage - 1);
            }});
            nextBtn.addEventListener('click', function() {{
                if (currentPage < totalPages-1) updatePage(currentPage + 1);
            }});
            document.addEventListener('keydown', function(e) {{
                if (e.key==='ArrowLeft'  && currentPage>0)           {{ updatePage(currentPage-1); e.preventDefault(); }}
                if (e.key==='ArrowRight' && currentPage<totalPages-1) {{ updatePage(currentPage+1); e.preventDefault(); }}
            }});

            document.getElementById('fullscreenBtn').addEventListener('click', function() {{
                if (!document.fullscreenElement && !document.webkitFullscreenElement &&
                    !document.mozFullScreenElement) {{
                    (container.requestFullscreen || container.webkitRequestFullscreen ||
                     container.msRequestFullscreen || container.mozRequestFullScreen).call(container);
                }} else {{
                    (document.exitFullscreen || document.webkitExitFullscreen ||
                     document.msExitFullscreen || document.mozCancelFullScreen).call(document);
                }}
            }});
            document.addEventListener('fullscreenchange', function() {{
                container.style.maxWidth = document.fullscreenElement ? '100%' : '1100px';
            }});
        </script>
    </body>
    </html>
    """
    return html_code

# ==============================
# DISPLAY PRESENTATION
# ==============================
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)

    if st.button("◀ Back to Courses"):
        st.session_state['viewing_course'] = None
        for k in ['pdf_images', 'current_pdf_key', 'current_page']:
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown(f"""
        <div style="text-align:center;">
            <h2>📖 {course['title']}</h2>
            <p style="color:#c2185b;">Level {course['level']} | {course['upload_date']}</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    course_key = course["id"]

    # Charge les images depuis Supabase (avec cache session)
    if 'pdf_images' not in st.session_state or \
       st.session_state.get('current_pdf_key') != course_key:
        with st.spinner("🔄 Chargement du cours…"):
            try:
                pdf_bytes = download_pdf(course["storage_path"])
                images_b64 = pdf_bytes_to_base64_images(pdf_bytes)
                st.session_state.pdf_images      = images_b64
                st.session_state.current_pdf_key = course_key
                st.session_state.current_page    = 0
            except Exception as e:
                st.error(f"❌ Impossible d'afficher ce PDF : {e}")
                pdf_bytes = download_pdf(course["storage_path"])
                st.download_button("📥 Télécharger le PDF", pdf_bytes,
                                   file_name=course["filename"],
                                   mime="application/pdf")
                return

    images_base64 = st.session_state.pdf_images
    total_pages   = len(images_base64)

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    # Compteur et barre de progression Streamlit (au-dessus du viewer)
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown(
            f"<h3 style='text-align:center;color:#c2185b;'>"
            f"Page {st.session_state.current_page + 1} / {total_pages}</h3>",
            unsafe_allow_html=True
        )
        st.progress((st.session_state.current_page + 1) / total_pages)
    st.markdown("---")

    # Viewer HTML complet (fullscreen + navigation interne)
    html_viewer = create_html_viewer(
        images_base64,
        st.session_state.current_page,
        total_pages,
        course['title']
    )
    st.components.v1.html(html_viewer, height=780, scrolling=True)

    # Download
    with st.expander("📥 Télécharger le PDF original", expanded=False):
        pdf_bytes = download_pdf(course["storage_path"])
        st.download_button(
            "Télécharger le fichier PDF",
            data=pdf_bytes,
            file_name=course["filename"],
            mime="application/pdf"
        )

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# MAIN
# ==============================
def main():
    if 'viewing_course' not in st.session_state:
        st.session_state.viewing_course = None

    st.markdown("""
        <div style="text-align:center;animation:fadeInUp 0.8s ease-out;">
            <h1>🌸 English Teacher's Platform 🌸</h1>
            <p style="color:#c2185b;font-size:18px;">✨ Make learning beautiful and fun! ✨</p>
        </div>
        <div style="text-align:center;margin-bottom:20px;font-size:30px;">
            📖 📝 🎓 ✏️ 📕
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
            <div style="text-align:center;padding:20px 0;">
                <h3 style="color:#ff69b4;">✨ Welcome! ✨</h3>
                <div style="font-size:30px;">👩‍🏫</div>
            </div>
        """, unsafe_allow_html=True)
        mode = st.radio("Choose your role:",
                        ["👩‍🏫 Teacher", "👧 Student"], index=0)
        st.markdown("---")
        st.caption("🌸 Made with love for English teachers 🌸")

    metadata = load_metadata()

    if st.session_state.viewing_course is not None:
        display_presentation(st.session_state.viewing_course)
    elif mode == "👩‍🏫 Teacher":
        teacher_mode(metadata)
    else:
        student_mode(metadata)

# ==============================
# TEACHER MODE
# ==============================
def teacher_mode(metadata):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🌸 Upload New Course")
        lc1, lc2 = st.columns(2)
        with lc1:
            level = st.selectbox("📚 Main Level", ["A", "B", "C"])
        with lc2:
            sub_level = st.selectbox("🎯 Sub-level", ["1", "2", "3"])
        full_level = f"{level}{sub_level}"

        title       = st.text_input("📖 Course Title",
                                    placeholder="e.g., Present Simple Tense")
        description = st.text_area("💭 Description",
                                   placeholder="What will students learn?")
        uploaded    = st.file_uploader("📎 Upload PDF File", type=["pdf"])

        if st.button("💖 Save Course", use_container_width=True):
            if title and uploaded:
                file_bytes   = uploaded.getbuffer().tobytes()
                storage_path = f"{full_level}/{uploaded.name}"
                course_id    = f"{full_level}_{uploaded.name}"

                with st.spinner("⬆️ Upload en cours…"):
                    upload_pdf(file_bytes, storage_path)
                    save_course(course_id, {
                        "title":        title,
                        "description":  description or "No description",
                        "level":        full_level,
                        "filename":     uploaded.name,
                        "storage_path": storage_path,
                        "upload_date":  time.strftime("%Y-%m-%d %H:%M"),
                    })

                st.balloons()
                st.success(f"✨ Course '{title}' saved! ✨")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("💔 Please add a title and file!")

    with col2:
        st.subheader("📊 Quick Stats")
        st.info(f"📚 **Total courses:** {len(metadata)}")
        if metadata:
            cnt = {}
            for c in metadata.values():
                cnt[c["level"]] = cnt.get(c["level"], 0) + 1
            st.write("**Courses per level:**")
            for lv, n in sorted(cnt.items()):
                st.progress(min(n / 10, 1.0), text=f"Level {lv}: {n} courses")

    st.markdown("---")
    st.subheader("📚 Manage Your Courses")

    if metadata:
        fl = st.selectbox("Filter by level:",
                          ["All"] + sorted({c["level"] for c in metadata.values()}))
        for key, course in metadata.items():
            if fl != "All" and course["level"] != fl:
                continue
            with st.container():
                ca, cb, cc = st.columns([3, 1, 1])
                with ca:
                    st.markdown(f"""
                        <div class="course-card">
                            <strong>📄 {course['title']}</strong><br>
                            <small>🎯 Level {course['level']}</small><br>
                            <small>📅 {course['upload_date']}</small><br>
                            <small>💭 {course['description']}</small>
                        </div>""", unsafe_allow_html=True)
                    if st.button("🎬 View & Present", key=f"view_{key}"):
                        for k in ['pdf_images', 'current_pdf_key', 'current_page']:
                            st.session_state.pop(k, None)
                        st.session_state.viewing_course = course
                        st.rerun()
                with cb:
                    pdf_bytes = download_pdf(course["storage_path"])
                    st.download_button("📥 Download", pdf_bytes,
                                       file_name=course["filename"],
                                       mime="application/pdf",
                                       key=f"down_{key}")
                with cc:
                    if st.button("🗑️ Delete", key=f"del_{key}"):
                        delete_pdf(course["storage_path"])
                        remove_course(key)
                        st.warning(f"💔 '{course['title']}' deleted")
                        time.sleep(0.5)
                        st.rerun()
    else:
        st.info("🌸 No courses yet. Upload your first course above!")

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# STUDENT MODE
# ==============================
def student_mode(metadata):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.subheader("🎓 Browse Your Courses")

    c1, c2 = st.columns(2)
    with c1:
        level = st.selectbox("📚 Select Main Level", ["A", "B", "C"])
    with c2:
        sub_level = st.selectbox("🎯 Select Sub-level", ["1", "2", "3"])

    full_level        = f"{level}{sub_level}"
    available_courses = {k: v for k, v in metadata.items()
                         if v["level"] == full_level}

    if available_courses:
        st.success(f"✨ Found {len(available_courses)} course(s) for Level {full_level} ✨")
        for key, course in available_courses.items():
            with st.expander(f"📖 {course['title']}", expanded=True):
                ca, cb = st.columns([2, 1])
                with ca:
                    st.markdown(f"""
                        <div style="background:#fff0f5;padding:15px;border-radius:15px;">
                            <strong>💭 Description:</strong><br>{course['description']}<br><br>
                            <strong>📅 Uploaded:</strong> {course['upload_date']}<br>
                            <strong>🎯 Level:</strong> {course['level']}<br>
                            <strong>📄 Type:</strong> PDF Document
                        </div>""", unsafe_allow_html=True)
                    if st.button("🎬 View Course", key=f"view_student_{key}"):
                        for k in ['pdf_images', 'current_pdf_key', 'current_page']:
                            st.session_state.pop(k, None)
                        st.session_state.viewing_course = course
                        st.rerun()
                with cb:
                    pdf_bytes = download_pdf(course["storage_path"])
                    st.download_button(
                        "📥 Download Course", pdf_bytes,
                        file_name=course["filename"],
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"dl_s_{key}"
                    )
                if st.button("💡 Get a tip", key=f"tip_{key}"):
                    import random
                    tips = ["✨ Take notes while reading!",
                            "💕 Practice with a friend!",
                            "⭐ Review key vocabulary after!",
                            "🌸 Ask questions if something is unclear!"]
                    st.info(f"💖 Tip: {random.choice(tips)}")
    else:
        st.warning(f"💔 No courses available for Level {full_level} yet.")
        st.markdown("""
            <div style="text-align:center;padding:40px;">
                <div style="font-size:50px;">📚✨</div>
                <p style="color:#c2185b;">Ask your teacher to upload courses for this level!</p>
            </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    main()
