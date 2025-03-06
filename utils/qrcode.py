"""
QR code generation module for iClass attendance.
"""

import time
import config

def generate_qrcode_url(course_sched_id):
    """
    Generate the URL for the QR code with current timestamp.

    Args:
        course_sched_id: Course schedule ID for attendance

    Returns:
        str: URL for QR code generation
    """
    # Get current timestamp in milliseconds and multiply by 1000 to match the format in the HTML
    timestamp = int(time.time() * 1000) * 1000

    # Generate URL for QR code
    url = f"{config.ICLASS_QR_BASE}?courseSchedId={course_sched_id}&timestamp={timestamp}"

    return url