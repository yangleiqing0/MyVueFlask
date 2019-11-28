# !/usr/bin/env python3
# encoding: utf-8
import json
from flask.views import MethodView
from flask import render_template, Blueprint, request, redirect, url_for, session, jsonify
from common import db, get_values
# from common.pre_db_insert_data import to_insert_data
from app import return_app
# from views.testcase_report import report_delete
# from modles import TestCaseStartTimes, Variables, User
# from common import clear_download_xlsx

home_blueprint = Blueprint('home_blueprint', __name__)


class Home(MethodView):

    def get(self):
        return jsonify(True)


app = return_app()


@app.before_request  # 在请求达到视图前执行
def login_required():
    # print('username: ', session.get('username'), request.path, type(session.get('username')))
    if request.path in ('/logout', '/login', '/report_email', '/case_upload'):
        return

    if not session.get('user_id') and get_values('user_id'):
        # 处理gunicorn多个导致登陆后页面有user_id,但是server没有user_id
        session['user_id'] = get_values('user_id')
    print('before', session.get('user_id'), request.path)
    s_uid = session.get('user_id')

    if not s_uid:
        return jsonify(out='请重新登录')
    if request.method == 'POST':
        user_id = get_values('user_id')
        print('post', s_uid, user_id)
        if user_id:
            if isinstance(user_id, int):
                user_id = int(user_id)
                print('uid:', user_id, type(user_id))
                if s_uid != user_id:
                    print('重新登录')
                    session['user_id'] = None
                    return jsonify(out='请重新登录')
            elif user_id.isdigit():
                if int(user_id) != s_uid:
                    session['user_id'] = None
                    return jsonify(out='请重新登录')
            else:
                session['user_id'] = None
                return jsonify(out='请重新登录')
    elif request.method == 'GET':
        user_id = get_values('user_id', post=False)
        print('uid get:', user_id, session.get('user_id'), type(user_id), type(session.get('user_id')))
        if user_id:
            if user_id.isdigit():
                if int(user_id) != s_uid:
                    session['user_id'] = None
                    return jsonify(out='请重新登录')
            else:
                session['user_id'] = None
                return jsonify(out='请重新登录')


# class ClearData(MethodView):
#
#     def get(self):
#         clear_report(is_job=False)
#         return 'OK'


home_blueprint.add_url_rule('/', view_func=Home.as_view('home'))
# home_blueprint.add_url_rule('/clear_data/', view_func=ClearData.as_view('clear_data'))




# @app.errorhandler(404)
# # 当发生404错误时，会被该路由匹配
# def handle_404_error(err_msg):
#     """自定义的异常处理函数"""
#     # 这个函数的返回值就是前端用户看到的最终结果 (404错误页面)
#     return render_template('exception/404.html', err_msg=err_msg, mes=404)


# @app.errorhandler(500)
# def handle_500_error(err_msg):
#     return render_template('exception/404.html', err_msg=err_msg, mes=500)


# @app.errorhandler(AttributeError)
# def zero_division_error(e):
#     print('error:', e)
#     return render_template('exception/404.html', err_msg=e, mes=500)


@app.before_first_request  # 在第一个次请求前执行创建数据库和预插入数据的操作
def db_create_pre_all():
    session['user_id'] = ''
    session['username'] = ''
    session['app_rootpath'] = app.root_path
    import modles
    # db.create_all()
#
#     from views.job import init_scheduler
#     from common.pre_db_insert_data import to_insert_data
#     to_insert_data()
#     for user in User.query.all():
#         to_insert_data(user.id)


# @app.before_first_request
# def init_scheduler_job():
#     # 5分钟检查一次需要删除的测试用例xlsx
#     from modles.job import Job
#     from views.job import scheduler_job
#     from app import scheduler
#     jobs = Job.query.filter(Job.is_start == 1).all()
#     print('jobs:', jobs)
#     for job in jobs:
#         scheduler_job(job, scheduler)
#     job_id = "__clear_download_xlsx"
#     scheduler.add_job(id='__clear_report', func=clear_report, trigger='cron', hour='*/12', minute='0', second='0')
#     scheduler.add_job(id=job_id, func=clear_download_xlsx, trigger='cron', minute='*/5', second='0')
#     scheduler.add_job(id="__clear_upload_xlsx", func=clear_download_xlsx, args=('upload',), trigger='cron',
#                       minute='*/5', second='0')
#     print('scheduler_job:', scheduler.get_job(job_id), scheduler.get_job('__clear_report'))



