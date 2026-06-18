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

    @keyframes fadeInUp {
        from { transform: translateY(20px); opacity: 0; }
        to   { transform: translateY(0);    opacity: 1; }
    }
    .fade-in { animation: fadeInUp 0.6s ease-out; }
</style>
""", unsafe_allow_html=True)

# ==============================
# FOLDERS
# ==============================
def init_folders():
    for level in ["A", "B", "C"]:
        for sub in ["1", "2", "3"]:
            Path(f"courses/Level_{level}/{level}{sub}").mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    Path("courses/pdf_pages").mkdir(parents=True, exist_ok=True)

# ==============================
# METADATA
# ==============================
def load_metadata():
    p = "data/courses_metadata.json"
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    with open("data/courses_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

# ==============================
# DELETE
# ==============================
def delete_course(course_key, course_path, pdf_pages_folder=None):
    try:
        if os.path.exists(course_path):
            os.remove(course_path)
        if pdf_pages_folder and os.path.exists(pdf_pages_folder):
            shutil.rmtree(pdf_pages_folder)
        metadata = load_metadata()
        if course_key in metadata:
            del metadata[course_key]
            save_metadata(metadata)
        return True
    except Exception as e:
        st.error(f"Delete error: {e}")
        return False

# ==============================
# PDF → LIST OF BASE64 IMAGES
# ==============================
def pdf_to_base64_images(pdf_path: str, cache_dir: str) -> list[str]:
    """
    Convert each PDF page to a PNG and return list of base64 strings.
    Results are cached on disk so repeat views are instant.
    """
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)

    cached_pngs = sorted(cache.glob("page_*.png"))
    pdf_mtime   = Path(pdf_path).stat().st_mtime

    # Use cache if fresh
    if cached_pngs and cache.stat().st_mtime >= pdf_mtime:
        b64_list = []
        for p in cached_pngs:
            with open(p, "rb") as f:
                b64_list.append(base64.b64encode(f.read()).decode())
        return b64_list

    # Re-render with PyMuPDF
    doc     = fitz.open(pdf_path)
    b64_list = []
    for i, page in enumerate(doc):
        mat = fitz.Matrix(2.0, 2.0)          # 144 DPI — crisp on screen
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        if img.width > 1400:                 # cap width for performance
            ratio    = 1400 / img.width
            img      = img.resize((1400, int(img.height * ratio)), Image.LANCZOS)

        png_path = cache / f"page_{i:04d}.png"
        img.save(str(png_path), "PNG", optimize=True)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64_list.append(base64.b64encode(buf.getvalue()).decode())

    doc.close()
    return b64_list

# ==============================
# FULLSCREEN VIEWER (iframe trick)
# The only reliable way to get true fullscreen in Streamlit is to
# build a self-contained HTML page inside st.components.v1.html,
# because that component IS rendered in its own iframe with the
# browser's native fullscreen API available.
# We embed ALL slide images as base64 so no server round-trip is needed.
# ==============================
def build_fullscreen_viewer(b64_images: list[str], title: str) -> str:
    """Return a complete HTML page with slide viewer + fullscreen button."""

    # Serialise images as a JS array of data-URIs
    js_images = "[\n" + ",\n".join(
        f'  "data:image/png;base64,{b64}"' for b64 in b64_images
    ) + "\n]"

    total = len(b64_images)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: linear-gradient(135deg, #ffe6f0, #ffd9e8);
    display: flex; flex-direction: column;
    align-items: center;
    padding: 12px 8px;
    min-height: 100vh;
  }}

  #viewer {{
    width: 100%; max-width: 960px;
    background: white;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(255,20,147,.2);
    border: 2px solid #ffc0cb;
    overflow: hidden;
  }}

  /* ── header ── */
  #viewer-header {{
    background: linear-gradient(90deg, #ff69b4, #ff1493);
    color: white;
    padding: 14px 20px;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 8px;
  }}
  #viewer-header h2 {{ font-size: 1rem; font-weight: 700; flex: 1; }}

  /* ── slide image ── */
  #slide-wrap {{
    padding: 16px;
    text-align: center;
    background: #fff;
  }}
  #slide-img {{
    max-width: 100%;
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,.12);
    display: block;
    margin: 0 auto;
  }}

  /* ── nav bar ── */
  #nav {{
    display: flex; align-items: center; justify-content: center;
    gap: 10px;
    padding: 14px 20px;
    background: #fff0f5;
    border-top: 1px solid #ffc0cb;
    flex-wrap: wrap;
  }}
  button {{
    background: linear-gradient(45deg, #ff69b4, #ff1493);
    color: white; border: none; border-radius: 25px;
    padding: 10px 22px; font-weight: bold; font-size: .9rem;
    cursor: pointer; transition: transform .2s;
  }}
  button:hover:not(:disabled) {{ transform: scale(1.06); }}
  button:disabled {{ opacity: .4; cursor: not-allowed; transform: none; }}

  #fs-btn {{
    background: linear-gradient(45deg, #9c27b0, #7b1fa2);
    padding: 10px 18px;
  }}

  #counter {{
    background: white; border: 2px solid #ff69b4;
    border-radius: 20px; padding: 8px 20px;
    color: #c2185b; font-weight: bold; min-width: 110px;
    text-align: center; font-size: .95rem;
  }}

  /* ── progress ── */
  #prog-wrap {{
    height: 8px; background: #ffe0ec;
    margin: 0; border-radius: 0;
  }}
  #prog-fill {{
    height: 100%;
    background: linear-gradient(90deg, #ff69b4, #ff1493);
    transition: width .3s ease;
    border-radius: 0;
  }}

  /* ── fullscreen overrides ── */
  :fullscreen #viewer,
  :-webkit-full-screen #viewer,
  :-moz-full-screen #viewer {{
    max-width: 100vw; width: 100vw;
    border-radius: 0; border: none;
    height: 100vh;
    display: flex; flex-direction: column;
  }}
  :fullscreen #slide-wrap,
  :-webkit-full-screen #slide-wrap,
  :-moz-full-screen #slide-wrap {{
    flex: 1; display: flex;
    align-items: center; justify-content: center;
    overflow: auto;
  }}
  :fullscreen body,
  :-webkit-full-screen body,
  :-moz-full-screen body {{
    padding: 0; background: #111;
    justify-content: flex-start;
  }}
</style>
</head>
<body>

<div id="viewer">
  <div id="viewer-header">
    <h2>📖 {title}</h2>
    <button id="fs-btn" onclick="toggleFS()">⛶ Fullscreen</button>
  </div>

  <div id="prog-wrap"><div id="prog-fill" style="width:0%"></div></div>

  <div id="slide-wrap">
    <img id="slide-img" src="" alt="slide"/>
  </div>

  <div id="nav">
    <button id="btn-first"  onclick="goTo(0)"           title="First">⏮</button>
    <button id="btn-prev"   onclick="goTo(cur-1)"        title="Previous">◀ Prev</button>
    <span   id="counter"    class="">1 / {total}</span>
    <button id="btn-next"   onclick="goTo(cur+1)"        title="Next">Next ▶</button>
    <button id="btn-last"   onclick="goTo(total-1)"      title="Last">⏭</button>
  </div>
</div>

<script>
const images = {js_images};
const total  = {total};
let   cur    = 0;

function goTo(n) {{
  n = Math.max(0, Math.min(total - 1, n));
  cur = n;
  document.getElementById('slide-img').src        = images[n];
  document.getElementById('counter').textContent  = (n+1) + ' / ' + total;
  document.getElementById('prog-fill').style.width = ((n+1)/total*100) + '%';
  document.getElementById('btn-prev').disabled  = (n === 0);
  document.getElementById('btn-first').disabled = (n === 0);
  document.getElementById('btn-next').disabled  = (n === total-1);
  document.getElementById('btn-last').disabled  = (n === total-1);
}}

function toggleFS() {{
  var el = document.getElementById('viewer');
  var fsEl = document.fullscreenElement ||
             document.webkitFullscreenElement ||
             document.mozFullScreenElement;
  if (!fsEl) {{
    (el.requestFullscreen    ||
     el.webkitRequestFullscreen ||
     el.mozRequestFullScreen).call(el);
  }} else {{
    (document.exitFullscreen    ||
     document.webkitExitFullscreen ||
     document.mozCancelFullScreen).call(document);
  }}
}}

// Keyboard arrows
document.addEventListener('keydown', function(e) {{
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown')  goTo(cur+1);
  if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')    goTo(cur-1);
  if (e.key === 'Home')                                  goTo(0);
  if (e.key === 'End')                                   goTo(total-1);
  if (e.key === 'f' || e.key === 'F')                    toggleFS();
}});

// Init
goTo(0);
</script>
</body>
</html>"""

# ==============================
# DISPLAY PRESENTATION
# ==============================
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)

    if st.button("◀ Back to Courses"):
        st.session_state["viewing_course"] = None
        for k in ["b64_images", "current_pdf_key"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown(f"### 📖 {course['title']}")
    st.markdown(f"🎯 Level **{course['level']}** &nbsp;|&nbsp; 📅 {course['upload_date']}")
    st.markdown(f"💭 {course['description']}")
    st.markdown("---")

    course_key = f"{course['level']}_{Path(course['filename']).stem}"
    cache_dir  = f"courses/pdf_pages/{course_key}"

    # Load / cache images
    if st.session_state.get("current_pdf_key") != course_key:
        with st.spinner("🔄 Loading slides… first open may take a moment."):
            try:
                imgs = pdf_to_base64_images(course["path"], cache_dir)
                st.session_state["b64_images"]     = imgs
                st.session_state["current_pdf_key"] = course_key
            except Exception as e:
                st.error(f"❌ Cannot render PDF: {e}")
                with open(course["path"], "rb") as f:
                    st.download_button("📥 Download PDF", f,
                                       file_name=course["filename"],
                                       mime="application/pdf")
                return

    b64_images = st.session_state.get("b64_images", [])
    if not b64_images:
        st.warning("No pages found in this PDF.")
        return

    # Build the self-contained HTML viewer and render it inside
    # st.components.v1.html — this iframe has a real document context
    # so requestFullscreen() works perfectly.
    viewer_html = build_fullscreen_viewer(b64_images, course["title"])

    # Height = enough to show one slide comfortably; user can fullscreen for more
    st.components.v1.html(viewer_html, height=780, scrolling=False)

    st.caption("💡 Use ← → arrow keys to navigate · Press **F** or ⛶ for fullscreen")

    st.markdown("---")
    with open(course["path"], "rb") as f:
        st.download_button(
            "📥 Download Original PDF", f,
            file_name=course["filename"],
            mime="application/pdf"
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# MAIN
# ==============================
def main():
    if "viewing_course" not in st.session_state:
        st.session_state["viewing_course"] = None

    st.markdown("""
        <div style="text-align:center;animation:fadeInUp .8s ease-out">
            <h1>🌸 English Teacher's Platform 🌸</h1>
            <p style="color:#c2185b;font-size:18px">✨ Make learning beautiful and fun! ✨</p>
        </div>
        <div style="text-align:center;margin-bottom:20px;font-size:30px">
            📖 📝 🎓 ✏️ 📕
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
            <div style="text-align:center;padding:20px 0">
                <h3 style="color:#ff69b4">✨ Welcome! ✨</h3>
                <div style="font-size:30px">👩‍🏫</div>
            </div>
        """, unsafe_allow_html=True)
        mode = st.radio("Choose your role:",
                        ["👩‍🏫 Teacher", "👧 Student"], index=0)
        st.markdown("---")
        st.caption("🌸 Made with love for English teachers 🌸")

    metadata = load_metadata()

    if st.session_state["viewing_course"] is not None:
        display_presentation(st.session_state["viewing_course"])
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
                folder = Path(f"courses/Level_{level}/{full_level}")
                folder.mkdir(parents=True, exist_ok=True)
                save_path = folder / uploaded.name
                with open(save_path, "wb") as f:
                    f.write(uploaded.getbuffer())

                # Pre-render cache so first view is instant
                course_key = f"{full_level}_{Path(uploaded.name).stem}"
                with st.spinner("⚙️ Pre-processing pages…"):
                    pdf_to_base64_images(str(save_path),
                                         f"courses/pdf_pages/{course_key}")

                key = f"{full_level}_{uploaded.name}"
                metadata[key] = {
                    "title":       title,
                    "description": description or "No description",
                    "level":       full_level,
                    "path":        str(save_path),
                    "filename":    uploaded.name,
                    "upload_date": time.strftime("%Y-%m-%d %H:%M"),
                    "type":        "pdf",
                }
                save_metadata(metadata)
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
                        for k in ["b64_images", "current_pdf_key"]:
                            st.session_state.pop(k, None)
                        st.session_state["viewing_course"] = course
                        st.rerun()
                with cb:
                    with open(course["path"], "rb") as f:
                        st.download_button("📥 Download", f,
                                           file_name=course["filename"],
                                           mime="application/pdf",
                                           key=f"down_{key}")
                with cc:
                    if st.button("🗑️ Delete", key=f"del_{key}"):
                        pdf_pages = Path(
                            f"courses/pdf_pages/{course['level']}_{Path(course['filename']).stem}"
                        )
                        if delete_course(key, course["path"], pdf_pages):
                            st.warning(f"💔 '{course['title']}' deleted")
                            time.sleep(0.5)
                            st.rerun()
    else:
        st.info("🌸 No courses yet. Upload your first course above!")

    st.markdown("</div>", unsafe_allow_html=True)

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
                        <div style="background:#fff0f5;padding:15px;border-radius:15px">
                            <strong>💭 Description:</strong><br>{course['description']}<br><br>
                            <strong>📅 Uploaded:</strong> {course['upload_date']}<br>
                            <strong>🎯 Level:</strong> {course['level']}
                        </div>""", unsafe_allow_html=True)
                    if st.button("🎬 View Course", key=f"view_s_{key}"):
                        for k in ["b64_images", "current_pdf_key"]:
                            st.session_state.pop(k, None)
                        st.session_state["viewing_course"] = course
                        st.rerun()
                with cb:
                    with open(course["path"], "rb") as f:
                        st.download_button(
                            "📥 Download Course", f,
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
            <div style="text-align:center;padding:40px">
                <div style="font-size:50px">📚✨</div>
                <p style="color:#c2185b">Ask your teacher to upload courses for this level!</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    init_folders()
    main()
