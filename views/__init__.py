import json
import os
import datetime
import re
import time
from .com import get_list, post_edit, post_del
from views.mysql import mysqlrun

from .user import user_blueprint
from .login import login_blueprint
from .case_group import case_group_blueprint
from .variables import variables_blueprint
from .request_headers import request_headers_blueprint
from .emai import mail_blueprint
from .mysql import mysql_blueprint
from .home import home_blueprint
from .testcase_report import testcase_report_blueprint
from .testcase import testcase_blueprint
from .scene import testcase_scene_blueprint
from .job import job_blueprint
from .testcase_request import test_case_request_blueprint

view_list = []
[view_list.append(eval(dr)) if '_blueprint' in dr else "" for dr in dir()]


