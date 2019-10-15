# coding=utf-8
from modles import User, ProjectGroup
from flask.views import MethodView
from flask import render_template, Blueprint, redirect, url_for, jsonify, session
from common import get_values, db


user_blueprint = Blueprint('user_blueprint', __name__)


class UserRegist(MethodView):

    def post(self):
        project_groups = ProjectGroup.query.all()
        return 'OK'

    def post(self):
        username, password, project_group_id = get_values('username', 'password', 'project_group')
        user = User(username, password, project_group_id)
        db.session.add(user)
        db.session.commit()
        new_user = User.query.filter(User.username == username).first().id
        # add_pre_data_go(new_user)
        session['msg'] = '注册成功'
        return 'OK'


class UserRegistValidate(MethodView):

    def get(self):
        username = get_values('username')
        user_count = User.query.filter(User.username == username).count()
        if user_count != 0:
            return jsonify(False)
        else:
            return jsonify(True)


user_blueprint.add_url_rule('/user_regist/', view_func=UserRegist.as_view('user_regist'))

user_blueprint.add_url_rule('/user_regist_validate/', view_func=UserRegistValidate.as_view('user_regist_validate'))

