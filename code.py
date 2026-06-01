<!DOCTYPE html>
<html>
<head>
    <title>English Teacher's Platform</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #ffe6f0 0%, #ffd9e8 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1 {
            text-align: center;
            color: #c2185b;
            margin: 20px 0;
        }
        
        .subtitle {
            text-align: center;
            color: #c2185b;
            margin-bottom: 30px;
        }
        
        .two-columns {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
        }
        
        .upload-form {
            background: white;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .upload-form h2 {
            color: #c2185b;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ffc0cb;
            border-radius: 10px;
            font-size: 14px;
        }
        
        button {
            background: linear-gradient(45deg, #ff69b4, #ff1493);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
        }
        
        button:hover {
            transform: scale(1.02);
        }
        
        .stats {
            background: white;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .stats h2 {
            color: #c2185b;
            margin-bottom: 20px;
        }
        
        .stat-number {
            font-size: 36px;
            font-weight: bold;
            color: #ff69b4;
            text-align: center;
        }
        
        .courses-list {
            margin-top: 40px;
        }
        
        .courses-list h2 {
            color: #c2185b;
            margin-bottom: 20px;
        }
        
        .course-card {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .course-info h3 {
            color: #333;
            margin-bottom: 5px;
        }
        
        .course-info p {
            color: #666;
            font-size: 14px;
        }
        
        .course-actions button {
            width: auto;
            padding: 8px 15px;
            margin-left: 10px;
        }
        
        .btn-view {
            background: linear-gradient(45deg, #ff69b4, #ff1493);
        }
        
        .btn-delete {
            background: linear-gradient(45deg, #ff6b6b, #c0392b);
        }
        
        .filter {
            margin-bottom: 20px;
        }
        
        .filter select {
            width: 200px;
        }
        
        @media (max-width: 768px) {
            .two-columns {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌸 English Teacher's Platform 🌸</h1>
        <p class="subtitle">✨ Make learning beautiful and fun! ✨</p>
        
        <div class="two-columns">
            <!-- Formulaire d'upload -->
            <div class="upload-form">
                <h2>📤 Upload New Course</h2>
                <form method="POST" action="/upload" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>📖 Course Title</label>
                        <input type="text" name="title" placeholder="e.g., Present Simple Tense" required>
                    </div>
                    
                    <div class="form-group">
                        <label>🎯 Level</label>
                        <select name="level">
                            <option>A1</option><option>A2</option><option>A3</option>
                            <option>B1</option><option>B2</option><option>B3</option>
                            <option>C1</option><option>C2</option><option>C3</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>📎 PowerPoint File</label>
                        <input type="file" name="file" accept=".ppt,.pptx" required>
                    </div>
                    
                    <button type="submit">💖 Save Course</button>
                </form>
            </div>
            
            <!-- Statistiques -->
            <div class="stats">
                <h2>📊 Quick Stats</h2>
                <div class="stat-number">{{ courses|length }}</div>
                <p style="text-align: center;">Total Courses</p>
            </div>
        </div>
        
        <!-- Liste des cours -->
        <div class="courses-list">
            <h2>📚 Your Courses</h2>
            <div class="filter">
                <select id="levelFilter" onchange="filterCourses()">
                    <option value="all">All Levels</option>
                    <option>A1</option><option>A2</option><option>A3</option>
                    <option>B1</option><option>B2</option><option>B3</option>
                    <option>C1</option><option>C2</option><option>C3</option>
                </select>
            </div>
            <div id="coursesContainer">
                {% for id, course in courses.items() %}
                <div class="course-card" data-level="{{ course.level }}">
                    <div class="course-info">
                        <h3>📘 {{ course.title }}</h3>
                        <p>🎯 Level {{ course.level }} | 📅 {{ course.date }}</p>
                    </div>
                    <div class="course-actions">
                        <a href="/view/{{ id }}"><button class="btn-view">🎬 View</button></a>
                        <a href="/delete/{{ id }}" onclick="return confirm('Delete this course?')"><button class="btn-delete">🗑️ Delete</button></a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <script>
        function filterCourses() {
            let filter = document.getElementById('levelFilter').value;
            let cards = document.querySelectorAll('.course-card');
            
            cards.forEach(card => {
                if (filter === 'all' || card.dataset.level === filter) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
