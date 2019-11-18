from datetime import datetime, timedelta
from flask.views import MethodView
from flask import render_template, Blueprint, make_response, redirect, url_for, session, flash, jsonify, request
from common import get_values, cdb
from modles import User, Variables


login_blueprint = Blueprint('login_blueprint', __name__)


class Index(MethodView):

    def get(self):
        return jsonify('/')


class Login(MethodView):

    def post(self):
        username, password = get_values('username', 'password')
        users = User.query.filter(User.username == username).all()
        print(users)
        if len(users) > 0:
            user = users[0]
            if user.password == password:
                session['user_id'] = user.id
                session['request_{}'.format(user.id)] = ''
                print('login user_id', session.get('user_id'))
                return jsonify(msg='登录成功', data={'user_id': user.id})
            return jsonify(err='账号或密码错误')
        return jsonify(err='账号或密码错误')


class LoginOut(MethodView):

    def get(self):
        session['user_id'] = None
        print('登出成功')
        return jsonify(msg='登出成功')


login_blueprint.add_url_rule('/', view_func=Index.as_view('/'))
login_blueprint.add_url_rule('/login', view_func=Login.as_view('login'))
login_blueprint.add_url_rule('/logout', view_func=LoginOut.as_view('logout'))
