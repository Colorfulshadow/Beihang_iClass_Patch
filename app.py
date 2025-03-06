"""
Main Flask application for BUAA iClass Attendance System.
Handles web interface and API calls.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import logging
import os
from datetime import timedelta

# Import utility modules
from utils.auth import SSOAuth
from utils.courses import CourseManager
import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key
app.permanent_session_lifetime = timedelta(hours=2)  # Session timeout

@app.route('/')
def index():
    """Main page - shows login form or course list with QR codes."""
    if 'logged_in' not in session or not session['logged_in']:
        return render_template('index.html', logged_in=False)

    # If user is logged in, show courses
    return render_template(
        'index.html',
        logged_in=True,
        user_info=session.get('user_info', {}),
        today_courses=session.get('today_courses', [])
    )

@app.route('/login', methods=['POST'])
def login():
    """Handle login form submission."""
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return render_template('index.html', logged_in=False, error="请输入用户名和密码")

    # Try to login
    auth = SSOAuth(username, password)
    if auth.login():
        # Store session information
        session.permanent = True
        session['logged_in'] = True
        session['username'] = username
        session['user_id'] = auth.user_info.get('id')
        session['session_id'] = auth.session_id
        session['user_info'] = auth.user_info

        # Get today's courses
        course_manager = CourseManager(
            auth.session,
            user_id=auth.user_info.get('id'),
            session_id=auth.session_id
        )
        today_courses = course_manager.get_today_courses()
        session['today_courses'] = today_courses

        # Store the session object (convert to pickle or other serializable format in a real app)
        # This is a simplified example - in a real app, you'd need a better way to persist the session
        session['auth_session'] = {}
        session['auth_cookies'] = {k: v for k, v in auth.session.cookies.items()}

        return redirect(url_for('index'))
    else:
        return render_template('index.html', logged_in=False, error="登录失败，请检查用户名和密码")

@app.route('/refresh', methods=['POST'])
def refresh():
    """Refresh course information."""
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('index'))

    try:
        # Create a new session with the stored cookies
        auth = SSOAuth(session.get('username'))
        for cookie_name, cookie_value in session.get('auth_cookies', {}).items():
            auth.session.cookies.set(cookie_name, cookie_value)

        # Get today's courses
        course_manager = CourseManager(
            auth.session,
            user_id=session.get('user_id'),
            session_id=session.get('session_id')
        )
        today_courses = course_manager.get_today_courses()
        session['today_courses'] = today_courses

        # Update cookie information
        session['auth_cookies'] = {k: v for k, v in auth.session.cookies.items()}

        flash("课程信息已刷新", "success")
    except Exception as e:
        logger.error(f"Error refreshing courses: {str(e)}")
        flash(f"刷新失败: {str(e)}", "error")

    return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
def logout():
    """Handle logout."""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)