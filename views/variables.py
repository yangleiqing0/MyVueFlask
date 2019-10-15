from flask.views import MethodView
from common import get_values
from flask import render_template, Blueprint, request, redirect, url_for, current_app, jsonify, session, flash
from modles import db, Variables, TestCases
from views import get_list, post_del, post_edit

variables_blueprint = Blueprint('variables_blueprint', __name__)


class VariableList(MethodView):

    def post(self):
        return get_list(Variables)


class VariableUpdate(MethodView):

    def post(self):
        name, value, description, _id, user_id = get_values('name', 'value', 'description', 'id', 'user_id')
        return post_edit(Variables, _id, '全局变量', name=name, value=value, description=description, user_id=user_id)


class VariableDelete(MethodView):

    def post(self):
        return post_del(Variables, '全局变量')


class VariableValidata(MethodView):

    def post(self):
        variable_id, name, testcase_id, regist_variable, update, user_id = get_values(
            'variable_id', 'name', 'testcase_id', 'regist_variable', 'update', 'user_id')
        print('update:', update, user_id)
        if update:
            if variable_id:
                variables = Variables.query.filter(
                    Variables.id != variable_id, Variables.name == name, Variables.user_id == user_id).count()
                if variables != 0:
                    return jsonify(False)
                else:
                    return jsonify(True)
            else:
                testcase = TestCases.query.get(testcase_id)
                regist_variables = regist_variable.split(',')
                regist_variables.sort()
                testcase_regist_variable = testcase.regist_variable.split(',')
                testcase_regist_variable.sort()

                if len(regist_variables) != len(set(regist_variables)):
                    return jsonify(False)
                if testcase_regist_variable == regist_variables:
                    return jsonify(True)
                for _regist_variable in regist_variables:
                    var = Variables.query.filter(Variables.name == _regist_variable, Variables.user_id == user_id).first()
                    print('VariableUpdateValidata var: ', var, regist_variables)
                    if var:
                        variable = Variables.query.filter(
                            Variables.id != var.id, Variables.name == _regist_variable,
                            Variables.user_id == user_id).count()
                    else:
                        variable = Variables.query.filter(
                            Variables.name == _regist_variable, Variables.user_id == user_id).count()
                    if variable != 0:
                        return jsonify(False)
                return jsonify(True)
        if name:
            regist_variable = name
        if ',' in regist_variable and len(regist_variable) > 0:
            variable_list = regist_variable.split(',')
            if len(variable_list) != len(set(variable_list)):
                return jsonify(False)
            print('variable_list:', variable_list)
            for _variable in variable_list:
                variable = Variables.query.filter(Variables.name == _variable,
                                                  Variables.user_id == user_id).count()
                if variable != 0:
                    return jsonify(False)
            return jsonify(True)
        else:
            variable = Variables.query.filter(Variables.name == regist_variable, Variables.user_id == user_id).count()
            if variable != 0:
                return jsonify(False)
            else:
                return jsonify(True)


class OldSqlVariableValidata(MethodView):

    def get(self):
        user_id = session.get('user_id')
        old_sql_regist_variable = get_values('old_sql_regist_variable')
        if not old_sql_regist_variable:
            return jsonify(True)
        variable = Variables.query.filter(Variables.name == old_sql_regist_variable, Variables.user_id == user_id).count()
        if variable != 0:
            return jsonify(False)
        else:
            return jsonify(True)


class NewSqlVariableValidata(MethodView):

    def get(self):
        user_id = session.get('user_id')
        new_sql_regist_variable = get_values('new_sql_regist_variable')
        if not new_sql_regist_variable:
            return jsonify(True)
        variable = Variables.query.filter(Variables.name == new_sql_regist_variable,
                                          Variables.user_id == user_id).count()
        if variable != 0:
            return jsonify(False)
        else:
            return jsonify(True)


class OldSqlVariableUpdateValidata(MethodView):

    def get(self):
        user_id = session.get('user_id')
        old_sql_regist_variable, testcase_id = get_values('old_sql_regist_variable', 'testcase_id')
        print('OldSqlVariableUpdateValidata:', old_sql_regist_variable, testcase_id)
        testcase = TestCases.query.get(testcase_id)
        if not old_sql_regist_variable:
            return jsonify(True)
        var = Variables.query.filter(Variables.name == testcase.old_sql_regist_variable, Variables.user_id == user_id).first()
        # print('OldSqlVariableUpdateValidata var:', var, var.id)
        if var:
            variable = Variables.query.filter(
                Variables.id != var.id, Variables.name == old_sql_regist_variable, Variables.user_id == user_id).count()
        else:
            variable = Variables.query.filter(
                Variables.name == old_sql_regist_variable, Variables.user_id == user_id).count()
        if variable != 0:
            return jsonify(False)
        else:
            return jsonify(True)


class NewSqlVariableUpdateValidata(MethodView):

    def get(self):
        user_id = session.get('user_id')
        new_sql_regist_variable, testcase_id = get_values('new_sql_regist_variable', 'testcase_id')
        testcase = TestCases.query.get(testcase_id)
        print('new_sql_regist_variable:', new_sql_regist_variable)
        if not new_sql_regist_variable:
            return jsonify(True)
        var = Variables.query.filter(Variables.name == testcase.new_sql_regist_variable, Variables.user_id == user_id).first()
        if var:
            variable = Variables.query.filter(
                Variables.id != var.id, Variables.name == new_sql_regist_variable, Variables.user_id == user_id).count()
        else:
            variable = Variables.query.filter(
                Variables.name == new_sql_regist_variable, Variables.user_id == user_id).count()
        if variable != 0:
            return jsonify(False)
        else:
            return jsonify(True)


variables_blueprint.add_url_rule('/variable_list', view_func=VariableList.as_view('variable_list'))
variables_blueprint.add_url_rule('/variable_edit', view_func=VariableUpdate.as_view('variable_edit'))
variables_blueprint.add_url_rule('/variable_del', view_func=VariableDelete.as_view('variable_del'))

variables_blueprint.add_url_rule('/variable_validate', view_func=VariableValidata.as_view('variable_validate'))
variables_blueprint.add_url_rule('/old_sql_regist_variable/', view_func=OldSqlVariableValidata.as_view('old_sql_regist_variable'))
variables_blueprint.add_url_rule('/new_sql_regist_variable/', view_func=NewSqlVariableValidata.as_view('new_sql_regist_variable'))
variables_blueprint.add_url_rule('/old_sql_regist_update_variable/', view_func=OldSqlVariableUpdateValidata.as_view('old_sql_regist_update_variable'))
variables_blueprint.add_url_rule('/new_sql_regist_update_variable/', view_func=NewSqlVariableUpdateValidata.as_view('new_sql_regist_update_variable'))