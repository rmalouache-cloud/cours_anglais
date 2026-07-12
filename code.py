import streamlit as st
import json
import time
from PIL import Image
import io
import base64
import fitz  # PyMuPDF
import requests

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="✨ English Teacher's Platform ✨",
    page_icon="🌸",
    layout="wide"
)

# ==============================
# CUSTOM CSS
# ==============================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 100%);
    }
    h1, h2, h3 { color: #c2185b !important; }
    .stButton > button {
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        color: white; border-radius: 25px; border: none;
        padding: 12px 25px; font-weight: bold; transition: all 0.3s ease;
    }
    .stButton > button:hover { transform: scale(1.05); }
    .course-card {
        background: white; border-radius: 20px; padding: 20px;
        margin: 10px 0; box-shadow: 0 5px 15px rgba(0,0,0,0.08);
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
# GITHUB CONFIG
# Tout est stocké dans ton repo GitHub :
#   - PDFs        → pdfs/{level}/{filename}
#   - Métadonnées → data/courses_metadata.json
# ==============================
def gh_headers():
    return {
        "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json"
    }

def gh_url(path):
    """URL API GitHub pour un fichier donné."""
    repo = st.secrets["GITHUB_REPO"]   # ex: "rmalouache-cloud/cours_anglais"
    return f"https://api.github.com/repos/{repo}/contents/{path}"

def gh_get_file(path):
    """Récupère un fichier depuis GitHub. Retourne (content_bytes, sha) ou (None, None)."""
    r = requests.get(gh_url(path), headers=gh_headers(), timeout=15)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    data    = r.json()
    content = base64.b64decode(data["content"])
    return content, data["sha"]

def gh_put_file(path, content_bytes, sha=None, message="update"):
    """Crée ou met à jour un fichier sur GitHub."""
    payload = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode("utf-8"),
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(gh_url(path), headers=gh_headers(),
                     json=payload, timeout=30)
    if r.status_code not in (200, 201):
        st.error(f"❌ GitHub upload error {r.status_code}: {r.text[:300]}")
        return False
    return True

def gh_delete_file(path, sha, message="delete file"):
    """Supprime un fichier sur GitHub."""
    payload = {"message": message, "sha": sha}
    r = requests.delete(gh_url(path), headers=gh_headers(),
                        json=payload, timeout=15)
    return r.status_code == 200

# ==============================
# MÉTADONNÉES  (JSON dans GitHub)
# ==============================
METADATA_PATH = "data/courses_metadata.json"

def load_metadata() -> dict:
    try:
        content, _ = gh_get_file(METADATA_PATH)
        if content is None:
            return {}
        return json.loads(content.decode("utf-8"))
    except Exception as e:
        st.error(f"❌ Cannot load metadata: {e}")
        return {}

def save_metadata(metadata: dict):
    try:
        _, sha = gh_get_file(METADATA_PATH)
        content_bytes = json.dumps(metadata, indent=2,
                                   ensure_ascii=False).encode("utf-8")
        gh_put_file(METADATA_PATH, content_bytes,
                    sha=sha, message="update courses metadata")
    except Exception as e:
        st.error(f"❌ Cannot save metadata: {e}")

def add_course(course_id: str, data: dict):
    metadata = load_metadata()
    metadata[course_id] = data
    save_metadata(metadata)

def remove_course(course_id: str):
    metadata = load_metadata()
    if course_id in metadata:
        del metadata[course_id]
        save_metadata(metadata)

# ==============================
# PDFs  (fichiers binaires dans GitHub)
# GitHub accepte jusqu'à 100 MB par fichier via l'API
# ==============================
def upload_pdf(file_bytes: bytes, storage_path: str):
    """Upload un PDF dans le repo GitHub."""
    _, sha = gh_get_file(storage_path)   # sha si le fichier existe déjà
    ok = gh_put_file(storage_path, file_bytes,
                     sha=sha, message=f"add pdf {storage_path}")
    if not ok:
        raise Exception("Upload failed")

def download_pdf(storage_path: str) -> bytes:
    """Télécharge un PDF depuis GitHub."""
    content, _ = gh_get_file(storage_path)
    if content is None:
        raise Exception(f"File not found: {storage_path}")
    return content

def delete_pdf(storage_path: str):
    """Supprime un PDF du repo GitHub."""
    _, sha = gh_get_file(storage_path)
    if sha:
        gh_delete_file(storage_path, sha, message=f"delete pdf {storage_path}")

# ==============================
# PDF → BASE64 IMAGES  (PyMuPDF)
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
            img   = img.resize((1200, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        images_b64.append(base64.b64encode(buf.getvalue()).decode())
    doc.close()
    return images_b64

# ==============================
# HTML VIEWER  (identique à ton original)
# ==============================
def create_html_viewer(images_base64, current_page, total_pages, course_title):
    current_img = images_base64[current_page]
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:'Segoe UI',Arial,sans-serif;
              background:linear-gradient(135deg,#ffe6f0,#ffd9e8);padding:20px;}}
        .pc{{max-width:1100px;margin:0 auto;background:white;border-radius:20px;
              padding:30px;box-shadow:0 10px 30px rgba(0,0,0,.1);transition:all .3s;}}
        .pc:fullscreen,.pc:-webkit-full-screen,.pc:-moz-full-screen{{
            max-width:100%;width:100vw;height:100vh;border-radius:0;padding:20px;
            overflow-y:auto;background:white;display:flex;flex-direction:column;justify-content:center;}}
        .ft{{display:flex;justify-content:flex-end;margin-bottom:15px;}}
        .bfs{{background:linear-gradient(45deg,#2196F3,#1976D2);color:white;border:none;
              border-radius:25px;padding:12px 30px;font-weight:bold;cursor:pointer;
              font-size:16px;box-shadow:0 4px 15px rgba(33,150,243,.3);transition:all .3s;}}
        .bfs:hover{{transform:scale(1.05);background:linear-gradient(45deg,#1976D2,#0D47A1);}}
        .hd{{display:flex;justify-content:space-between;align-items:center;
              margin-bottom:15px;flex-wrap:wrap;gap:10px;}}
        h1{{color:#c2185b;font-size:22px;margin:0}}
        .pi{{color:#c2185b;font-weight:bold;font-size:15px;
              background:#ffe6f0;padding:6px 16px;border-radius:20px;}}
        .pb{{width:100%;height:6px;background:#f0f0f0;border-radius:3px;
              overflow:hidden;margin:10px 0 20px;}}
        .pf{{width:{((current_page+1)/total_pages)*100}%;height:100%;
              background:linear-gradient(45deg,#ff69b4,#ff1493);transition:width .3s;}}
        .iw{{width:100%;display:flex;justify-content:center;align-items:center;
              min-height:400px;background:#fafafa;border-radius:12px;
              padding:10px;margin-bottom:20px;}}
        .img{{max-width:100%;max-height:70vh;object-fit:contain;border-radius:8px;
               box-shadow:0 4px 15px rgba(0,0,0,.08);user-select:none;}}
        .nb{{display:flex;justify-content:center;gap:15px;margin:15px 0 0;flex-wrap:wrap;}}
        .bn{{background:linear-gradient(45deg,#ff69b4,#ff1493);color:white;border:none;
              border-radius:25px;padding:12px 30px;font-weight:bold;cursor:pointer;
              font-size:16px;min-width:140px;transition:all .3s;}}
        .bn:hover:not(:disabled){{transform:scale(1.05);box-shadow:0 5px 15px rgba(255,20,147,.3);}}
        .bn:disabled{{opacity:.5;cursor:not-allowed;transform:none;}}
    </style></head><body>
    <div class="pc" id="pc">
        <div class="ft"><button class="bfs" onclick="toggleFS()">🖥️ FULLSCREEN</button></div>
        <div class="hd">
            <h1>📖 {course_title}</h1>
            <div class="pi" id="pi">Page {current_page+1} / {total_pages}</div>
        </div>
        <div class="pb"><div class="pf" id="pf"></div></div>
        <div class="iw">
            <img id="img" class="img" src="data:image/png;base64,{current_img}" />
        </div>
        <div class="nb">
            <button class="bn" id="prev" {"disabled" if current_page==0 else ""}>◀◀ PREVIOUS</button>
            <button class="bn" id="next" {"disabled" if current_page==total_pages-1 else ""}>NEXT ▶▶</button>
        </div>
    </div>
    <script>
        const imgs={json.dumps(images_base64)};
        let cur={current_page};
        const tot={total_pages};
        const img=document.getElementById('img');
        const pi=document.getElementById('pi');
        const pf=document.getElementById('pf');
        const prev=document.getElementById('prev');
        const next=document.getElementById('next');
        const pc=document.getElementById('pc');

        function go(n){{
            if(n<0||n>=tot)return;
            cur=n;
            img.src='data:image/png;base64,'+imgs[n];
            pi.textContent='Page '+(n+1)+' / '+tot;
            pf.style.width=((n+1)/tot*100)+'%';
            prev.disabled=(n===0);
            next.disabled=(n===tot-1);
        }}
        prev.onclick=function(){{if(cur>0)go(cur-1);}};
        next.onclick=function(){{if(cur<tot-1)go(cur+1);}};
        document.addEventListener('keydown',function(e){{
            if(e.key==='ArrowLeft'&&cur>0){{go(cur-1);e.preventDefault();}}
            if(e.key==='ArrowRight'&&cur<tot-1){{go(cur+1);e.preventDefault();}}
        }});
        function toggleFS(){{
            var fs=document.fullscreenElement||document.webkitFullscreenElement||document.mozFullScreenElement;
            if(!fs)(pc.requestFullscreen||pc.webkitRequestFullscreen||pc.mozRequestFullScreen).call(pc);
            else(document.exitFullscreen||document.webkitExitFullscreen||document.mozCancelFullScreen).call(document);
        }}
        document.addEventListener('fullscreenchange',function(){{
            pc.style.maxWidth=document.fullscreenElement?'100%':'1100px';
        }});
    </script></body></html>
    """

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

    if 'pdf_images' not in st.session_state or \
       st.session_state.get('current_pdf_key') != course_key:
        with st.spinner("🔄 Loading course…"):
            try:
                pdf_bytes  = download_pdf(course["storage_path"])
                images_b64 = pdf_bytes_to_base64_images(pdf_bytes)
                st.session_state.pdf_images      = images_b64
                st.session_state.current_pdf_key = course_key
                st.session_state.current_page    = 0
            except Exception as e:
                st.error(f"❌ Cannot display this PDF: {e}")
                return

    images_base64 = st.session_state.pdf_images
    total_pages   = len(images_base64)

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown(
            f"<h3 style='text-align:center;color:#c2185b;'>"
            f"Page {st.session_state.current_page+1} / {total_pages}</h3>",
            unsafe_allow_html=True
        )
        st.progress((st.session_state.current_page+1) / total_pages)
    st.markdown("---")

    html_viewer = create_html_viewer(
        images_base64, st.session_state.current_page,
        total_pages, course['title']
    )
    st.components.v1.html(html_viewer, height=780, scrolling=True)

    with st.expander("📥 Download original PDF", expanded=False):
        pdf_bytes = download_pdf(course["storage_path"])
        st.download_button("Download PDF", data=pdf_bytes,
                           file_name=course["filename"], mime="application/pdf")

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
        with lc1: level     = st.selectbox("📚 Main Level", ["A","B","C"])
        with lc2: sub_level = st.selectbox("🎯 Sub-level",  ["1","2","3"])
        full_level  = f"{level}{sub_level}"
        title       = st.text_input("📖 Course Title", placeholder="e.g., Present Simple Tense")
        description = st.text_area("💭 Description",   placeholder="What will students learn?")
        uploaded    = st.file_uploader("📎 Upload PDF File", type=["pdf"])

        if st.button("💖 Save Course", use_container_width=True):
            if title and uploaded:
                file_bytes   = uploaded.getbuffer().tobytes()
                storage_path = f"pdfs/{full_level}/{uploaded.name}"
                course_id    = f"{full_level}_{uploaded.name}"

                with st.spinner("⬆️ Uploading PDF to GitHub…"):
                    try:
                        upload_pdf(file_bytes, storage_path)
                    except Exception as e:
                        st.error(f"❌ Upload failed: {e}")
                        return

                with st.spinner("💾 Saving metadata…"):
                    add_course(course_id, {
                        "id":           course_id,
                        "title":        title,
                        "description":  description or "No description",
                        "level":        full_level,
                        "filename":     uploaded.name,
                        "storage_path": storage_path,
                        "upload_date":  time.strftime("%Y-%m-%d %H:%M"),
                    })

                st.balloons()
                st.success(f"✨ Course '{title}' saved successfully! ✨")
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
                st.progress(min(n/10, 1.0), text=f"Level {lv}: {n} courses")

    st.markdown("---")
    st.subheader("📚 Manage Your Courses")

    if metadata:
        fl = st.selectbox("Filter by level:",
                          ["All"] + sorted({c["level"] for c in metadata.values()}))
        for key, course in metadata.items():
            if fl != "All" and course["level"] != fl: continue
            ca, cb, cc = st.columns([3,1,1])
            with ca:
                st.markdown(f"""
                    <div class="course-card">
                        <strong>📄 {course['title']}</strong><br>
                        <small>🎯 Level {course['level']}</small><br>
                        <small>📅 {course['upload_date']}</small><br>
                        <small>💭 {course['description']}</small>
                    </div>""", unsafe_allow_html=True)
                if st.button("🎬 View & Present", key=f"view_{key}"):
                    for k in ['pdf_images','current_pdf_key','current_page']:
                        st.session_state.pop(k, None)
                    st.session_state.viewing_course = course
                    st.rerun()
            with cb:
                pdf_bytes = download_pdf(course["storage_path"])
                st.download_button("📥 Download", pdf_bytes,
                                   file_name=course["filename"],
                                   mime="application/pdf", key=f"down_{key}")
            with cc:
                if st.button("🗑️ Delete", key=f"del_{key}"):
                    with st.spinner("🗑️ Deleting…"):
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
    with c1: level     = st.selectbox("📚 Select Main Level", ["A","B","C"])
    with c2: sub_level = st.selectbox("🎯 Select Sub-level",  ["1","2","3"])

    full_level        = f"{level}{sub_level}"
    available_courses = {k: v for k,v in metadata.items() if v["level"]==full_level}

    if available_courses:
        st.success(f"✨ Found {len(available_courses)} course(s) for Level {full_level} ✨")
        for key, course in available_courses.items():
            with st.expander(f"📖 {course['title']}", expanded=True):
                ca, cb = st.columns([2,1])
                with ca:
                    st.markdown(f"""
                        <div style="background:#fff0f5;padding:15px;border-radius:15px;">
                            <strong>💭 Description:</strong><br>{course['description']}<br><br>
                            <strong>📅 Uploaded:</strong> {course['upload_date']}<br>
                            <strong>🎯 Level:</strong> {course['level']}<br>
                            <strong>📄 Type:</strong> PDF Document
                        </div>""", unsafe_allow_html=True)
                    if st.button("🎬 View Course", key=f"view_student_{key}"):
                        for k in ['pdf_images','current_pdf_key','current_page']:
                            st.session_state.pop(k, None)
                        st.session_state.viewing_course = course
                        st.rerun()
                with cb:
                    pdf_bytes = download_pdf(course["storage_path"])
                    st.download_button(
                        "📥 Download Course", pdf_bytes,
                        file_name=course["filename"], mime="application/pdf",
                        use_container_width=True, key=f"dl_s_{key}"
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
