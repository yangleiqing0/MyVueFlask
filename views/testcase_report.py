from flask.views import MethodView
from sqlalchemy import or_
from flask import render_template, Blueprint, request, redirect, url_for, send_from_directory, session, jsonify, \
    Response
from common import get_values, db, cdb, AnalysisParams, send_excel, send_mail, test_report, os, re
from modles import TestCaseSceneResult, Variables, TestCaseStartTimes, TestCaseResult, TestCaseScene, TestCases, \
    TimeMessage, datetime
from . import get_list, post_del


testcase_report_blueprint = Blueprint('testcase_report_blueprint', __name__)


class EnvMessage:

    def __init__(self, testcase_results, testcase_time_id, testcase_time, testcase_scene_list):
        user_id = session.get('user_id')
        self.testcase_scene_list = testcase_scene_list
        self.test_name = Variables.query.filter(Variables.name == '_TEST_NAME',
                                                Variables.user_id == user_id).first().value
        self.zdbm_version = Variables.query.filter(Variables.name == '_TEST_VERSION',
                                                   Variables.user_id == user_id).first().value
        self.test_pl = Variables.query.filter(Variables.name == '_TEST_PL', Variables.user_id == user_id).first().value
        self.test_net = Variables.query.filter(Variables.name == '_TEST_NET',
                                               Variables.user_id == user_id).first().value
        self.title_name = Variables.query.filter(Variables.name == '_TITLE_NAME',
                                                 Variables.user_id == user_id).first().value
        self.fail_sum = self.count_success_testcase_scene(testcase_time_id) + self.count_testcase_fail(testcase_time_id)
        self.test_sum = len(testcase_results) + len(testcase_scene_list)
        self.test_success = self.test_sum - self.fail_sum
        self.time_strftime = testcase_time.time_strftime
        if self.test_success == 0:
            self.score = 0
        else:
            self.score = int(self.test_success * 100 / self.test_sum)
        print('EnvMessage:', self.fail_sum, self.test_sum )

    def count_success_testcase_scene(self, testcase_time_id):
        fail_count = 0
        for testcase_scene in self.testcase_scene_list:
            for testcase in testcase_scene.testcases:
                testcase_result = TestCaseResult.query.filter(
                    TestCaseResult.testcase_id==testcase.id, TestCaseResult.testcase_start_time_id==testcase_time_id).first()
                print('testcase.testcase_result: ', testcase_result)
                if testcase_result.result != "测试成功":
                    fail_count += 1
                    break
        return fail_count

    @staticmethod
    def count_testcase_fail(testcase_time_id):
        count = TestCaseResult.query.join(TestCases, TestCaseResult.testcase_id == TestCases.id).filter(
            TestCaseResult.testcase_start_time_id == testcase_time_id, TestCases.testcase_scene_id.is_(None),
            TestCaseResult.result != "测试成功").count()
        return count


class Test:

    def __init__(self, testcase_result):
        print('Test :', testcase_result)

        self.t_name, self.url, self.request_body, self.hope = AnalysisParams().\
            analysis_more_params(testcase_result[0], testcase_result[1], testcase_result[3], testcase_result[5])
        print('self.t_name: ', self.t_name)

        self.method, self.response_body, self.old_database_value, self.new_database_value, self.result, \
        self.old_sql_value_result, self.new_sql_value_result, self.test_result  \
            = testcase_result[2], testcase_result[4], testcase_result[6], testcase_result[7], testcase_result[11], \
        testcase_result[9], testcase_result[10], testcase_result[8]

        try:
            self.scene_id = testcase_result[12]
        except Exception:
            pass


class Testcaseresult:

    def __init__(self, testcase_time_id, result="testcases"):
        self.testcase_time = TestCaseStartTimes.query.get(testcase_time_id)
        print('testcase_time_id: ', testcase_time_id, self.testcase_time)

        if result == 'testcases':
            testcase_results_query_sql = 'select test_case_result.testcase_name,test_case_result.testcase_url,' \
                                         'test_case_result.testcase_method,test_case_result.testcase_data,' \
                                         'test_case_result.response_body,test_case_result.' \
                                         'testcase_hope_result,test_case_result.' \
                                         'old_sql_value,test_case_result.new_sql_value,test_case_result.' \
                                         'testcase_test_result,test_case_result.old_sql_value_result,test_case_result.new_sql_value_result' \
                                         ', test_case_result.result from testcases,test_case_result where testcases.id=' \
                                         'test_case_result.testcase_id and testcases.testcase_scene_id is Null and ' \
                                         'test_case_result.testcase_start_time_id=%s' \
                                         % testcase_time_id
            self.testcase_results = cdb().query_db(testcase_results_query_sql)
            print('self.testcase_results:', self.testcase_results)

        elif result == 'scene_testcases':
            testcase_results_query_sql = 'select test_case_result.testcase_name,test_case_result.testcase_url,' \
                                         'test_case_result.testcase_method,test_case_result.testcase_data,' \
                                         'test_case_result.response_body,test_case_result.testcase_hope_result,' \
                                         'test_case_result.old_sql_value,test_case_result.new_sql_value,' \
                                         'test_case_result.testcase_test_result,test_case_result.old_sql_value_result,' \
                                         'test_case_result.new_sql_value_result, test_case_result.result, ' \
                                         'testcases.testcase_scene_id' \
                                         ' from testcases, test_case_result ' \
                                         'where testcases.id=test_case_result.testcase_id and ' \
                                         'testcases.testcase_scene_id is not NULL and ' \
                                         'test_case_result.testcase_start_time_id=%s' \
                                         % testcase_time_id
            self.testcase_results = cdb().query_db(testcase_results_query_sql)

            print('self.testcase_results:', self.testcase_results)


class TestCaseReport(MethodView):

    def get(self, email=False, testcase_time_id=None):
        testcase_time_id = request.args.get('testcase_time_id', testcase_time_id)
        testcase_results = Testcaseresult(testcase_time_id).testcase_results
        items = []
        for testcase_result in testcase_results:
            print('testcase_result:', testcase_result)
            items.append(Test(testcase_result))
        allocation = TimeMessage.query.filter(TimeMessage.time_id == testcase_time_id).first()
        testcase_scene_list = TestCaseSceneResult.query.filter(TestCaseSceneResult.time_id == testcase_time_id).all()
        for testcase_scene in testcase_scene_list:
            testcase_scene.test_cases = TestCaseResult.query.filter(TestCaseResult.scene_id == testcase_scene.scene_id, TestCaseResult.testcase_start_time_id == testcase_time_id).all()

        if email:
            return items, allocation, testcase_scene_list
        return render_template("testcase_report/testcase_report.html", items=items, allocation=allocation,
                               testcase_scene_list=testcase_scene_list)

    def post(self):
        testcase_time_id = request.args.get('testcase_time_id')
        # 生成测试报告
        get_report(testcase_time_id)
        items, allocation, testcase_scene_list = add_message(testcase_time_id)

        # return items, Allocation
        return render_template("testcase_report/testcase_report.html", items=items, allocation=allocation,
                               testcase_scene_list=testcase_scene_list)


def add_message(testcase_time_id):
    testcase_scene_ids, testcase_scene_list, testcase_scene_testcases_after_list, testcase_results, testcase_time, items = get_testcase_scene_message(
        testcase_time_id)
    for testcase_scene_id in testcase_scene_ids:
        testcase_scene = TestCaseScene.query.get(testcase_scene_id)
        testcase_scene_list.append(testcase_scene)
        testcase_scene_testcases = []
        for testcase_scene_testcase in testcase_scene_testcases_after_list:
            if testcase_scene_testcase.scene_id == testcase_scene.id:
                testcase_scene_testcases.append(testcase_scene_testcase)
            testcase_scene.test_cases = testcase_scene_testcases
    allocation = EnvMessage(testcase_results, testcase_time_id, testcase_time, testcase_scene_list)
    print('allocation:', allocation.fail_sum)
    time_message = TimeMessage(allocation.test_name, allocation.zdbm_version, allocation.test_pl, allocation.test_net,
                               allocation.title_name, allocation.fail_sum, allocation.test_sum, allocation.test_success,
                               allocation.time_strftime, allocation.score, testcase_time_id)
    db.session.add(time_message)
    db.session.commit()
    return items, allocation, testcase_scene_list


def get_testcase_scene_message(testcase_time_id):
    testcase_results = Testcaseresult(testcase_time_id).testcase_results
    items = []
    for testcase_result in testcase_results:
        items.append(Test(testcase_result))
    testcase_time = TestCaseStartTimes.query.get(testcase_time_id)
    testcase_scene_results = Testcaseresult(testcase_time_id, result="scene_testcases").testcase_results
    testcase_scene_ids = []
    testcase_scene_testcases_after_list = []
    for testcase_scene_result in testcase_scene_results:
        testcase_scene_ids.append(testcase_scene_result[12])
        testcase_scene_testcases_after_list.append(Test(testcase_scene_result))
    testcase_scene_ids = set(testcase_scene_ids)
    testcase_scene_list = []
    return testcase_scene_ids, testcase_scene_list, testcase_scene_testcases_after_list, testcase_results, testcase_time, items


def get_env_message(testcase_time_id):
    testcase_scene_ids, testcase_scene_list, testcase_scene_testcases_after_list, testcase_results, testcase_time, items = get_testcase_scene_message(testcase_time_id)
    for testcase_scene_id in testcase_scene_ids:
        testcase_scene = TestCaseScene.query.get(testcase_scene_id)
        fail_count = 0
        for testcase in testcase_scene.testcases:
            testcase_result = TestCaseResult.query.filter(TestCaseResult.testcase_id==testcase.id,
                                                          TestCaseResult.testcase_start_time_id==testcase_time_id).first()
            if testcase_result.result != "测试成功":
                fail_count += 1
        if fail_count == 0:
            testcase_scene.result = "测试成功"
        else:
            testcase_scene.result = "测试失败"
        testcase_scene_list.append(testcase_scene)
        testcase_scene_testcases = []
        for testcase_scene_testcase in testcase_scene_testcases_after_list:
            if testcase_scene_testcase.scene_id == testcase_scene.id:
                testcase_scene_testcases.append(testcase_scene_testcase)
            testcase_scene.test_cases = testcase_scene_testcases
    allocation = EnvMessage(testcase_results, testcase_time_id, testcase_time, testcase_scene_list)
    return items, allocation, testcase_scene_list


def get_report(testcase_time_id):
    user_id = session.get('user_id')
    time_strftime = datetime.now().strftime('%Y%m%d%H%M%S')
    testcase_report_name = Variables.query.filter(Variables.name == "_TEST_REPORT_EXCEL_NAME", Variables.user_id == user_id).first().value + "_" + \
                           time_strftime + ".xlsx"
    REPORT_FILE_PATH = Variables.query.filter(Variables.name == "_REPORT_FILE_PATH").first().value
    Filename = REPORT_FILE_PATH + testcase_report_name
    test_case_start_time = TestCaseStartTimes().query.get(testcase_time_id)
    test_case_start_time.filename = Filename
    test_case_start_time.name = testcase_report_name
    db.session.commit()
    _, allocation, testcase_scene_list = get_env_message(testcase_time_id)
    test_report(testcase_time_id, allocation, testcase_scene_list)


class TestCaseReportList(MethodView):

    def get(self):
        return get_list(TestCaseStartTimes)


class TestCaseReportDelete(MethodView):

    def post(self):
        return post_del(TestCaseStartTimes, '测试报告')


def report_delete(testcase_time_id):
    try:

        testcase_report = TestCaseStartTimes.query.get(testcase_time_id)
        testcase_results = testcase_report.this_time_testcase_result
        testcase_scene_results = TestCaseSceneResult.query.filter(TestCaseSceneResult.time_id == testcase_time_id).all()
        env = TimeMessage.query.filter(TimeMessage.time_id == testcase_time_id).first()
        print('testcase_report: ', testcase_report, id)
        db.session.delete(testcase_report)
        try:
            db.session.delete(env)
        except Exception as e:
            pass
        db.session.commit()
        try:
            for testcase_scene_result in testcase_scene_results:
                db.session.delete(testcase_scene_result)
                db.session.commit()
        except Exception as e:
            print(e)
            pass
        try:
            for testcase_result in testcase_results:
                db.session.delete(testcase_result)
                db.session.commit()
            from config.app_config import project_path
            filename = os.path.join(project_path, testcase_report.filename)
            if testcase_report.filename:
                os.remove(filename)
        except FileNotFoundError:
            pass
    except AttributeError as e:
        print(e)


class TestCaseReportDownLoad(MethodView):

    def get(self):
        _id = get_values('id', post=False)
        download_path, name = TestCaseStartTimes.query.get(_id).filename.split('/')
        print('download_path:', download_path)
        dirpath = os.path.join(session.get('app_rootpath'), download_path)
        # 这里是下在目录，从工程的根目录写起，比如你要下载static/js里面的js文件，这里就要写“static/js”
        print('dirpath:', dirpath)
        return send_from_directory(dirpath, name, as_attachment=True)  # as_attachment=True 一定要写，不然会变成打开，而不是下载


class TestCaseReportSendMail(MethodView):

    def get(self):
        report_type = request.args.get('report_type')
        testcase_time_id = request.args.get('testcase_time_id')
        if report_type == 'phantomjs':
            print('到了phantomjs')
            items, allocation, testcase_scene_list = TestCaseReport().get(email=True, testcase_time_id=testcase_time_id)
            return render_template('testcase_report/testcase_report_email.html', items=items, allocation=allocation,
                                   testcase_scene_list=testcase_scene_list)
        return 'OK'

    def post(self):
        testcase_time_id, user_id, subject, to_user_list, email_method = get_values(
            'report_id', 'user_id', 'subject', 'to_user_list', 'email_method')
        to_user_list = to_user_list.split(',')
        print('TestCaseReportSendMail testcase_time_id:', testcase_time_id, subject, to_user_list, email_method)
        result = '正在进行邮件发送'
        if email_method == 1:
            result = send_mail(subject, to_user_list, user_id=user_id, testcase_time_id=testcase_time_id)
        elif email_method == 2:
            result = send_excel(subject, to_user_list, testcase_time_id=testcase_time_id)
        return jsonify(msg=result)


testcase_report_blueprint.add_url_rule('/testcasereport/', view_func=TestCaseReport.as_view('testcase_report'))
testcase_report_blueprint.add_url_rule('/report_list', view_func=TestCaseReportList.as_view('report_list'))
testcase_report_blueprint.add_url_rule('/report_del', view_func=TestCaseReportDelete.as_view('report_del'))
testcase_report_blueprint.add_url_rule('/report_download', view_func=TestCaseReportDownLoad.as_view('report_download'))

testcase_report_blueprint.add_url_rule('/report_email', view_func=TestCaseReportSendMail.as_view('report_email'))
