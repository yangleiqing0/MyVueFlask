# coding=utf-8
import json
from datetime import datetime
from flask.views import MethodView
from flask import render_template, Blueprint, redirect, url_for, session, request, current_app, jsonify
from common import get_values, send_excel, send_mail, all_to_dict
from views.testcase_report import get_report, add_message
from views.testcase_request import post_testcase
from modles import Job, Mail, TestCases, TestCaseScene, TestCaseStartTimes, db
from views import post_edit, get_list, post_del


job_blueprint = Blueprint('job_blueprint', __name__)


class JobAdd(MethodView):

    def post(self):
        user_id =session.get('user_id')
        testcases, testcase_scenes, description = get_values('testcases', 'testcase_scenes', 'description')
        print('JobAdd: ', testcases, testcase_scenes)
        job = Job(testcases, testcase_scenes, description, user_id)
        db.session.add(job)
        db.session.commit()
        # app.logger.info('message:insert into SchedulerJobs success, name: %s' % name)
        return json.dumps({"job_id": str(job.id)})


class JobUpdate(MethodView):

    def post(self):
        is_start = 0
        page, _id, name, description, triggers, cron, is_start, mail_id, testcases, testcase_scenes = get_values(
            'page', 'id', 'name', 'description', 'triggers', 'cron', 'is_start', 'mail_id', 'testcases',
            'testcase_scenes')
        if is_start:
            is_start = 1
        # testcases = request.form.getlist('testcase')
        # testcase_scenes = request.form.getlist('testcase_scene')
        print('JobUpdate post:', testcases, testcase_scenes, type(testcases), is_start)
        if len(testcases) > 1:
            if not testcases[-1]:
                testcases.pop()
            testcases = ','.join(map(lambda x: str(x), testcases))+','
        else:
            testcases = ''
        if len(testcase_scenes) > 1:
            if not testcase_scenes[-1]:
                testcase_scenes.pop()
            testcase_scenes = ','.join(map(lambda x: str(x), testcase_scenes))+','
        else:
            testcase_scenes = ''
        job = Job.query.get(_id)
        old_cron = job.cron
        job.name = name
        job.testcases = testcases
        job.testcase_scenes = testcase_scenes
        job.description = description
        job.triggers = triggers
        job.cron = cron
        job.is_start = is_start
        job.mail_id = mail_id
        db.session.commit()
        print('old_cron cron:', old_cron, cron)
        if old_cron == cron:
            scheduler_job(job)
        else:
            scheduler_job(job, cron_change=1)

        return jsonify(msg='编辑任务成功')


class JobDelete(MethodView):

    def post(self):
        return post_del(Job, '任务')


class JobSchedulerUpdate(MethodView):

    def get(self):
        job_id, is_start = get_values('job_id', 'is_start')
        job = Job.query.get(job_id)
        job.is_start = is_start
        db.session.commit()
        scheduler_job(job)
        return 'OK'


class JobList(MethodView):

    def post(self):
        search, user_id, page, pagesize, _all, _id = get_values('search', 'user_id', 'page', 'pagesize', 'all', 'id')
        print('search', search, user_id, page, pagesize, _id)
        if _id:
            data = Job.query.get(_id).to_dict()
            return jsonify({'list': data})
        if not isinstance(page, int) or page <= 0:
            page = 1
        if user_id:
            if _all:
                _list = Job.query.filter(Job.user_id == user_id). \
                    order_by(Job.timestamp.desc(), Job.id.desc()).all()
                count = len(_list)
            else:
                _list = Job.query.filter(Job.user_id == user_id). \
                    order_by(Job.timestamp.desc(), Job.id.desc()).limit(pagesize).offset(
                    pagesize * (page - 1)).all()
                count = Job.query.filter(Job.user_id == user_id). \
                    order_by(Job.timestamp.desc(), Job.id.desc()).count()
            all_to_dict(_list, model=Job)
        else:
            _list, count = [{}], 0
        return jsonify({'list': _list, 'count': count})


class JobRun(MethodView):

    def get(self):
        mail = None
        job_id = get_values('id')
        job = Job.query.get(job_id)
        if job.mail_id:
            mail = Mail.query.get(job.mail_id)
        auto_send_mail(job, mail, is_async=False)
        return jsonify('邮件已开始发送')


class JobUpdateValidate(MethodView):

    def post(self):
        user_id = session.get('user_id')
        name, job_id = get_values('name', 'job_id')
        print('TestCaseSceneUpdateValidate:', name, job_id)
        job = Job.query.filter(
            Job.id != job_id, Job.name == name, Job.user_id == user_id).count()
        if job != 0:
            return jsonify(False)
        else:
            return jsonify(True)


job_blueprint.add_url_rule('/job_add/', view_func=JobAdd.as_view('job_add'))
job_blueprint.add_url_rule('/job_edit', view_func=JobUpdate.as_view('job_edit'))
job_blueprint.add_url_rule('/job_list', view_func=JobList.as_view('job_list'))
job_blueprint.add_url_rule('/job_del', view_func=JobDelete.as_view('job_del'))
job_blueprint.add_url_rule('/job_run/', view_func=JobRun.as_view('job_run'))

job_blueprint.add_url_rule('/job_scheduler_update/', view_func=JobSchedulerUpdate.as_view('job_scheduler_update'))

job_blueprint.add_url_rule('/job_validate', view_func=JobUpdateValidate.as_view('job_validate'))


def scheduler_job(job, scheduler=None, cron_change=None):
    if not scheduler:
        from app import scheduler
    scheduler_job_id = 'job_' + str(job.id)
    print('scheduler_job:', job.id, job.is_start, job.mail_id, scheduler.get_jobs())
    mail = None
    if scheduler.get_job(scheduler_job_id) and not cron_change and job.is_start==1:
        print('此任务已在执行')
        return

    if job.cron and job.triggers:
        if job.mail_id:
            mail = Mail.query.get(job.mail_id)
        else:
            print('此任务没有配置邮件接收人')
        if job.is_start == 1:
            cron = job.cron.split(' ')
            print(cron)
            if len(cron) !=6:
                print('cron表达式不正确', job.name)
                return
            if cron_change:
                print('定时任务规则改变')

                try:
                    scheduler.remove_job(scheduler_job_id)
                except Exception as e:
                    print(e, '无此任务', job.name)
            scheduler.add_job(id=scheduler_job_id, func=auto_send_mail,
                                  trigger=job.triggers, year=cron[5], month=cron[4],
                              day=cron[3], hour=cron[2], minute=cron[1],
                                  second=cron[0], args=(job, mail))
            print('get_jobs:', scheduler.get_jobs(), scheduler.get_job(scheduler_job_id))

            print(scheduler.get_job('scheduler_job_id'))

        elif job.is_start == 0:
            print('get_jobs is:', scheduler.get_jobs())
            try:
                scheduler.remove_job(scheduler_job_id)
            except Exception as e:
                print(e, '无此任务', job.name)
                return
            print('get_jobs is_after:', scheduler.get_jobs())
        print('现在有的任务：', scheduler.get_jobs())

    else:
        print('未输入cron表达式或trigger')
        return


def print_job_name(job):
    print(job.name)


def auto_send_mail(job, mail, is_async=True):
    user_id = job.user_id
    testcases_ids = testcase_scenes_ids = []
    if job.testcases:
        testcases_ids = eval(job.testcases)
    if job.testcase_scenes:
        testcase_scenes_ids = eval(job.testcase_scenes)
    testcase_time_id = get_testcase_time_id(user_id, is_async)
    post_request(testcases_ids, testcase_scenes_ids, testcase_time_id)
    get_report(testcase_time_id)
    add_message(testcase_time_id)
    if mail:
        if mail.email_method == 1:
            send_mail(mail.subject, mail.to_user_list.split(','), user_id=user_id, testcase_time_id=testcase_time_id)
        elif mail.email_method == 2:
            send_excel(mail.subject, mail.to_user_list.split(','), testcase_time_id=testcase_time_id)
        else:
            print('auto_send_mail:错误的邮件发送方式')


def get_testcase_time_id(user_id, is_async=True):
    if is_async:
        from werkzeug.test import EnvironBuilder
        from app import return_app
        app = return_app()
        app.request_context(EnvironBuilder('/', 'http://localhost/').get_environ()).push()
        # 构建一个request上下文对象放入app

    session['user_id'] = user_id
    time_strftime = datetime.now().strftime('%Y%m%d%H%M%S')
    testcase_time = TestCaseStartTimes(time_strftime=time_strftime, user_id=user_id)
    db.session.add(testcase_time)
    db.session.commit()
    return testcase_time.id


def post_request(testcases_ids, testcase_scenes_ids, testcase_time_id):
    if testcases_ids:
        for testcase_id in testcases_ids:
            post_testcase(testcase_id, testcase_time_id)
    if testcase_scenes_ids:
        for testcase_scene_id in testcase_scenes_ids:
            testcase_scene = TestCaseScene.query.get(testcase_scene_id)
            for testcase_scene_testcase in testcase_scene.testcases:
                post_testcase(testcase_scene_testcase.id, testcase_time_id)


def init_scheduler():
    is_start_job = Job.query.filter(Job.is_start == 1).all()
    for job in is_start_job:
        scheduler_job(job)

