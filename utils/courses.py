"""
Course retrieval module for BUAA iClass system.
Handles retrieving course information and attendance details.
"""

import requests
import logging
from datetime import datetime
import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('courses')

class CourseManager:
    def __init__(self, session, user_id=None, session_id=None):
        """
        Initialize the course manager.

        Args:
            session: requests.Session object with authenticated session
            user_id: User ID from the system
            session_id: Session ID for API requests
        """
        self.session = session
        self.user_id = user_id
        self.session_id = session_id
        self.current_semester = None
        self.courses = []
        self.today_courses = []

    def get_current_semester(self):
        """
        Get the current semester code.

        Returns:
            str: Semester code
        """
        try:
            url = f"{config.ICLASS_API_BASE}/course/get_base_school_year.action"
            params = {
                "userId": self.user_id,
                "type": "2"
            }

            headers = {
                "sessionId": self.session_id
            }

            response = self.session.get(url, params=params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data.get("STATUS") == "0":
                    # Get the current semester (status="1")
                    semesters = data.get("result", [])
                    for semester in semesters:
                        if semester.get("yearStatus") == "1":
                            self.current_semester = semester.get("code")
                            logger.info(f"Current semester: {semester.get('name')} ({self.current_semester})")
                            return self.current_semester

                    # If no active semester found, use the first one
                    if semesters:
                        self.current_semester = semesters[0].get("code")
                        logger.info(f"Using first semester in list: {semesters[0].get('name')} ({self.current_semester})")
                        return self.current_semester

                    logger.error("No semesters found")
                    return None
                else:
                    logger.error(f"Failed to get semester info: {data}")
                    return None
            else:
                logger.error(f"Failed to get semester info: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting current semester: {str(e)}")
            return None

    def get_all_courses(self):
        """
        Get all courses for the current semester.

        Returns:
            list: List of course dictionaries
        """
        if not self.current_semester:
            self.get_current_semester()

        if not self.current_semester:
            logger.error("Could not determine current semester")
            return []

        try:
            url = f"{config.ICLASS_API_BASE}/choosecourse/get_myall_course.action"
            params = {
                "user_type": "1",
                "id": self.user_id,
                "xq_code": self.current_semester
            }

            headers = {
                "sessionId": self.session_id
            }

            response = self.session.get(url, params=params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data.get("STATUS") == "0":
                    self.courses = data.get("result", [])
                    logger.info(f"Got {len(self.courses)} courses for semester {self.current_semester}")
                    return self.courses
                else:
                    logger.error(f"Failed to get courses: {data}")
                    return []
            else:
                logger.error(f"Failed to get courses: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting courses: {str(e)}")
            return []

    def get_today_courses(self):
        """
        Filter courses to only those with classes today.
        Gets course schedule IDs for attendance.

        Returns:
            list: List of today's courses with attendance details
        """
        if not self.courses:
            self.get_all_courses()

        today = datetime.now().strftime("%Y%m%d")
        today_courses = []

        # For each course, get the attendance details
        for course in self.courses:
            try:
                course_id = course.get("course_id")
                if not course_id:
                    continue

                url = f"{config.ICLASS_API_BASE}/my/get_my_course_sign_detail.action"
                params = {
                    "id": self.user_id,
                    "courseId": course_id
                }

                response = self.session.post(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("STATUS") == "0":
                        attendance_records = data.get("result", [])

                        # Filter for today's classes
                        for record in attendance_records:
                            record_date = record.get("teachTime", "")

                            # Check if the class is for today
                            if record_date == today:
                                # Add attendance details to the course
                                course_with_attendance = course.copy()
                                course_with_attendance["schedId"] = record.get("courseSchedId")
                                course_with_attendance["beginTime"] = record.get("classBeginTime")
                                course_with_attendance["endTime"] = record.get("classEndTime")
                                course_with_attendance["signStatus"] = record.get("signStatus")

                                today_courses.append(course_with_attendance)
                                logger.info(f"Found today's class for {course.get('course_name')}")
            except Exception as e:
                logger.error(f"Error processing course {course.get('course_name')}: {str(e)}")

        self.today_courses = today_courses
        logger.info(f"Found {len(today_courses)} courses scheduled for today")
        return today_courses