# encoding=utf-8

from _datetime import datetime
from flask.views import MethodView
from flask import render_template, Blueprint, request, session, current_app, jsonify
from common import AnalysisParams, to_execute_testcase, NullObject, AssertMethod, to_dict
from views import mysqlrun, json, time
from views.com import get_values
from modles import datetime, TestCases, TestCaseResult, CaseGroup, TestCaseStartTimes, TestCaseScene, User, db, \
    Variables

test_case_request_blueprint = Blueprint('test_case_request_blueprint', __name__)


class TestCaseRequest(MethodView):

    def get(self):
        user_id = session.get('user_id')
        print('user_id:', user_id)
        case_groups = CaseGroup.query.filter(CaseGroup.user_id == user_id).order_by(
            CaseGroup.updated_time.desc(), CaseGroup.id.desc()).all()
        # to_dict(case_groups)
        case_groups_new = []
        for case_group in case_groups:
            case_group_NullObject = NullObject()
            case_group_NullObject.name = case_group.name
            case_group_NullObject.id = case_group.id
            # case_group_NullObject.choose = []
            # case_group_NullObject.checkAll = True
            # case_group_NullObject.isIndeterminate = True
            testcase_list = []
            testcases = TestCases.query.join(CaseGroup, CaseGroup.id == TestCases.group_id).filter(
                TestCases.testcase_scene_id.is_(None), TestCases.group_id == case_group.id, TestCases.user_id == user_id
            ).order_by(TestCases.updated_time.desc(), TestCases.id.desc()).all()
        #     print(' %s testcases_:' % case_group, testcases)
            for testcase in testcases:
                testcase_NullObject = NullObject()
                testcase_NullObject.id = testcase.id
                testcase_NullObject.name = testcase.name
                testcase_NullObject.is_testcase_scene = 0
                testcase_list.append(testcase_NullObject.__dict__)
            try:
                case_group_scene = TestCaseScene.query.join(CaseGroup, CaseGroup.id == TestCaseScene.group_id).filter(
                    TestCaseScene.user_id == user_id, CaseGroup.name == case_group.name).order_by(
                    TestCaseScene.updated_time.desc(), TestCaseScene.id.desc()).all()
                for testcase_scene in case_group_scene:
                    testcase_scene_NullObject = NullObject()
                    testcase_scene_NullObject.id = testcase_scene.id
                    testcase_scene_NullObject.name = testcase_scene.name
                    testcase_scene_NullObject.is_testcase_scene = 1
                    testcase_list.append(testcase_scene_NullObject.__dict__)
            except KeyError:
                pass

            case_group_NullObject.testcase_list = testcase_list
            case_groups_new.append(case_group_NullObject.__dict__)
        print('testcase_list: ', case_groups_new)

        return jsonify({'list': case_groups_new})

    def post(self):
        time_id = get_values('id')
        case_time = TestCaseStartTimes.query.get(time_id)
        testcase_ids, testcase_scene_ids = json.loads(case_time.case_list), json.loads(case_time.scene_list)
        print('TestCaseRequest post request.form: ', testcase_ids, testcase_scene_ids)
        for _i in range(len(testcase_ids)):
            testcase_ids[_i] = int(testcase_ids[_i])
        scene_case_list = []
        testcase_list = []
        for index, testcase_id in enumerate(testcase_ids):
            testcase = TestCases.query.get(int(testcase_id))
            testcase.name = AnalysisParams().analysis_params(testcase.name)
            case_dict = testcase.get_dict('id', 'name')
            case_dict['response_body'] = get_response_body(testcase.id, time_id)
            case_dict['is_show'] = False
            testcase_list.append(case_dict)
            scene_case_list.append([testcase.id, ])
        print('testcase_list post: ', testcase_list,  scene_case_list)

        scene_list = []
        for testcase_scene_id in testcase_scene_ids:
            testcase_scene = TestCaseScene.query.get(int(testcase_scene_id))
        #     scene_list.append(_testcase_scene)
        #
        # cmpfun = operator.attrgetter('updated_time')
        # scene_list.sort(key=cmpfun, reverse=True)
        # print('scene_list', scene_list)
        # for testcase_scene in scene_list:
            testcases = testcase_scene.testcases
            case_list = []
            for testcase in testcases:
                testcase.name = AnalysisParams().analysis_params(testcase.name)
                testcase.scene_name = testcase.testcase_scene.name
                case_dict = testcase.get_dict('id', 'name', 'scene_name')
                case_dict['response_body'] = get_response_body(testcase.id, time_id)
                case_dict['is_show'] = False
                testcase_list.append(case_dict)
                case_list.append(testcase.id)
                testcase_ids.append(testcase.id)
            scene_case_list.append(case_list)
        print("request_testcase_ids_list: ", scene_list)

        return jsonify({'list': testcase_list, 'scene_case_list': scene_case_list, 'testcase_ids': testcase_ids})


class TestCaseRequestStart(MethodView):

    def post(self):
        print(request.args)
        test_case_id, testcase_time_id = get_values('case_id', 'time_id')
        print('异步请求的test_case_id,testcase_time_id: ', test_case_id, testcase_time_id)
        response_body = post_testcase(test_case_id, testcase_time_id)
        return jsonify(response_body)


def get_response_body(case_id, time_id):
    response_body = ''
    print('get_response_body', case_id, time_id)
    if not case_id:
        return response_body
    if TestCaseResult.query.filter(TestCaseResult.testcase_id == case_id,
                                   TestCaseResult.testcase_start_time_id == time_id).count():
        case_result = TestCaseResult.query.filter(TestCaseResult.testcase_id == case_id,
                                                  TestCaseResult.testcase_start_time_id == time_id).first()
        if case_result.response_body:
            response_body = case_result.response_body
    return response_body


def post_testcase(test_case_id=None, testcase_time_id=None, testcase=None, is_run=False, is_commit=True):

    if not testcase:
        testcase = TestCases.query.get(test_case_id)
    else:
        is_run = True
    session[testcase.name] = []
    method = testcase.method
    if isinstance(testcase, NullObject):
        url, data = AnalysisParams().analysis_more_params(testcase.url, testcase.data, testcase_name=testcase.name)
        return to_execute_testcase(testcase, url, data , is_commit=is_commit)

    if testcase.wait:
        # 前置等待验证
        # url, data = AnalysisParams().analysis_more_params(testcase.url, testcase.data, testcase_name=testcase.name)
        hope_result = AnalysisParams().analysis_more_params(testcase.hope_result)
        wait = testcase.wait[0]
        time_count = 0
        if wait.old_wait_mysql and wait.old_wait and wait.old_wait_sql:
            _hope_result = AnalysisParams().analysis_params(wait.old_wait)
            mysqlrun(mysql_id=wait.old_wait_mysql, sql=wait.old_wait_sql, is_request=False, regist=False, is_cache=True)
            while 1:
                old_wait_value = mysqlrun(mysql_id=wait.old_wait_mysql, sql=wait.old_wait_sql, is_request=False,
                                          regist=False, cache=True)
                old_wait_assert_result = AssertMethod(actual_result=old_wait_value,
                                                      hope_result=_hope_result).assert_method()
                if old_wait_assert_result == "测试成功":
                    break
                else:
                    print('5s后执行下一次前置验证, 此次查询结果: %s 已执行 %ss  等待超时%s' % (old_wait_value, time_count,  int(wait.old_wait_time) * 60))
                    time_count += 5
                    time.sleep(5)
                if wait.old_wait_time:
                    if time_count == int(wait.old_wait_time) * 60:
                        time_out_mes = "前置等待超时, 查询结果 %s" % old_wait_value
                        if testcase_time_id:
                            testcase_result = TestCaseResult(test_case_id, testcase.name, testcase.url, testcase.data, method, hope_result,
                                                             testcase_time_id, '', '',
                                                             old_sql_value='',
                                                             new_sql_value='',
                                                             old_sql_value_result='',
                                                             new_sql_value_result='', result=time_out_mes,
                                                             scene_id=testcase.testcase_scene_id)
                            # 测试结果实例化
                            db.session.add(testcase_result)
                            db.session.commit()
                        return time_out_mes
    print('testcase.old', testcase.old_sql, testcase.old_sql_id, testcase.old_sql_regist_variable)
    old_sql_value, old_sql_value_result = get_assert_value(testcase, 'old_sql')

    url, data = AnalysisParams().analysis_more_params(testcase.url, testcase.data, testcase_name=testcase.name)

    response_body, regist_variable_value = to_execute_testcase(testcase, url, data)
    # 发送请求

    hope_result = AnalysisParams().analysis_more_params(testcase.hope_result)
    # 结果比较前进行解析期望参数
    testcase_test_result = AssertMethod(actual_result=response_body, hope_result=hope_result).assert_method()

    new_sql_value, new_sql_value_result = get_assert_value(testcase, 'new_sql')

    print('testcase_test_result:', testcase_test_result)
    if testcase_test_result == "测试失败" or old_sql_value_result == "测试失败" or new_sql_value_result == "测试失败":
        test_result = "测试失败"
    else:
        test_result = "测试成功"

    if testcase.wait:
        # 后置等待验证
        print('进入后置等待:', testcase)
        wait = testcase.wait[0]
        time_new_count = 0
        if wait.new_wait_mysql and wait.new_wait and wait.new_wait_sql:
            __hope_result = AnalysisParams().analysis_params(wait.new_wait)
            mysqlrun(mysql_id=wait.new_wait_mysql, sql=wait.new_wait_sql, is_request=False,
                     regist=False, is_cache=True)
            # 先运行一次进行缓存数据，后面每次直接调用
            while 1:
                new_wait_value = mysqlrun(mysql_id=wait.new_wait_mysql, sql=wait.new_wait_sql, is_request=False,
                                          regist=False, cache=True)
                new_wait_assert_result = AssertMethod(actual_result=new_wait_value,
                                                      hope_result=__hope_result).assert_method()
                if new_wait_assert_result == "测试成功":
                    break
                else:
                    print('5s后执行下一次后置验证, 此次查询结果: %s 已执行 %ss  等待超时%s' % (
                    new_wait_value, time_new_count, int(wait.new_wait_time) * 60))
                    time_new_count += 5
                    time.sleep(5)
                if wait.new_wait_time:
                    if time_new_count == int(wait.new_wait_time) * 60:
                        time_out_new_mes = "后置等待超时, 查询结果 %s" % new_wait_value
                        test_result = time_out_new_mes
                        break
    if testcase_time_id:
        # 如果存在此记录，则修改此记录，不存在则创建
        if TestCaseResult.query.filter(TestCaseResult.testcase_start_time_id == testcase_time_id,
                                       TestCaseResult.testcase_id == test_case_id).count():
            case_result = TestCaseResult.query.filter(TestCaseResult.testcase_start_time_id == testcase_time_id,
                                                      TestCaseResult.testcase_id == test_case_id).first()
            case_result.response_body = response_body
            case_result.result = test_result
        else:
            testcase_result = TestCaseResult(test_case_id, testcase.name, url, data, method, hope_result,
                                             testcase_time_id, response_body, testcase_test_result,
                                             old_sql_value=str(old_sql_value), new_sql_value=str(new_sql_value),
                                             old_sql_value_result=old_sql_value_result,
                                             new_sql_value_result=new_sql_value_result,
                                             result=test_result, scene_id=testcase.testcase_scene_id)
            # 测试结果实例化
            db.session.add(testcase_result)
        db.session.commit()
    session.pop(testcase.name)
    if is_run:
        return response_body, regist_variable_value

    return response_body


class TestCaseTimeGet(MethodView):

    def post(self):
        #  获得本次测试批号和是否开启异步场景功能
        # print('current_app.name: ', current_app.name)
        user_id = session.get('user_id')
        case_list, scene_list = get_values('case_list', 'scene_list')
        time_strftime = datetime.now().strftime('%Y%m%d%H%M%S')
        testcase_time = TestCaseStartTimes(time_strftime=time_strftime, user_id=user_id, case_list=json.dumps(case_list),
                                           scene_list=json.dumps(scene_list))
        db.session.add(testcase_time)
        db.session.commit()
        print('testcase_time: ', testcase_time)

        scene_async = Variables.query.filter(Variables.name == '_Scene_Async', Variables.user_id == user_id).first().value
        return jsonify({"time_id": testcase_time.id, 'scene_async': scene_async})


test_case_request_blueprint.add_url_rule('/request_play', view_func=TestCaseRequest.as_view('request_play'))
test_case_request_blueprint.add_url_rule('/request_start', view_func=TestCaseRequestStart.as_view('request_start'))
test_case_request_blueprint.add_url_rule('/time_get', view_func=TestCaseTimeGet.as_view('time_get'))


def get_assert_value(testcase, value):
    if value == 'old_sql':
        if testcase.old_sql and testcase.old_sql_id:
            if not testcase.old_sql_regist_variable:
                old_sql_regist_variable = ''
            else:
                old_sql_regist_variable = testcase.old_sql_regist_variable
            old_sql_value = mysqlrun(mysql_id=testcase.old_sql_id, sql=testcase.old_sql,
                                     regist_variable=old_sql_regist_variable, is_request=False)
            if testcase.old_sql_hope_result:
                old_sql_value_result = AssertMethod(actual_result=old_sql_value, hope_result=AnalysisParams().analysis_params(testcase.old_sql_hope_result)).assert_method()
            else:
                old_sql_value_result = ''
            print('old_sql_value_result:', old_sql_value_result, old_sql_value)
        else:
            old_sql_value = old_sql_value_result = ''
        return old_sql_value, old_sql_value_result

    elif value == 'new_sql':
        if testcase.new_sql and testcase.new_sql_id:
            if not testcase.new_sql_regist_variable:
                new_sql_regist_variable = ''
            else:
                new_sql_regist_variable = testcase.new_sql_regist_variable
            new_sql_value = mysqlrun(mysql_id=testcase.new_sql_id, sql=testcase.new_sql,
                                     regist_variable=new_sql_regist_variable, is_request=False)
            print('new_sql_regist_variable:', testcase.new_sql_regist_variable)
            if testcase.new_sql_hope_result:
                new_sql_value_result = AssertMethod(actual_result=new_sql_value,
                                                    hope_result=AnalysisParams().analysis_params(
                                                        testcase.new_sql_hope_result)).assert_method()
            else:
                new_sql_value_result = ''
            print('new_sql_value_result:', new_sql_value_result)
        else:
            new_sql_value = new_sql_value_result = ''
        # 调用比较的方法判断响应报文是否满足期望
        return new_sql_value, new_sql_value_result


