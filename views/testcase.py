# encoding=utf-8
from . import os, json, datetime, get_list, post_del, post_edit
from flask.views import MethodView
from flask import render_template, Blueprint, request, redirect, url_for, jsonify, session, send_from_directory, flash
from common import AnalysisParams, db, cdb, MethodRequest, to_execute_testcase, get_values, \
    get_now_time, read_xlsx, NullObject, RangName, WriterXlsx, all_to_dict
from modles import TestCases, CaseGroup, User, Mysql, RequestHeaders, Variables, Wait
from config.app_config import ALLOWED_EXTENSIONS, TESTCASE_XLSX_PATH

testcase_blueprint = Blueprint('testcase_blueprint', __name__)


class TestCaseRun(MethodView):

    def post(self):
        testcase = NullObject()
        testcase.name, testcase.url, testcase.data, testcase.method, request_headers_id, \
            testcase.regist_variable, testcase.regular, testcase.group_id \
            = get_values('name', 'url', 'data', 'method', 'header_id', 'regist_variable', 'regular', 'group_id')
        testcase.testcase_request_header = RequestHeaders.query.get(request_headers_id)
        testcase_results = []
        testcase_result, regist_variable_value = to_execute_testcase(testcase)
        testcase_results.extend(['【%s】' % testcase.name, testcase_result, '【正则匹配的值】', regist_variable_value])
        testcase_results_html = '<br>'.join(testcase_results)
        return jsonify(testcase_results_html)


class TestCastList(MethodView):

    def post(self):
        search, user_id, page, pagesize = get_values('search', 'user_id', 'page', 'pagesize')
        user = User.query.get(user_id)
        _list = TestCases.query.filter(TestCases.user_id == user_id, TestCases.testcase_scene_id.is_(None)). \
            order_by(TestCases.timestamp.desc()).limit(pagesize).offset(pagesize*(page-1)).all()
        case_groups = user.user_case_groups
        count = TestCases.query.filter(TestCases.user_id == user_id, TestCases.testcase_scene_id.is_(None)). \
            order_by(TestCases.timestamp.desc()).count()
        request_headers = user.user_request_headers
        mysqls = user.user_mysqls
        for mysql in mysqls:
            mysql.name = AnalysisParams().analysis_params(mysql.name)
        case_groups, request_headers, mysqls = all_to_dict(_list, case_groups, request_headers, mysqls, wait=True)
        return jsonify({
            'list': _list,
            'groups': case_groups,
            'headers': request_headers,
            'mysqls': mysqls,
            'count':count
        })


class UpdateTestCase(MethodView):

    def post(self):

        _id, user_id, name, url, method, data, group_id, request_headers_id, regist_variable, regular \
            , hope_result, old_sql, new_sql, old_sql_regist_variable, new_sql_regist_variable, \
            old_sql_hope_result, new_sql_hope_result, old_sql_id, new_sql_id, wait, testcase_scene_id, is_model = get_values(
                'id', 'user_id', 'name', 'url', 'method', 'data', 'group_id', 'header_id',
                'regist_variable', 'regular', 'hope_result', 'old_sql', 'new_sql',
                'old_sql_regist_variable', 'new_sql_regist_variable', 'old_sql_hope_result',
                'new_sql_hope_result', 'old_mysql', 'new_mysql', 'wait', 'testcase_scene_id', 'is_model')
        if not wait:
            wait = {}
        old_wait_sql, old_wait, old_wait_time, old_wait_mysql, new_wait_sql, new_wait, new_wait_time, new_wait_mysql = \
            wait.get('old_wait_sql'), wait.get('old_wait'), wait.get('old_wait_time'), \
            wait.get('old_wait_mysql'), wait.get('new_wait_sql'), wait.get('new_wait'), \
            wait.get('new_wait_time'), wait.get('new_wait_mysql')

        if not old_wait_mysql:
            old_wait_mysql = None
        if not new_wait_mysql:
            new_wait_mysql = None
        if not old_sql_id:
            old_sql_id = None
        if not new_sql_id:
            new_sql_id = None

        if not _id:
            testcase = TestCases(
                name, url, data, regist_variable, regular, method, group_id,
                request_headers_id, testcase_scene_id, hope_result, user_id=user_id, old_sql=old_sql, new_sql=new_sql,
                old_sql_regist_variable=old_sql_regist_variable, new_sql_regist_variable=new_sql_regist_variable,
                old_sql_hope_result=old_sql_hope_result, new_sql_hope_result=new_sql_hope_result, old_sql_id=old_sql_id,
                new_sql_id=new_sql_id, is_model=is_model)
            add_regist_variable(old_sql_regist_variable, new_sql_regist_variable, user_id)
            db.session.add(testcase)
            db.session.commit()

            wait = Wait(old_wait_sql, old_wait, old_wait_time, old_wait_mysql, new_wait_sql, new_wait, new_wait_time,
                        new_wait_mysql, testcase.id)

            db.session.add(wait)
            db.session.commit()
            return jsonify(msg="添加用例成功")

        testcase = TestCases.query.get(_id)
        if testcase.wait:
            wait = Wait.query.filter(Wait.testcase_id == _id).first()
            wait.old_wait_sql = old_wait_sql
            wait.old_wait = old_wait
            wait.old_wait_time = old_wait_time
            wait.old_wait_mysql = old_wait_mysql
            wait.new_wait_sql = new_wait_sql
            wait.new_wait = new_wait
            wait.new_wait_time = new_wait_time
            wait.new_wait_mysql = new_wait_mysql
        else:
            wait = Wait(old_wait_sql, old_wait, old_wait_time, old_wait_mysql, new_wait_sql, new_wait, new_wait_time,
                        new_wait_mysql, testcase.id)
            db.session.add(wait)
        db.session.commit()

        update_regist_variable(_id, old_sql_regist_variable, new_sql_regist_variable, user_id)
        update_test_case_sql = 'update testcases set name=%s,url=%s,data=%s,method=%s,group_id=%s,' \
                               'request_headers_id=%s,regist_variable=%s,regular=%s,hope_result=%s,' \
                               'old_sql=%s,new_sql=%s,old_sql_regist_variable=%s,new_sql_regist_variable=%s,' \
                               'old_sql_hope_result=%s, new_sql_hope_result=%s, old_sql_id=%s, ' \
                               'new_sql_id=%s,is_model=%s where id=%s'
        cdb().opeat_db(update_test_case_sql, (name, url, data, method, group_id,
                                              request_headers_id, regist_variable, regular, hope_result, old_sql,
                                              new_sql, old_sql_regist_variable, new_sql_regist_variable,
                                              old_sql_hope_result, new_sql_hope_result, old_sql_id, new_sql_id,
                                              is_model, _id))

        return jsonify(msg="编辑用例成功")


class TestCaseCopy(MethodView):

    def get(self):
        page, testcase_id = get_values('page', 'testcase_id')
        testcase_self = TestCases.query.get(testcase_id)
        if not testcase_id or testcase_id == "null":
            flash('请配置用例模板')
            return redirect(url_for('testcase_blueprint.test_case_list', page=page))

        timestr = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        if len(testcase_self.name) > 30:
            name = testcase_self.name[:31] + timestr
        else:
            name = testcase_self.name + timestr
        testcase = TestCases(name, testcase_self.url, testcase_self.data, testcase_self.regist_variable,
                             testcase_self.regular, testcase_self.method, testcase_self.group_id,
                             testcase_self.request_headers_id, hope_result=testcase_self.hope_result,
                             user_id=testcase_self.user_id, old_sql=testcase_self.old_sql,
                             new_sql=testcase_self.old_sql,
                             old_sql_regist_variable=testcase_self.old_sql_regist_variable,
                             new_sql_regist_variable=testcase_self.new_sql_regist_variable,
                             old_sql_hope_result=testcase_self.old_sql_hope_result,
                             new_sql_hope_result=testcase_self.new_sql_hope_result, old_sql_id=testcase_self.old_sql_id,
                             new_sql_id=testcase_self.new_sql_id)
        db.session.add(testcase)
        db.session.commit()
        session['msg'] = '复制用例成功'
        if Wait.query.filter(Wait.testcase_id == testcase_id).count() > 0:
            old_wait = Wait.query.filter(Wait.testcase_id == testcase_id).first()
            wait = Wait(old_wait.old_wait_sql, old_wait.old_wait, old_wait.old_wait_time, old_wait.old_wait_mysql,
                        old_wait.new_wait_sql, old_wait.new_wait, old_wait.new_wait_time,
                        old_wait.new_wait_mysql, testcase.id)
            db.session.add(wait)
            db.session.commit()
        return redirect(url_for('testcase_blueprint.test_case_list', page=page))


class DeleteTestCase(MethodView):

    def post(self):
        _name = '测试用例'
        case = get_values('id', post=True)
        if isinstance(case, list):
            for g in case:
                if Wait.query.filter(Wait.testcase_id == g.get('id')).count() > 0:
                    wait = Wait.query.filter(Wait.testcase_id == g.get('id')).first()
                    db.session.delete(wait)
                case_group = TestCases.query.get(g.get('id'))
                db.session.delete(case_group)
            db.session.commit()
            return jsonify(msg='删除{}列表成功'.format(_name))
        if Wait.query.filter(Wait.testcase_id == case.get('id')).count() > 0:
            wait = Wait.query.filter(Wait.testcase_id == case.get('id')).first()
            db.session.delete(wait)
        case_group = TestCases.query.get(case.get('id'))
        db.session.delete(case_group)
        db.session.commit()
        return jsonify(msg='删除{}成功'.format(_name))


class TestCaseUrls(MethodView):

    def get(self):
        user_id = session.get('user_id')
        urls_sql = 'select url from testcases where user_id=%s'
        urls = list(set(cdb().query_db(urls_sql, params=(user_id,))))
        testcases_urls = []
        [testcases_urls.append(AnalysisParams().analysis_params(url[0])) for url in urls]
        testcases_urls.sort()
        return render_template('test_case/testcase_urls.html', testcases_urls=testcases_urls)


class TestCaseDownload(MethodView):

    def get(self):
        user_id = session.get('user_id')
        testcases = TestCases.query.filter(TestCases.testcase_scene_id.is_(None), TestCases.user_id == user_id). \
            with_entities(TestCases.id, TestCases.name, TestCases.method, TestCases.url, TestCases.data,
                          TestCases.regist_variable, TestCases.regular, TestCases.group_id.name,
                          TestCases.request_headers_id, TestCases.testcase_scene_id, TestCases.hope_result).all()
        now = get_now_time()
        dir_path, xlsx_name = WriterXlsx('testcases_' + now, testcases).open_xlsx()
        return send_from_directory(dir_path, xlsx_name, as_attachment=True)


class TestCaseUpload(MethodView):

    def post(self):
        if request.files.get('upload_xlsx'):
            xlsx = request.files['upload_xlsx']
            print('xlsx', xlsx)
            if allowed_file(xlsx.filename):
                now = get_now_time()
                dir_path = TESTCASE_XLSX_PATH + 'upload'
                Image = now + os.path.splitext(xlsx.filename)[-1]
                xlsx.save(os.path.join(dir_path, Image))
                xlsx_path = dir_path + '/' + Image
                row_list = read_xlsx(xlsx_path)
                print('row_list:', row_list)
                add_upload_testcases(row_list)
                os.remove(xlsx_path)
            else:
                flash('错误的文件格式')
                return redirect(url_for('testcase_blueprint.test_case_list'))
        else:
            flash('请选择上传文件')
        return redirect(url_for('testcase_blueprint.test_case_list'))


class TestCaseValidata(MethodView):

    def post(self):
        name, user_id, testcase_id = get_values('name', 'user_id', 'case_id')
        if testcase_id:
            testcase = TestCases.query.filter(
                TestCases.id != testcase_id).filter(TestCases.name == name, TestCases.user_id == user_id).count()
            if testcase != 0:
                return jsonify(False)
            else:
                return jsonify(True)
        testcase = TestCases.query.filter(TestCases.name == name, TestCases.user_id == user_id).count()
        if testcase != 0:
            return jsonify(False)
        else:
            return jsonify(True)


class TestCaseHopeResultValidata(MethodView):

    def post(self):
        hope_result = get_values('hope_result')
        print('hope_result: ', hope_result)
        try:
            hope_results = hope_result.split(',')
            for hope_result in hope_results:
                com_method, _ = hope_result.split(':', 1)
                if com_method not in ["包含", "不包含", "等于", "不等于"]:
                    return jsonify(False)
            return jsonify(True)
        except Exception as e:
            print(e)
            return jsonify(False)


class RegularValidata(MethodView):

    def post(self):
        regular = get_values('regular')
        regular_list = regular.split(',')
        for _regular in regular_list:
            print('_regular:', _regular)
            if '$' in _regular:
                if _regular[1] != '.':
                    return jsonify(False)
                if len(_regular.split('.')) != len(set(_regular.split('.'))):
                    return jsonify(False)
                else:
                    for key in _regular.split('.'):
                        if ' ' in key:
                            return jsonify(False)
        return jsonify(True)


testcase_blueprint.add_url_rule('/case_list', view_func=TestCastList.as_view('case_list'))
testcase_blueprint.add_url_rule('/case_del', view_func=DeleteTestCase.as_view('case_del'))
testcase_blueprint.add_url_rule('/case_edit', view_func=UpdateTestCase.as_view('case_edit'))
testcase_blueprint.add_url_rule('/case_run', view_func=TestCaseRun.as_view('case_run'))
testcase_blueprint.add_url_rule('/copy_test_case/', view_func=TestCaseCopy.as_view('copy_test_case'))
testcase_blueprint.add_url_rule('/test_case_urls/', view_func=TestCaseUrls.as_view('test_case_urls'))
testcase_blueprint.add_url_rule('/case_download', view_func=TestCaseDownload.as_view('case_download'))
testcase_blueprint.add_url_rule('/case_upload', view_func=TestCaseUpload.as_view('case_upload'))

testcase_blueprint.add_url_rule('/case_validate', view_func=TestCaseValidata.as_view('case_validate'))
testcase_blueprint.add_url_rule('/regular_validate', view_func=RegularValidata.as_view('regular_validate'))
testcase_blueprint.add_url_rule('/hope_validate',
                                view_func=TestCaseHopeResultValidata.as_view('hope_validate'))


def add_regist_variable(old_sql_regist_variable, new_sql_regist_variable, user_id):
    if old_sql_regist_variable:
        old_variable = Variables(old_sql_regist_variable, '', user_id=user_id, is_private=1)
        db.session.add(old_variable)
    if new_sql_regist_variable:
        new_variable = Variables(new_sql_regist_variable, '', user_id=user_id, is_private=1)
        db.session.add(new_variable)


def update_regist_variable(testcase_id, old_sql_regist_variable, new_sql_regist_variable, user_id):
    testcase = TestCases.query.get(testcase_id)
    if testcase.old_sql_regist_variable and old_sql_regist_variable:
        if Variables.query.filter(Variables.name == testcase.old_sql_regist_variable,
                                  Variables.user_id == user_id).count() > 0:
            Variables.query.filter(Variables.name == testcase.old_sql_regist_variable,
                                   Variables.user_id == user_id).first().name = old_sql_regist_variable

    if testcase.new_sql_regist_variable and new_sql_regist_variable:
        if Variables.query.filter(Variables.name == testcase.new_sql_regist_variable,
                                  Variables.user_id == user_id).count() > 0:
            Variables.query.filter(Variables.name == testcase.new_sql_regist_variable,
                                   Variables.user_id == user_id).first().name = new_sql_regist_variable
    db.session.commit()


def allowed_file(filename):
    _, ext = os.path.splitext(filename)
    print('ext.lower() in ALLOWED_EXTENSIONS:', ext.lower() in ALLOWED_EXTENSIONS)
    return ext.lower() in ALLOWED_EXTENSIONS  # 判断文件后缀在不在可允许的文件类型下


def add_upload_testcases(testcases):
    user_id = session.get('user_id')
    print('testcases:', testcases, len(testcases))
    if len(testcases) > 0:
        for testcase in testcases:
            testcase.pop(0)  # 自动删除ID列
            if not testcase[2]:  # 请求方式
                continue
            if testcase[2].lower() not in ['put', 'post', 'get', 'delete', 'head', 'options']:
                continue
            testcase[0] = AnalysisParams().analysis_params(testcase[0])  # 解析用例名称
            print(testcase[0],
                  TestCases.query.filter(TestCases.name == testcase[0], TestCases.user_id == user_id).count())
            if testcase[0] and not TestCases.query.filter(TestCases.name == testcase[0],
                                                          TestCases.user_id == user_id).count():
                if testcase[-1]:  # 用例分组
                    if not CaseGroup.query.filter(CaseGroup.name == testcase[-1], CaseGroup.user_id == user_id).count():
                        case_group = CaseGroup(testcase[-1], user_id=user_id)
                        db.session.add(case_group)
                        db.session.commit()
                        testcase[-1] = case_group.id
                    else:
                        testcase[-1] = CaseGroup.query.filter(CaseGroup.name == testcase[-1],
                                                              CaseGroup.user_id == user_id).first().id
                else:
                    testcase[-1] = None
                if testcase[3]:  # 请求头部
                    if not RequestHeaders.query.filter(RequestHeaders.value == testcase[3],
                                                       RequestHeaders.user_id == user_id).count():
                        request_headers_name = testcase[0] + RangName.rand_name('6')  # 6位随机数+用例名作为头部名称
                        request_headers = RequestHeaders(request_headers_name, testcase[3], user_id=user_id)
                        db.session.add(request_headers)
                        db.session.commit()
                        testcase[3] = request_headers.id
                    else:
                        testcase[3] = RequestHeaders.query.filter(RequestHeaders.value == testcase[3],
                                                                  RequestHeaders.user_id == user_id).first().id
                _testcase = TestCases(testcase[0], testcase[1], testcase[4], testcase[6], testcase[7],
                                      testcase[2], testcase[-1], testcase[3], hope_result=testcase[5], user_id=user_id)
                db.session.add(_testcase)
                db.session.commit()
    else:
        print("空文件或已存在此用例")
