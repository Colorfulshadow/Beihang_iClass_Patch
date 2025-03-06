"""
Command-line interface for BUAA iClass Attendance System.
This script can be used without the web interface.
"""

import argparse
import logging
import os
import time
import json
import qrcode
from datetime import datetime, timedelta
from PIL import Image

# Import utility modules
from utils.auth import SSOAuth
from utils.courses import CourseManager
from utils.qrcode import generate_qrcode_url
import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('cli')

def save_qrcode(url, filepath):
    """Generate and save QR code image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)
    return filepath

def login():
    """Log in to BUAA SSO system."""
    username = config.USERNAME
    password = config.PASSWORD

    # If not configured, ask for credentials
    if not username:
        username = input("Enter your BUAA username: ")
    if not password:
        import getpass
        password = getpass.getpass("Enter your BUAA password: ")

    auth = SSOAuth(username, password)
    if auth.login():
        logger.info(f"Logged in as {auth.user_info.get('realName')} ({auth.user_info.get('userName')})")
        return auth
    else:
        logger.error("Login failed")
        return None

def get_today_courses(auth):
    """Get courses for today."""
    course_manager = CourseManager(
        auth.session,
        user_id=auth.user_info.get('id'),
        session_id=auth.session_id
    )
    today_courses = course_manager.get_today_courses()
    return today_courses

def get_all_course_schedules(auth, days_range=30):
    """Get all course schedules within a date range."""
    course_manager = CourseManager(
        auth.session,
        user_id=auth.user_info.get('id'),
        session_id=auth.session_id
    )
    all_schedules = course_manager.get_all_course_schedules(days_range)
    return all_schedules

def save_course_info(courses, filepath):
    """Save course information to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    logger.info(f"Course information saved to {filepath}")

def generate_qrcodes_for_courses(courses, output_dir, update_interval=10):
    """Generate QR codes for all courses."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logger.info(f"Generating QR codes in {output_dir}, updating every {update_interval} seconds")

    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Updating QR codes at {current_time}")

        for course in courses:
            course_sched_id = course.get('schedId')
            if not course_sched_id:
                continue

            course_name = course.get('course_name', 'unknown')
            safe_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '_')).rstrip()

            # Add date information to the filename if available
            if 'formattedDate' in course:
                date_str = course.get('formattedDate')
                filename = f"{date_str}_{safe_name}_{course_sched_id}.png"
            else:
                # Fallback to the old naming scheme
                filename = f"{safe_name}_{course_sched_id}.png"

            filepath = os.path.join(output_dir, filename)

            # Generate QR code URL with current timestamp
            url = generate_qrcode_url(course_sched_id)

            # Save QR code
            save_qrcode(url, filepath)
            logger.info(f"Updated QR code for {course_name} ({filename})")

        # Wait for next update
        time.sleep(update_interval)

def list_courses(courses):
    """List courses in a formatted way."""
    if not courses:
        logger.info("No courses found")
        return

    logger.info(f"Found {len(courses)} courses")

    # Group courses by date if the date information is available
    if 'formattedDate' in courses[0]:
        # Sort courses by date
        courses.sort(key=lambda x: x.get('formattedDate', ''))

        # Group by date
        courses_by_date = {}
        for course in courses:
            date = course.get('formattedDate')
            if date not in courses_by_date:
                courses_by_date[date] = []
            courses_by_date[date].append(course)

        # Display courses grouped by date
        for date, date_courses in courses_by_date.items():
            logger.info(f"\n=== {date} ===")
            for i, course in enumerate(date_courses):
                status = "Signed" if course.get('signStatus') == '1' else "Not signed"
                logger.info(f"{i+1}. {course.get('course_name')} ({status}) at {course.get('beginTime')} in {course.get('course_address', 'Unknown location')}")
    else:
        # Display courses without grouping
        for i, course in enumerate(courses):
            status = "Signed" if course.get('signStatus') == '1' else "Not signed"
            logger.info(f"{i+1}. {course.get('course_name')} ({status}) at {course.get('beginTime')} in {course.get('course_address', 'Unknown location')}")

def main():
    """Main function for CLI."""
    parser = argparse.ArgumentParser(description='BUAA iClass Attendance CLI')
    parser.add_argument('-o', '--output-dir', default='qrcodes', help='Directory to save QR codes')
    parser.add_argument('-i', '--interval', type=int, default=10, help='QR code update interval in seconds')
    parser.add_argument('-s', '--save-info', action='store_true', help='Save course information to a JSON file')
    parser.add_argument('-a', '--all-schedules', action='store_true', help='Get all course schedules, not just today')
    parser.add_argument('-d', '--days', type=int, default=30, help='Number of days to look back and forward when using --all-schedules')
    parser.add_argument('-f', '--filter-date', help='Filter courses by date (format: YYYY-MM-DD), works with --all-schedules')
    args = parser.parse_args()

    # Login
    auth = login()
    if not auth:
        return

    # Get courses based on command line options
    if args.all_schedules:
        courses = get_all_course_schedules(auth, args.days)

        # Filter by date if specified
        if args.filter_date:
            filtered_courses = [c for c in courses if c.get('formattedDate') == args.filter_date]
            logger.info(f"Filtered to {len(filtered_courses)} courses on {args.filter_date}")
            courses = filtered_courses
    else:
        courses = get_today_courses(auth)

    if not courses:
        logger.info("No courses found")
        return

    # List courses
    list_courses(courses)

    # Save course information if requested
    if args.save_info:
        filename = 'all_courses.json' if args.all_schedules else 'today_courses.json'
        save_course_info(courses, filename)

    # Generate QR codes
    try:
        generate_qrcodes_for_courses(courses, args.output_dir, args.interval)
    except KeyboardInterrupt:
        logger.info("QR code generation stopped")

if __name__ == '__main__':
    main()