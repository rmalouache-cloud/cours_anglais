import streamlit as st
import json
import os
from pathlib import Path
import time
from PIL import Image
import io
import random

# Page configuration
st.set_page_config(
    page_title="✨ English Teacher's Platform ✨",
    page_icon="🌸",
    layout="wide"
)

# Custom CSS with animations and interactions
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 100%);
    }
    
    h1, h2, h3 {
        color: #c2185b !important;
    }
    
    /* Animated buttons */
    .stButton > button {
        background: linear-gradient(45deg, #ff69b4, #ff1493);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 12px 25px;
        font-weight: bold;
        transition: all 0.3s ease;
        animation: pulse 2s infinite;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        animation: none;
        box-shadow: 0 0 20px rgba(255,105,180,0.5);
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    /* Floating animation for cards */
    .course-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border: 1px solid #ffc0cb;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .course-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 15px 30px rgba(0,0,0,0.15);
    }
    
    /* Bouncing emoji */
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    .bouncing-emoji {
        animation: bounce 1s ease-in-out infinite;
        display: inline-block;
        font-size: 30px;
        margin: 0 5px;
    }
    
    /* Rotating heart */
    @keyframes heartbeat {
        0% { transform: scale(1); }
        25% { transform: scale(1.2); }
        50% { transform: scale(1); }
        75% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    .heartbeat {
        animation: heartbeat 1.5s ease-in-out infinite;
        display: inline-block;
    }
    
    /* Sparkle effect */
    @keyframes sparkle {
        0% { opacity: 0; transform: scale(0); }
        50% { opacity: 1; transform: scale(1.2); }
        100% { opacity: 0; transform: scale(0); }
    }
    
    .sparkle {
        position: fixed;
        pointer-events: none;
        animation: sparkle 1s ease-out forwards;
        font-size: 20px;
    }
    
    /* Slide-in animation */
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .slide-in {
        animation: slideIn 0.5s ease-out;
    }
    
    /* Glowing text */
    @keyframes glow {
        0% { text-shadow: 0 0 5px #ff69b4; }
        50% { text-shadow: 0 0 20px #ff69b4, 0 0 30px #ff1493; }
        100% { text-shadow: 0 0 5px #ff69b4; }
    }
    
    .glow-text {
        animation: glow 2s ease-in-out infinite;
    }
    
    /* Confetti effect */
    .confetti {
        position: fixed;
        width: 10px;
        height: 10px;
        background: #ff69b4;
        animation: confetti-fall 3s linear forwards;
        z-index: 9999;
    }
    
    @keyframes confetti-fall {
        0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
        100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
    }
</style>

<script>
    // Function to create sparkles on click
    function createSparkle(event) {
        for(let i = 0; i < 10; i++) {
            let sparkle = document.createElement('div');
            sparkle.innerHTML = ['✨', '⭐', '💖', '🌸', '📚'][Math.floor(Math.random() * 5)];
            sparkle.className = 'sparkle';
            sparkle.style.left = event.clientX + 'px';
            sparkle.style.top = event.clientY + 'px';
            sparkle.style.position = 'fixed';
            document.body.appendChild(sparkle);
            setTimeout(() => sparkle.remove(), 1000);
        }
    }
    
    // Add click event listener to body
    document.addEventListener('click', createSparkle);
    
    // Create confetti
    function createConfetti() {
        for(let i = 0; i < 50; i++) {
            let confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * window.innerWidth + 'px';
            confetti.style.backgroundColor = ['#ff69b4', '#ff1493', '#ffc0cb', '#ffb6c1'][Math.random() * 4];
            confetti.style.width = Math.random() * 8 + 4 + 'px';
            confetti.style.height = Math.random() * 8 + 4 + 'px';
            confetti.style.animationDuration = Math.random() * 2 + 1 + 's';
            document.body.appendChild(confetti);
            setTimeout(() => confetti.remove(), 3000);
        }
    }
</script>
""", unsafe_allow_html=True)

# Initialize session state for interactions
if 'click_count' not in st.session_state:
    st.session_state.click_count = 0
if 'show_surprise' not in st.session_state:
    st.session_state.show_surprise = False
if 'message' not in st.session_state:
    st.session_state.message = ""
if 'selected_emoji' not in st.session_state:
    st.session_state.selected_emoji = "🌸"

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

# Convert PPT to HTML slides
def convert_ppt_to_html_slides(ppt_path):
    try:
        from pptx import Presentation
        
        prs = Presentation(ppt_path)
        slides_html = []
        
        for idx, slide in enumerate(prs.slides):
            html_content = f"""
            <div class="slide-in" style="
                width: 100%;
                min-height: 500px;
                background: white;
                border-radius: 15px;
                padding: 40px;
                font-family: 'Segoe UI', Arial, sans-serif;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            ">
                <h2 style="color: #c2185b; border-bottom: 2px solid #ff69b4; padding-bottom: 10px;">
                    📍 Slide {idx + 1}
                </h2>
                <div style="font-size: 20px; line-height: 1.6; margin-top: 20px;">
            """
            
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    if idx == 0 and shape == slide.shapes[0]:
                        html_content += f"<h1 style='color: #ff69b4; animation: glow 2s infinite;'>{shape.text}</h1>"
                    else:
                        html_content += f"<p>📌 {shape.text}</p>"
            
            html_content += """
                </div>
            </div>
            """
            slides_html.append(html_content)
        
        return slides_html
    except Exception as e:
        return None

# Display presentation with interactions
def display_presentation(course):
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    
    # Interactive back button with counter
    col_back, col_counter, col_empty = st.columns([1, 1, 4])
    with col_back:
        if st.button("◀ Back to Courses", use_container_width=False):
            st.session_state['viewing_course'] = None
            st.rerun()
    
    with col_counter:
        if st.button(f"🎯 Click me! ({st.session_state.click_count})", use_container_width=False):
            st.session_state.click_count += 1
            if st.session_state.click_count % 5 == 0:
                st.session_state.show_surprise = True
                st.session_state.message = random.choice([
                    "🎉 You're amazing! 🎉",
                    "⭐ Great job! ⭐",
                    "💖 Keep going! 💖",
                    "🌸 You're a star! 🌸",
                    "📚 Learning is fun! 📚"
                ])
                st.balloons()
            st.rerun()
    
    if st.session_state.show_surprise:
        st.success(f"✨ {st.session_state.message} ✨")
        time.sleep(2)
        st.session_state.show_surprise = False
    
    # Title with animated emoji
    st.markdown(f"""
        <div style="text-align: center;">
            <div>
                <span class="bouncing-emoji">📖</span>
                <span class="heartbeat">💖</span>
                <span class="bouncing-emoji">✨</span>
            </div>
            <h2 class="glow-text">{course['title']}</h2>
            <p style="color: #c2185b;">⭐ Level {course['level']} | {course['upload_date']} ⭐</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    slides_html = convert_ppt_to_html_slides(course["path"])
    
    if slides_html:
        if 'slide_index' not in st.session_state:
            st.session_state.slide_index = 0
        
        # Navigation with interactive buttons
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("◀◀ PREVIOUS", use_container_width=True):
                if st.session_state.slide_index > 0:
                    st.session_state.slide_index -= 1
                    st.rerun()
        
        with col2:
            st.markdown(f"<h3 style='text-align: center;'>📄 {st.session_state.slide_index + 1} / {len(slides_html)}</h3>", unsafe_allow_html=True)
        
        with col3:
            progress = (st.session_state.slide_index + 1) / len(slides_html)
            st.progress(progress)
        
        with col4:
            if st.button("NEXT ▶▶", use_container_width=True):
                if st.session_state.slide_index < len(slides_html) - 1:
                    st.session_state.slide_index += 1
                    st.rerun()
        
        with col5:
            st.markdown("""
                <button onclick="document.documentElement.requestFullscreen(); createConfetti();" style="
                    background: linear-gradient(45deg, #ff69b4, #ff1493);
                    color: white;
                    border: none;
                    border-radius: 25px;
                    padding: 10px 20px;
                    font-weight: bold;
                    cursor: pointer;
                    width: 100%;
                    transition: transform 0.3s;
                "
                onmouseover="this.style.transform='scale(1.05)'"
                onmouseout="this.style.transform='scale(1)'">
                    🖥️ FULLSCREEN 🎉
                </button>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown(slides_html[st.session_state.slide_index], unsafe_allow_html=True)
        
        # Interactive tip button
        if st.button("💡 Get a learning tip 💡"):
            tips = [
                "📝 Take notes while watching!",
                "💕 Practice with a friend after!",
                "⭐ Review vocabulary 3 times!",
                "🌸 Ask questions if confused!",
                "🎯 Set a small goal for each slide!",
                "📖 Repeat key phrases out loud!",
                "✨ Draw mind maps of what you learn!"
            ]
            st.info(f"💖 {random.choice(tips)}")
        
        with st.expander("📥 Download Original PowerPoint", expanded=False):
            with open(course["path"], "rb") as f:
                st.download_button(
                    label="📎 Download PPT File",
                    data=f,
                    file_name=course["filename"],
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )
    else:
        st.error("❌ Cannot display this PowerPoint.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main application
def main():
    if 'viewing_course' not in st.session_state:
        st.session_state.viewing_course = None
    
    # Animated header
    st.markdown("""
        <div style="text-align: center;">
            <div>
                <span class="bouncing-emoji">🌸</span>
                <span class="heartbeat">💖</span>
                <span class="bouncing-emoji">📚</span>
                <span class="heartbeat">✨</span>
                <span class="bouncing-emoji">🎓</span>
            </div>
            <h1 class="glow-text">✨ English Teacher's Platform ✨</h1>
            <p style="color: #c2185b; font-size: 18px;">💕 Make learning beautiful and fun! 💕</p>
            <div>
                <span class="bouncing-emoji">📖</span>
                <span class="bouncing-emoji">📝</span>
                <span class="bouncing-emoji">🎓</span>
                <span class="bouncing-emoji">✏️</span>
                <span class="bouncing-emoji">📕</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Interactive mood selector
    st.markdown("---")
    col_mood1, col_mood2, col_mood3, col_mood4, col_mood5 = st.columns(5)
    
    moods = {"🌸": "Happy", "⭐": "Motivated", "💖": "Loving", "🎯": "Focused", "📚": "Learning"}
    mood_emojis = list(moods.keys())
    
    for i, (emoji, mood) in enumerate(moods.items()):
        with eval(f"col_mood{i+1}"):
            if st.button(f"{emoji} {mood}", key=f"mood_{emoji}"):
                st.session_state.selected_emoji = emoji
                st.success(f"✨ {mood} mood activated! ✨")
                st.balloons()
                time.sleep(1)
                st.rerun()
    
    # Sidebar with interactions
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align: center; padding: 20px 0;">
                <div style="font-size: 60px; animation: bounce 1s infinite;">👩‍🏫</div>
                <h3 style="color: #ff69b4;">✨ Welcome! ✨</h3>
                <p>Your mood: {st.session_state.selected_emoji}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Interactive role selector with emojis
        mode = st.radio(
            "📌 Choose your role:",
            ["👩‍🏫 Teacher", "👧 Student"],
            index=0
        )
        
        # Interactive quote generator
        if st.button("💬 Get inspired 💬"):
            quotes = [
                "✨ Teaching is a work of heart! ✨",
                "💖 Every student can learn! 💖",
                "🌸 Make mistakes, learn faster! 🌸",
                "⭐ You're doing amazing! ⭐",
                "📚 Knowledge is power! 📚"
            ]
            st.info(random.choice(quotes))
        
        st.markdown("---")
        
        # Interactive fun fact
        if st.button("🎲 Random fun fact 🎲"):
            facts = [
                "Did you know? 'E' is the most common letter in English!",
                "The longest English word has 189,819 letters!",
                "English has over 1 million words!",
                "The shortest sentence is 'Go!'",
                "Shakespeare invented over 1,700 words!"
            ]
            st.success(f"📖 {random.choice(facts)}")
        
        st.markdown("---")
        st.markdown('<div style="text-align: center;"><span class="heartbeat">🌸</span> Made with love <span class="heartbeat">🌸</span></div>', unsafe_allow_html=True)
    
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
            
            st.write("**📊 Courses per level:**")
            for level, count in sorted(levels_count.items()):
                st.progress(min(count/10, 1.0), text=f"Level {level}: {count} courses")
        
        # Interactive celebration button
        if st.button("🎉 Celebrate success 🎉"):
            st.balloons()
            st.snow()
            st.success("🎊 You're doing great! 🎊")
    
    st.markdown("---")
    st.subheader("📚 Manage Your Courses")
    
    if metadata:
        filter_level = st.selectbox("🔍 Filter by level:", ["All"] + sorted(set(c["level"] for c in metadata.values())))
        
        for key, course in metadata.items():
            if filter_level != "All" and course["level"] != filter_level:
                continue
                
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                        <div class="course-card" onclick="createSparkle(event)">
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
                                label="📎 Click to download",
                                data=f,
                                file_name=course["filename"],
                                key=f"down_btn_{key}",
                                hidden=True
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
    
    # Interactive level selector with visual feedback
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
                
                # Interactive learning buttons
                col_tip, col_review, col_practice = st.columns(3)
                with col_tip:
                    if st.button(f"💡 Get a tip", key=f"tip_{key}"):
                        tips = [
                            "✨ Take notes while watching!",
                            "💕 Practice with a friend!",
                            "⭐ Review key vocabulary after!",
                            "🌸 Ask questions if something is unclear!",
                            "📝 Write down new words!",
                            "🎯 Repeat after the presentation!"
                        ]
                        st.info(f"💖 Tip: {random.choice(tips)}")
                
                with col_review:
                    if st.button(f"⭐ Rate this course", key=f"rate_{key}"):
                        rating = random.randint(4, 5)
                        st.success(f"⭐ You gave this course {rating}/5 stars! ⭐")
                
                with col_practice:
                    if st.button(f"🎯 Practice mode", key=f"practice_{key}"):
                        st.info("🎧 Try to repeat what you learned out loud! 🎧")
    else:
        st.warning(f"💔 No courses available for Level {full_level} yet.")
        st.markdown("""
            <div style="text-align: center; padding: 40px;">
                <div>
                    <span class="bouncing-emoji">📚</span>
                    <span class="heartbeat">✨</span>
                    <span class="bouncing-emoji">💕</span>
                </div>
                <p style="color: #c2185b;">🌸 Ask your teacher to upload courses for this level! 🌸</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    init_folders()
    main()
