import datetime
import json
from flask.views import MethodView
from flask import render_template, Blueprint, request, redirect, url_for, jsonify, session, flash
from common import get_values, to_execute_testcase, all_to_dict
from modles import db, TestCases, TestCaseScene, User, Wait
from views import post_edit
from views.testcase_request import post_testcase

testcase_scene_blueprint = Blueprint('testcase_scene_blueprint', __name__)


class TestCaseSceneUpdate(MethodView):

    def post(self):
        _id, name, group_id, description, user_id = get_values(
            'id', 'name', 'group_id', 'description', 'user_id')
        return post_edit(TestCaseScene, _id, '测试场景', name=name, description=description, group_id=group_id, user_id=user_id)


class TestCaseSceneTestCaseList(MethodView):

    def post(self):
        search, user_id, page, pagesize, _id = get_values('search', 'user_id', 'page', 'pagesize', 'id')
        if _id:
            _list = TestCaseScene.query.get(_id).to_dict()
            return jsonify({'list': _list})
        user = User.query.get(user_id)
        _list = TestCaseScene.query.filter(TestCaseScene.user_id == user_id).order_by(
            TestCaseScene.timestamp.desc(), TestCaseScene.id.desc()).limit(pagesize).offset(pagesize*(page-1)).all()
        count = TestCaseScene.query.filter(TestCaseScene.user_id == user_id).order_by(
            TestCaseScene.timestamp.desc(), TestCaseScene.id.desc()).count()
        model_scenes = TestCaseScene.query.filter(TestCaseScene.is_model == 1,
                                                  TestCaseScene.user_id == user_id).all()
        model_cases = TestCases.query.filter(TestCases.is_model == 1, TestCases.user_id == user_id).all()
        case_groups = user.user_case_groups
        case_groups, model_scenes, model_cases = all_to_dict(_list, case_groups, model_scenes, model_cases,
                                                             model=TestCaseScene)

        return jsonify({
            'list': _list,
            'groups': case_groups,
            'model_scenes': model_scenes,
            'model_cases': model_cases,
            'count': count
        })


class TestCaseSceneRun(MethodView):

    def post(self):
        testcase_scene_id = get_values('id')
        testcase_scene = TestCaseScene.query.get(testcase_scene_id)
        testcases = testcase_scene.testcases
        testcase_results = []
        for testcase in testcases:
            testcase_result, regist_variable_value = post_testcase(testcase=testcase)
            testcase_results.extend(['【%s】' % testcase.name, testcase_result])
        testcase_results_html = '<br>'.join(testcase_results)
        print('TestCaseSceneRun: ', json.dumps({'testcase_results': testcase_results_html}))
        session['request_{}'.format(session['user_id'])] = ''
        return json.dumps(testcase_results_html)


class TestCaseSceneDelete(MethodView):

    def post(self):
        _name = '测试场景'
        scene = get_values('id')
        if isinstance(scene, list):
            for g in scene:
                _g = TestCaseScene.query.get(g.get('id'))
                cases = TestCases.query.join(TestCaseScene, TestCases.testcase_scene_id == TestCaseScene.id). \
                    filter(TestCases.testcase_scene_id == g.get('id')).all()
                if len(cases) > 0:
                    for case in cases:
                        db.session.delete(case)
                db.session.delete(_g)
            db.session.commit()
            return jsonify(msg='删除{}列表成功'.format(_name))
        _scene = TestCaseScene.query.get(scene.get('id'))
        print('scene', _scene)
        testcases = TestCases.query.join(TestCaseScene, TestCases.testcase_scene_id == TestCaseScene.id). \
            filter(TestCases.testcase_scene_id == scene.get('id')).all()

        if len(testcases) > 0:
            for testcase in testcases:
                db.session.delete(testcase)
        db.session.delete(_scene)
        db.session.commit()
        return jsonify(msg='删除{}成功'.format(_name))


class TestCaseSceneTestCaseCopy(MethodView):

    def get(self):
        scene_page, testcase_scene_id, testcase_id = get_values('scene_page', 'testcase_scene_id', 'testcase_id')
        if not testcase_id or testcase_id == "null":
            print('TestCaseSceneTestCaseCopy:', testcase_id, type(testcase_id))
            flash('请先设置用例模板')
            return redirect(url_for('testcase_scene_blueprint.testcase_scene_testcase_list', page=scene_page))

        testcase = TestCases.query.get(testcase_id)

        timestr = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        if len(testcase.name) > 30:
            name = testcase.name[:21] + timestr
        else:
            name = testcase.name + timestr
        testcase_new = TestCases(name, testcase.url, testcase.data, testcase.regist_variable,
                       testcase.regular, testcase.method, testcase.group_id, testcase.request_headers_id,
                       testcase_scene_id, testcase.hope_result, user_id=testcase.user_id, old_sql=testcase.old_sql,
                                 new_sql=testcase.old_sql, old_sql_regist_variable=testcase.old_sql_regist_variable,
                                 new_sql_regist_variable=testcase.new_sql_regist_variable, old_sql_hope_result=testcase.old_sql_hope_result,
                                 new_sql_hope_result=testcase.new_sql_hope_result, old_sql_id=testcase.old_sql_id,
                                 new_sql_id=testcase.new_sql_id)
        db.session.add(testcase_new)
        db.session.commit()
        session['msg'] = '复制用例成功'
        if Wait.query.filter(Wait.testcase_id == testcase.id).count() > 0:
            old_wait = Wait.query.filter(Wait.testcase_id == testcase.id).first()
            wait = Wait(old_wait.old_wait_sql, old_wait.old_wait, old_wait.old_wait_time, old_wait.old_wait_mysql,
                        old_wait.new_wait_sql, old_wait.new_wait, old_wait.new_wait_time,
                        old_wait.new_wait_mysql, testcase_new.id)
            db.session.add(wait)
            db.session.commit()
        return redirect(url_for('testcase_scene_blueprint.testcase_scene_testcase_list', page=scene_page))


class TestCaseSceneCopy(MethodView):

    def get(self):
        scene_page, testcase_scene_id = get_values('scene_page', 'testcase_scene_id')
        if not testcase_scene_id or testcase_scene_id == "null":
            flash('请先设置场景模板')
            return redirect(url_for('testcase_scene_blueprint.testcase_scene_testcase_list', page=scene_page))
        testcase_scene = TestCaseScene.query.get(testcase_scene_id)
        timestr = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))

        if len(testcase_scene.name) > 30:
            name = testcase_scene.name[:21] + timestr
        else:
            name = testcase_scene.name + timestr
        testcase_scene_copy = TestCaseScene(name, description=testcase_scene.description, user_id=testcase_scene.user_id)
        db.session.add(testcase_scene_copy)
        db.session.commit()
        session['msg'] = '复制场景成功'
        return redirect(url_for('testcase_scene_blueprint.testcase_scene_testcase_list', page=scene_page))


class SceneUp(MethodView):
    def post(self):
        _id = get_values('id')
        scene = TestCaseScene.query.get(_id)
        scene.updated_time = datetime.datetime.now()
        db.session.commit()
        return jsonify(msg="场景顺序提升成功")


class TestCaseSceneModel(MethodView):

    def get(self, testcase_scene_id):
        testcase_scene = TestCaseScene.query.get(testcase_scene_id)
        page = request.args.get('page')
        if testcase_scene.is_model == 0 or testcase_scene.is_model is None:
            testcase_scene.is_model = 1
            flash('设置场景模板成功')
        else:
            testcase_scene.is_model = 0
            flash('取消场景模板成功')
        db.session.commit()
        return redirect(url_for('testcase_scene_blueprint.testcase_scene_testcase_list', page=page))


class TestCaseSceneUpdateValidate(MethodView):

    def post(self):
        scene_id, name, user_id = get_values('scene_id', 'name', 'user_id')
        if scene_id:
            testcase_scene = TestCaseScene.query.filter(
                TestCaseScene.id != scene_id, TestCaseScene.name == name, TestCaseScene.user_id == user_id).count()
            if testcase_scene != 0:
                return jsonify(False)
            else:
                return jsonify(True)
        scene = TestCaseScene.query.filter(TestCaseScene.name == name, TestCaseScene.user_id == user_id).count()
        if scene != 0:
            return jsonify(False)
        else:
            return jsonify(True)


testcase_scene_blueprint.add_url_rule('/scene_edit', view_func=TestCaseSceneUpdate.as_view('scene_edit'))
testcase_scene_blueprint.add_url_rule('/testcase_scene_copy_scene/', view_func=TestCaseSceneCopy.as_view('testcase_scene_copy_scene'))
testcase_scene_blueprint.add_url_rule('/testcase_scene_model/<testcase_scene_id>/', view_func=TestCaseSceneModel.as_view('testcase_scene_model'))


testcase_scene_blueprint.add_url_rule('/testcase_scene_copy/', view_func=TestCaseSceneTestCaseCopy.as_view('testcase_scene_copy'))
testcase_scene_blueprint.add_url_rule('/scene_list', view_func=TestCaseSceneTestCaseList.as_view('scene_list'))
testcase_scene_blueprint.add_url_rule('/scene_del', view_func=TestCaseSceneDelete.as_view('scene_del'))
testcase_scene_blueprint.add_url_rule('/scene_run', view_func=TestCaseSceneRun.as_view('scene_run'))
testcase_scene_blueprint.add_url_rule('/scene_up', view_func=SceneUp.as_view('scene_up'))

testcase_scene_blueprint.add_url_rule('/scene_validate', view_func=TestCaseSceneUpdateValidate.as_view('scene_validate'))

