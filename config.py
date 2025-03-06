"""
Configuration file for the BUAA iClass Attendance System.
Fill in your SSO credentials and other configuration options.
"""

# SSO Credentials
USERNAME = ""  # Your BUAA SSO username
PASSWORD = ""  # Your BUAA SSO password

# URLs
SSO_LOGIN_URL = "https://sso.buaa.edu.cn/login"
ICLASS_SERVICE_URL = "https://iclass.buaa.edu.cn:8346/"
ICLASS_API_BASE = "https://iclass.buaa.edu.cn:8346/app"
ICLASS_QR_BASE = "http://iclass.buaa.edu.cn:8081/app/course/stu_scan_sign.action"

# QR Code Update Interval (in milliseconds)
QR_UPDATE_INTERVAL = 5000  # 5 seconds