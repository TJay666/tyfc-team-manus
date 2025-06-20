from flask import Flask, request, redirect, render_template_string
import os
import sys

# 添加項目根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

app = Flask(__name__)

# 登入頁面HTML模板 - 使用原始設計
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>獵鷹登入頁面</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
        }
        
        .gradient-background {
            background: linear-gradient(135deg, #43389F 0%, #211E53 100%);
        }
        
        .login-card-top {
            background-color: #2C2A5A;
        }
        
        .login-card-bottom {
            background-color: #E9E4F0;
        }
        
        .login-button {
            background-color: #2C2A5A;
        }
        
        .login-button:hover {
            background-color: #3a377a;
        }
        
        .input-field {
            background-color: #F7F7FC;
            border-color: #DCD9E8;
        }
        
        .logo-container {
            width: 288px;
            height: 288px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: center;
            background: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjg4IiBoZWlnaHQ9IjI4OCIgdmlld0JveD0iMCAwIDI4OCAyODgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxjaXJjbGUgY3g9IjE0NCIgY3k9IjE0NCIgcj0iMTQ0IiBmaWxsPSIjMkMyQTVBIi8+CjxjaXJjbGUgY3g9IjE0NCIgY3k9IjE0NCIgcj0iMTIwIiBmaWxsPSIjNDMzODlGIi8+Cjx0ZXh0IHg9IjE0NCIgeT0iODAiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIyNCIgZm9udC13ZWlnaHQ9ImJvbGQiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5UQU9ZVUFOIFVOSVZFUlNJVFk8L3RleHQ+CjxjaXJjbGUgY3g9IjE0NCIgY3k9IjE0NCIgcj0iNDAiIGZpbGw9IiM2NjdlZWEiLz4KPHN2ZyB4PSIxMjQiIHk9IjEyNCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiB2aWV3Qm94PSIwIDAgMjQgMjQiIGZpbGw9IndoaXRlIj4KICA8cGF0aCBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnptMCAxOGMtNC40MSAwLTgtMy41OS04LThzMy41OS04IDgtOCA4IDMuNTkgOCA4LTMuNTkgOC04IDh6Ii8+CiAgPHBhdGggZD0iTTEyIDZjLTMuMzEgMC02IDIuNjktNiA2czIuNjkgNiA2IDYgNi0yLjY5IDYtNi0yLjY5LTYtNi02em0wIDEwYy0yLjIxIDAtNC0xLjc5LTQtNHMxLjc5LTQgNC00IDQgMS43OSA0IDQtMS43OSA0LTQgNHoiLz4KPC9zdmc+Cjx0ZXh0IHg9IjE0NCIgeT0iMjIwIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTgiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+Rk9PVEJBTEwgQ0xVQjwvdGV4dD4KPHN2ZyB4PSI2MCIgeT0iNjAiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+CiAgPHBvbHlnb24gcG9pbnRzPSIxMiwyIDIyLDggMTgsMjIgNiwyMiAyLDgiLz4KPC9zdmc+CjxzdmcgeD0iMjA4IiB5PSI2MCIgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIiB2aWV3Qm94PSIwIDAgMjQgMjQiIGZpbGw9IndoaXRlIj4KICA8cG9seWdvbiBwb2ludHM9IjEyLDIgMjIsOCAxOCwyMiA2LDIyIDIsOCIvPgo8L3N2Zz4KPHN2ZyB4PSI2MCIgeT0iMjA4IiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPgogIDxwb2x5Z29uIHBvaW50cz0iMTIsMiAyMiw4IDE4LDIyIDYsMjIgMiw4Ii8+Cjwvc3ZnPgo8c3ZnIHg9IjIwOCIgeT0iMjA4IiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPgogIDxwb2x5Z29uIHBvaW50cz0iMTIsMiAyMiw4IDE4LDIyIDYsMjIgMiw4Ii8+Cjwvc3ZnPgo8L3N2Zz4=') center/contain no-repeat;
        }
    </style>
</head>
<body class="gradient-background" style="display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 16px;">

    <div style="width: 100%; max-width: 448px; background: white; border-radius: 12px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); overflow: hidden;">
        <div class="login-card-top" style="padding: 40px; text-align: center;">
            <div style="margin-bottom: 24px;">
                <div class="logo-container"></div>
                <p style="font-size: 18px; color: rgba(255, 255, 255, 0.8); margin-top: 16px; font-weight: bold;">TFFA</p>
            </div>

            <h1 style="font-size: 32px; font-weight: bold; color: white; margin-bottom: 8px;">獵鷹 登入</h1>
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 16px;">歡迎回來！請輸入您的帳號密碼。</p>
        </div>

        <div class="login-card-bottom" style="padding: 40px;">
            <form action="/login" method="POST">
                <div style="margin-bottom: 24px;">
                    <label for="username" style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 4px;">使用者名稱</label>
                    <input type="text" name="username" id="username" required
                           class="input-field" style="appearance: none; display: block; width: 100%; padding: 12px 16px; border: 1px solid #DCD9E8; border-radius: 8px; background-color: #F7F7FC; color: #374151; font-size: 16px; transition: all 0.15s;" 
                           placeholder="請輸入您的帳號">
                </div>

                <div style="margin-bottom: 32px;">
                    <label for="password" style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 4px;">密碼</label>
                    <input type="password" name="password" id="password" required
                           class="input-field" style="appearance: none; display: block; width: 100%; padding: 12px 16px; border: 1px solid #DCD9E8; border-radius: 8px; background-color: #F7F7FC; color: #374151; font-size: 16px; transition: all 0.15s;" 
                           placeholder="請輸入您的密碼">
                </div>

                <div>
                    <button type="submit" 
                            class="login-button" style="width: 100%; display: flex; justify-content: center; padding: 12px 16px; border: none; border-radius: 8px; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); font-size: 16px; font-weight: 500; color: white; cursor: pointer; transition: all 0.15s;">
                        登入
                    </button>
                </div>
            </form>

            <p style="margin-top: 32px; text-align: center; font-size: 14px; color: #6B7280;">
                還沒有帳號嗎？
                <a href="/register" style="font-weight: 500; color: #7C3AED; text-decoration: none; transition: all 0.15s;">
                    點此註冊
                </a>
            </p>
        </div>
    </div>

</body>
</html>
'''

# 儀表板頁面HTML模板
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>儀表板 - 桃園獵鷹宇宙</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f8fafc;
            color: #1f2937;
        }
        
        .navbar {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
        }
        
        .navbar-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .logo {
            display: flex;
            align-items: center;
            color: white;
            font-size: 20px;
            font-weight: bold;
        }
        
        .logo-icon {
            width: 40px;
            height: 40px;
            background: #667eea;
            border-radius: 50%;
            margin-right: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
            list-style: none;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 6px;
            transition: background-color 0.2s;
        }
        
        .nav-links a:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        
        .user-info {
            color: white;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .main-content {
            margin-top: 80px;
            padding: 2rem;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .welcome-banner {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .stat-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            margin: 0 auto 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: white;
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        .management-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }
        
        .management-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .management-card h3 {
            color: #1f2937;
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }
        
        .management-links {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .management-links a {
            color: #667eea;
            text-decoration: none;
            padding: 8px 12px;
            border-radius: 6px;
            transition: background-color 0.2s;
        }
        
        .management-links a:hover {
            background-color: #f3f4f6;
        }
        
        .footer {
            background-color: #2c3e50;
            color: white;
            text-align: center;
            padding: 1.5rem;
            margin-top: 3rem;
        }
        
        @media (max-width: 768px) {
            .navbar {
                padding: 1rem;
            }
            
            .nav-links {
                display: none;
            }
            
            .main-content {
                padding: 1rem;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .management-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <div class="logo">
                <div class="logo-icon">⚽</div>
                桃園獵鷹
            </div>
            <ul class="nav-links">
                <li><a href="/dashboard">儀表板</a></li>
                <li><a href="/teams">球隊管理</a></li>
                <li><a href="/players">球員管理</a></li>
                <li><a href="/matches">比賽管理</a></li>
                <li><a href="/users">使用者管理</a></li>
                <li><a href="/statistics">統計數據</a></li>
            </ul>
            <div class="user-info">
                <span>歡迎，{{ username }}！</span>
                <a href="/logout" style="color: #fbbf24;">登出</a>
            </div>
        </div>
    </nav>

    <main class="main-content">
        <div class="welcome-banner">
            <h1>歡迎回來，{{ username }}！</h1>
            <p>桃園獵鷹足球管理系統</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-number">15</div>
                <div class="stat-label">總使用者數</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-number">15</div>
                <div class="stat-label">已審核使用者</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚽</div>
                <div class="stat-number">2</div>
                <div class="stat-label">球隊數量</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📅</div>
                <div class="stat-number">0</div>
                <div class="stat-label">即將到來的比賽</div>
            </div>
        </div>

        <div class="management-grid">
            <div class="management-card">
                <h3>球隊管理</h3>
                <div class="management-links">
                    <a href="/teams">查看所有球隊</a>
                    <a href="/teams/create">新增球隊</a>
                    <a href="/teams/leagues">聯賽管理</a>
                </div>
            </div>
            
            <div class="management-card">
                <h3>球員管理</h3>
                <div class="management-links">
                    <a href="/players">查看所有球員</a>
                    <a href="/players/create">新增球員</a>
                    <a href="/players/statistics">球員統計</a>
                </div>
            </div>
            
            <div class="management-card">
                <h3>比賽管理</h3>
                <div class="management-links">
                    <a href="/matches">查看所有比賽</a>
                    <a href="/matches/create">安排新比賽</a>
                    <a href="/matches/results">比賽結果</a>
                </div>
            </div>
            
            <div class="management-card">
                <h3>使用者管理</h3>
                <div class="management-links">
                    <a href="/users">查看所有使用者</a>
                    <a href="/users/pending">待審核使用者</a>
                    <a href="/users/roles">權限管理</a>
                </div>
            </div>
        </div>
    </main>

    <footer class="footer">
        <p>&copy; 桃園獵鷹 · 版權所有</p>
    </footer>
</body>
</html>
'''

# 註冊頁面HTML模板
REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>桃園獵鷹足球管理系統 - 註冊</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .register-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 500px;
            text-align: center;
        }
        
        .logo {
            width: 80px;
            height: 80px;
            background: #667eea;
            border-radius: 50%;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            color: white;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }
        
        input[type="text"], input[type="password"], input[type="email"], select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .register-btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            margin-bottom: 20px;
        }
        
        .register-btn:hover {
            transform: translateY(-2px);
        }
        
        .login-link {
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
        }
        
        .login-link:hover {
            text-decoration: underline;
        }
        
        .info-box {
            margin-top: 20px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 10px;
            border-left: 4px solid #ffc107;
            text-align: left;
        }
        
        .info-title {
            font-weight: bold;
            color: #856404;
            margin-bottom: 5px;
        }
        
        .info-text {
            font-size: 14px;
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="register-container">
        <div class="logo">⚽</div>
        <h1>加入桃園獵鷹</h1>
        <p class="subtitle">註冊新帳號</p>
        
        <form method="POST" action="/register">
            <div class="form-group">
                <label for="username">使用者名稱</label>
                <input type="text" id="username" name="username" placeholder="請輸入使用者名稱" required>
            </div>
            
            <div class="form-group">
                <label for="email">電子郵件</label>
                <input type="email" id="email" name="email" placeholder="請輸入電子郵件" required>
            </div>
            
            <div class="form-group">
                <label for="nickname">暱稱</label>
                <input type="text" id="nickname" name="nickname" placeholder="請輸入暱稱" required>
            </div>
            
            <div class="form-group">
                <label for="user_type">使用者類型</label>
                <select id="user_type" name="user_type" required>
                    <option value="">請選擇使用者類型</option>
                    <option value="player">球員</option>
                    <option value="coach">教練</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="password">密碼</label>
                <input type="password" id="password" name="password" placeholder="請輸入密碼" required>
            </div>
            
            <div class="form-group">
                <label for="confirm_password">確認密碼</label>
                <input type="password" id="confirm_password" name="confirm_password" placeholder="請再次輸入密碼" required>
            </div>
            
            <button type="submit" class="register-btn">註冊帳號</button>
        </form>
        
        <a href="/" class="login-link">已有帳號？返回登入</a>
        
        <div class="info-box">
            <div class="info-title">📝 註冊說明</div>
            <div class="info-text">
                • 球員：可查看自己的比賽和統計數據<br>
                • 教練：可管理球隊、安排比賽、查看統計<br>
                • 系統管理員權限需要聯繫管理員開通
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 模擬登入驗證
        if username and password:
            # 返回登入成功頁面，包含完整的管理系統功能
            return render_template_string(DASHBOARD_TEMPLATE, username=username)
        else:
            return render_template_string(LOGIN_TEMPLATE + '<script>alert("請輸入帳號密碼");</script>')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        if username and email and password and user_type:
            # 模擬註冊成功，重定向到登入頁面
            return redirect('/')
        else:
            return render_template_string(REGISTER_TEMPLATE + '<script>alert("請填寫所有欄位");</script>')
    
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'football_management_system', 'version': '2.0.0'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

