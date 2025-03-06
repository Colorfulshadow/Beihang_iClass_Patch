"""
Course retrieval module for BUAA iClass system.
Handles retrieving course information and attendance details.
"""

import requests
import logging
from datetime import datetime, timedelta
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
        self.all_course_schedules = []

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

    def get_all_course_schedules(self, days_range=30):
        """
        Get all course schedules within a specified date range.
        Retrieves past and future course schedules for attendance.

        Args:
            days_range: Number of days to look back and forward (default: 30)

        Returns:
            list: List of course schedules with attendance details
        """
        if not self.courses:
            self.get_all_courses()

        # Calculate date range
        today = datetime.now()
        start_date = today - timedelta(days=days_range)
        end_date = today + timedelta(days=days_range)

        logger.info(f"Getting course schedules from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        all_schedules = []

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

                        # Process all records
                        for record in attendance_records:
                            try:
                                record_date = record.get("teachTime", "")

                                # Skip if date is missing
                                if not record_date:
                                    continue

                                # Parse the date
                                try:
                                    record_date_obj = datetime.strptime(record_date, "%Y%m%d")
                                except ValueError:
                                    logger.error(f"Invalid date format: {record_date}")
                                    continue

                                # Check if the class is within the date range
                                if start_date <= record_date_obj <= end_date:
                                    # Add attendance details to the course
                                    course_with_attendance = course.copy()
                                    course_with_attendance["schedId"] = record.get("courseSchedId")
                                    course_with_attendance["beginTime"] = record.get("classBeginTime")
                                    course_with_attendance["endTime"] = record.get("classEndTime")
                                    course_with_attendance["signStatus"] = record.get("signStatus")
                                    course_with_attendance["teachDate"] = record_date
                                    course_with_attendance["formattedDate"] = record_date_obj.strftime("%Y-%m-%d")

                                    # Add a flag for today
                                    is_today = record_date == today.strftime("%Y%m%d")
                                    course_with_attendance["isToday"] = is_today

                                    # Add a flag for past dates
                                    is_past = record_date_obj < today
                                    course_with_attendance["isPast"] = is_past

                                    all_schedules.append(course_with_attendance)
                                    logger.info(f"Found course schedule for {course.get('course_name')} on {record_date_obj.strftime('%Y-%m-%d')}")
                            except Exception as e:
                                logger.error(f"Error processing record for course {course.get('course_name')}: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing course {course.get('course_name')}: {str(e)}")

        # Sort schedules by date
        all_schedules.sort(key=lambda x: x.get("teachDate", ""))

        self.all_course_schedules = all_schedules
        logger.info(f"Found {len(all_schedules)} course schedules within the date range")
        return all_schedules