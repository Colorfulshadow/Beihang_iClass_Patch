"""
Main Flask application for BUAA iClass Attendance System.
Handles web interface and API calls.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
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

    # Default view is today's courses
    view_type = request.args.get('view', 'today')

    # If user is logged in, show courses
    return render_template(
        'index.html',
        logged_in=True,
        user_info=session.get('user_info', {}),
        today_courses=session.get('today_courses', []),
        all_course_schedules=session.get('all_course_schedules', []),
        view_type=view_type
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

        # Get course information
        course_manager = CourseManager(
            auth.session,
            user_id=auth.user_info.get('id'),
            session_id=auth.session_id
        )

        # Get today's courses
        today_courses = course_manager.get_today_courses()
        session['today_courses'] = today_courses

        # Get all course schedules (past and future)
        all_course_schedules = course_manager.get_all_course_schedules()
        session['all_course_schedules'] = all_course_schedules

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

        # Get course information
        course_manager = CourseManager(
            auth.session,
            user_id=session.get('user_id'),
            session_id=session.get('session_id')
        )

        # Get today's courses
        today_courses = course_manager.get_today_courses()
        session['today_courses'] = today_courses

        # Get all course schedules (past and future)
        all_course_schedules = course_manager.get_all_course_schedules()
        session['all_course_schedules'] = all_course_schedules

        # Update cookie information
        session['auth_cookies'] = {k: v for k, v in auth.session.cookies.items()}

        flash("课程信息已刷新", "success")
    except Exception as e:
        logger.error(f"Error refreshing courses: {str(e)}")
        flash(f"刷新失败: {str(e)}", "error")

    # Return to the same view
    view_type = request.form.get('view', 'today')
    return redirect(url_for('index', view=view_type))

@app.route('/logout', methods=['POST'])
def logout():
    """Handle logout."""
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/get-qrcode-url', methods=['GET'])
def get_qrcode_url():
    """API endpoint to get the QR code URL for a course schedule."""
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({"error": "Not logged in"}), 401

    course_sched_id = request.args.get('schedId')
    if not course_sched_id:
        return jsonify({"error": "No course schedule ID provided"}), 400

    # Import here to avoid circular imports
    from utils.qrcode import generate_qrcode_url

    try:
        url = generate_qrcode_url(course_sched_id)
        return jsonify({"url": url})
    except Exception as e:
        logger.error(f"Error generating QR code URL: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)