# AI+安全实训 - 核心模块
# 本目录包含课程各天对应的功能模块，每位同学需在对应日期
# 阅读、分析、利用并修复其中的安全漏洞。

from .auth import verify_login, get_user_info, USERS_DB
from .database import get_db_connection, query_users, add_user, search_users
from .file_handler import handle_file_upload, get_upload_path
from .user_service import get_user_profile, update_user_profile, process_recharge
from .page_loader import load_page
from .password_manager import change_password
from .url_fetcher import fetch_url
from .command_runner import run_ping
from .xml_processor import parse_xml_data
