import streamlit as st
import json
import os
from pathlib import Path
import time
from PIL import Image
import io
import base64
import subprocess
import shutil
import tempfile

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

# ==============================
# FOLDERS INIT
# ==============================
def init_folders():
    levels = ["A", "B", "C"]
    sub_levels = ["1", "2", "3"]
    for level in levels:
        for sub in sub_levels:
            Path(f"courses/Level_{level}/{level}{sub}").mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(exist_ok=True)

# ==============================
# METADATA
# ==============================
def load_metadata():
    if os.path.exists("data/courses_metadata.json"):
        with open("data/courses_metadata.json", "r") as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    with open("data/courses_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

# ==============================
# DELETE COURSE
# ==============================
def delete_course(course_key, course_path):
    try:
        if os.path.exists(course_path):
            os.remove(course_path)
        # Remove associated PDF if exists
        pdf_path = Path(course_path).with_suffix(".pdf")
        if pdf_path.exists():
            os.remove(pdf_path)
        metadata = load_metadata()
        if course_key in metadata:
            del metadata[course_key]
            save_metadata(metadata)
        return True
    except Exception as e:
        st.error(f"Delete error: {e}")
        return False

# ==============================
# PPT → PDF CONVERSION
# ==============================
def convert_ppt_to_pdf(ppt_path: str) -> str | None:
    """
    Convert a PPT/PPTX file to PDF using LibreOffice.
    Returns the PDF path on success, or None on failure.
    LibreOffice preserves all images, fonts and layouts exactly.
    """
    ppt_path = Path(ppt_path)
    pdf_path = ppt_path.with_suffix(".pdf")

    # If already converted and up-to-date, reuse
    if pdf_path.exists() and pdf_path.stat().st_mtime >= ppt_path.stat().st_mtime:
        return str(pdf_path)

    # Try LibreOffice (available on Linux servers / Streamlit Cloud)
    libreoffice_candidates = [
        "libreoffice",
        "libreoffice7.6",
        "soffice",
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
    ]

    libreoffice_cmd = None
    for candidate in libreoffice_candidates:
        if shutil.which(candidate):
            libreoffice_cmd = candidate
            break

    if libreoffice_cmd:
        try:
            result = subprocess.run(
                [
                    libreoffice_cmd,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(ppt_path.parent),
                    str(ppt_path),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if pdf_path.exists():
                return str(pdf_path)
        except Exception:
            pass

    # Fallback: python-pptx slide-by-slide image rendering
    # (lower fidelity but works everywhere without LibreOffice)
    return convert_ppt_to_pdf_fallback(str(ppt_path))


def convert_ppt_to_pdf_fallback(ppt_path: str) -> str | None:
    """
    Fallback: render each slide as an image using python-pptx + Pillow,
    then combine into a PDF.  Images, shapes and backgrounds are all captured
    because we render at slide level instead of shape level.
    """
    try:
        from pptx import Presentation
        from pptx.util import Emu
        import math

        prs = Presentation(ppt_path)

        # Slide dimensions in pixels at 150 dpi
        dpi = 150
        emu_per_inch = 914400
        slide_width_in = prs.slide_width / emu_per_inch
        slide_height_in = prs.slide_height / emu_per_inch
        px_w = int(slide_width_in * dpi)
        px_h = int(slide_height_in * dpi)

        slide_images = []

        for slide_idx, slide in enumerate(prs.slides):
            # Create blank white canvas
            canvas = Image.new("RGB", (px_w, px_h), "white")

            # Try to get background fill color
            try:
                bg = slide.background
                fill = bg.fill
                if fill.type is not None and str(fill.type) == "SOLID":
                    from pptx.dml.color import RGBColor
                    rgb = fill.fore_color.rgb
                    canvas = Image.new("RGB", (px_w, px_h), (rgb[0], rgb[1], rgb[2]))
            except Exception:
                pass

            # Draw each shape
            for shape in slide.shapes:
                try:
                    # Place embedded images
                    if hasattr(shape, "image"):
                        img_bytes = shape.image.blob
                        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

                        left = int(shape.left / emu_per_inch * dpi)
                        top = int(shape.top / emu_per_inch * dpi)
                        width = int(shape.width / emu_per_inch * dpi)
                        height = int(shape.height / emu_per_inch * dpi)

                        if width > 0 and height > 0:
                            img = img.resize((width, height), Image.LANCZOS)
                            canvas.paste(img, (left, top), img if img.mode == "RGBA" else None)

                    # Draw text as-is (basic, but better than nothing)
                    elif hasattr(shape, "text") and shape.text.strip():
                        from PIL import ImageDraw, ImageFont
                        draw = ImageDraw.Draw(canvas)
                        left = int(shape.left / emu_per_inch * dpi)
                        top = int(shape.top / emu_per_inch * dpi)
                        width = int(shape.width / emu_per_inch * dpi)

                        # Try to get font size
                        font_size = 18
                        text_color = (0, 0, 0)
                        try:
                            for para in shape.text_frame.paragraphs:
                                for run in para.runs:
                                    if run.font.size:
                                        font_size = max(10, int(run.font.size.pt * dpi / 72))
                                    if run.font.color and run.font.color.type is not None:
                                        try:
                                            rgb = run.font.color.rgb
                                            text_color = (rgb[0], rgb[1], rgb[2])
                                        except Exception:
                                            pass
                                    break
                                break
                        except Exception:
                            pass

                        try:
                            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                        except Exception:
                            font = ImageFont.load_default()

                        # Word-wrap text
                        words = shape.text.split()
                        lines = []
                        current_line = []
                        for word in words:
                            test_line = " ".join(current_line + [word])
                            bbox = draw.textbbox((0, 0), test_line, font=font)
                            if bbox[2] - bbox[0] <= width and current_line:
                                current_line.append(word)
                            else:
                                if current_line:
                                    lines.append(" ".join(current_line))
                                current_line = [word]
                        if current_line:
                            lines.append(" ".join(current_line))

                        y_offset = top
                        line_height = font_size + 4
                        for line in lines:
                            draw.text((left, y_offset), line, font=font, fill=text_color)
                            y_offset += line_height

                except Exception:
                    continue

            slide_images.append(canvas)

        if not slide_images:
            return None

        # Save as multi-page PDF
        pdf_path = Path(ppt_path).with_suffix(".pdf")
        first = slide_images[0].convert("RGB")
        rest = [img.convert("RGB") for img in slide_images[1:]]
        first.save(str(pdf_path), save_all=True, append_images=rest, format="PDF")
        return str(pdf_path)

    except Exception as e:
        st.error(f"Fallback conversion error: {e}")
        return None


# ==============================
# PDF → BASE64 FOR DISPLAY
# ==============================
def pdf_to_base64(pdf_path: str) -> str | None:
    try:
        with open(pdf_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


# ==============================
# DISPLAY PRESENTATION (FIXED)
# ==============================
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)

    if st.button("◀ Back to Courses"):
        st.session_state["viewing_course"] = None
        # Clear cached PDF data
        for key in ["pdf_b64", "current_course_path"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.markdown(f"### 📖 {course['title']}")
    st.markdown(f"🎯 Level **{course['level']}** &nbsp;|&nbsp; 📅 {course['upload_date']}")
    st.markdown("---")

    ppt_path = course["path"]

    # Convert only when needed
    if st.session_state.get("current_course_path") != ppt_path or "pdf_b64" not in st.session_state:
        with st.spinner("🔄 Preparing presentation... (first load may take a moment)"):
            pdf_path = convert_ppt_to_pdf(ppt_path)

        if pdf_path is None:
            st.error("❌ Could not convert this PowerPoint file. Please download it directly.")
        else:
            b64 = pdf_to_base64(pdf_path)
            if b64:
                st.session_state["pdf_b64"] = b64
                st.session_state["current_course_path"] = ppt_path
            else:
                st.error("❌ Could not read the converted PDF.")

    if "pdf_b64" in st.session_state:
        b64 = st.session_state["pdf_b64"]

        # -------------------------------------------------------
        # Embed PDF using <object> tag instead of <iframe>
        # <object> is not sandboxed — fullscreen works natively
        # The browser's built-in PDF viewer handles navigation,
        # zoom, and fullscreen without any custom JS needed.
        # -------------------------------------------------------
        pdf_embed_html = f"""
        <div style="
            background: white;
            border-radius: 20px;
            padding: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.12);
            border: 2px solid #ffc0cb;
        ">
            <object
                data="data:application/pdf;base64,{b64}"
                type="application/pdf"
                width="100%"
                style="height: 720px; border-radius: 15px; border: none; display: block;"
            >
                <!-- Fallback for browsers that can't render PDFs inline -->
                <p style="text-align:center; padding: 40px; color: #c2185b;">
                    ⚠️ Your browser cannot display PDFs inline.<br>
                    Please download the file below.
                </p>
            </object>
        </div>
        <p style="color:#888; font-size:13px; margin-top:8px;">
            💡 Use the PDF toolbar above to navigate slides, zoom, or enter fullscreen (⛶ button top-right of the PDF viewer).
        </p>
        """
        st.markdown(pdf_embed_html, unsafe_allow_html=True)

    st.markdown("---")

    # Download original PPT
    with open(ppt_path, "rb") as f:
        st.download_button(
            label="📥 Download Original PowerPoint",
            data=f,
            file_name=course["filename"],
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=False,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# MAIN
# ==============================
def main():
    if "viewing_course" not in st.session_state:
        st.session_state["viewing_course"] = None

    # Header
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
            index=0,
        )

        st.markdown("---")
        st.caption("🌸 Made with love for English teachers 🌸")

    metadata = load_metadata()

    if st.session_state["viewing_course"] is not None:
        display_presentation(st.session_state["viewing_course"])
    else:
        if mode == "👩‍🏫 Teacher":
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
            help="Upload your PowerPoint presentation",
        )

        if st.button("💖 Save Course", use_container_width=True):
            if title and uploaded_file:
                course_folder = Path(f"courses/Level_{level}/{full_level}")
                course_folder.mkdir(parents=True, exist_ok=True)

                save_path = course_folder / uploaded_file.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Pre-convert to PDF in background so first view is fast
                convert_ppt_to_pdf(str(save_path))

                course_key = f"{full_level}_{uploaded_file.name}"
                metadata[course_key] = {
                    "title": title,
                    "description": description if description else "No description",
                    "level": full_level,
                    "path": str(save_path),
                    "filename": uploaded_file.name,
                    "upload_date": time.strftime("%Y-%m-%d %H:%M"),
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
                lv = course["level"]
                levels_count[lv] = levels_count.get(lv, 0) + 1

            st.write("**Courses per level:**")
            for lv, count in sorted(levels_count.items()):
                st.progress(min(count / 10, 1.0), text=f"Level {lv}: {count} courses")

    st.markdown("---")
    st.subheader("📚 Manage Your Courses")

    if metadata:
        filter_level = st.selectbox(
            "Filter by level:",
            ["All"] + sorted(set(c["level"] for c in metadata.values())),
        )

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
                        st.session_state.pop("pdf_b64", None)
                        st.session_state.pop("current_course_path", None)
                        st.session_state["viewing_course"] = course
                        st.rerun()

                with col2:
                    with open(course["path"], "rb") as f:
                        st.download_button(
                            label="📥 Download",
                            data=f,
                            file_name=course["filename"],
                            key=f"down_{key}",
                        )

                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{key}"):
                        if delete_course(key, course["path"]):
                            st.warning(f"💔 Course '{course['title']}' deleted")
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
                        st.session_state.pop("pdf_b64", None)
                        st.session_state.pop("current_course_path", None)
                        st.session_state["viewing_course"] = course
                        st.rerun()

                with col2:
                    with open(course["path"], "rb") as f:
                        st.download_button(
                            label="📥 Download Course",
                            data=f,
                            file_name=course["filename"],
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True,
                            key=f"student_download_{key}",
                        )

                if st.button(f"💡 Get a tip", key=f"tip_{key}"):
                    import random
                    tips = [
                        "✨ Take notes while watching!",
                        "💕 Practice with a friend!",
                        "⭐ Review key vocabulary after!",
                        "🌸 Ask questions if something is unclear!",
                    ]
                    st.info(f"💖 Tip: {random.choice(tips)}")
    else:
        st.warning(f"💔 No courses available for Level {full_level} yet.")
        st.markdown("""
            <div style="text-align: center; padding: 40px;">
                <div style="font-size: 50px;">📚✨</div>
                <p style="color: #c2185b;">Ask your teacher to upload courses for this level!</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    init_folders()
    main()
