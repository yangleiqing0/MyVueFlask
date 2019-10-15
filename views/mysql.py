# coding=utf-8
import json
from flask.views import MethodView
from flask import render_template, Blueprint, redirect, url_for, session, request, jsonify
from common import get_values, ConnMysql, AnalysisParams
from modles import db, Mysql, Variables
from views import post_edit, get_list, post_del

mysql_blueprint = Blueprint('mysql_blueprint', __name__)


class MysqlUpdate(MethodView):

    def post(self):
        _id,  name, ip, port, user, password, db_name, description, user_id = get_values(
            'id', 'name', 'ip', 'port', 'user', 'password', 'db_name', 'description', 'user_id')
        return post_edit(Mysql, _id, '数据库配置', name=name, ip=ip, port=port, user=user, password=password,
                         db_name=db_name, description=description, user_id=user_id)


class MysqlList(MethodView):

    def post(self):
        return get_list(Mysql)


def mysqlrun(mysql_id=None, sql='', regist_variable='', is_request=True, regist=True):
    print('MysqlRun:', sql, regist_variable)
    mysql = Mysql.query.get(mysql_id)
    if not mysql:
        return json.dumps('请检查配置数据库')
    if not sql:
        return json.dumps('请输入查询语句')
    user_id = session.get('user_id')
    host, port, db_name, user, password = AnalysisParams().analysis_more_params(
        mysql.ip, mysql.port, mysql.db_name, mysql.user, mysql.password)
    try:
        result = ConnMysql(host, int(port), user, password, db_name, sql).select_mysql()
        if regist_variable and regist:
            if Variables.query.filter(Variables.name == regist_variable, Variables.user_id == user_id).count() > 0:
                Variables.query.filter(Variables.name == regist_variable, Variables.user_id == user_id).first().value = str(result)
            else:
                variable = Variables(regist_variable, str(result), is_private=1, user_id=user_id)
                db.session.add(variable)
            db.session.commit()
            if is_request:
                result = '【查询结果】<br>' + str(result) + '<br>【注册变量名】 【' + regist_variable + '】<br>' + str(result)
            else:
                return result
        elif not regist:
            return result
        else:
            result = '【查询结果】<br>' + str(result) + '<br>【未注册变量】'
        return json.dumps(result)
    except Exception as e:
        print(e)
        return json.dumps(str(e))


class MysqlRun(MethodView):

    def post(self):
        mysql_id, sql, regist_variable = get_values('mysql_id', 'sql', 'regist_variable')
        result = mysqlrun(mysql_id, sql, regist_variable)
        return result


class MysqlTest(MethodView):

    def post(self):
        ip, port, user, password, db_name = get_values(
            'ip', 'port', 'user', 'password', 'db_name')
        host, port, db_name, user, password = AnalysisParams().analysis_more_params(
            ip, port, db_name, user, password)
        print('form:',  ip, port, user, password, db_name)
        try:
            if db_name:
                sql = 'show tables'
            else:
                sql = 'show databases'
            result = ConnMysql(host, int(port), user, password, db_name, sql).select_mysql()
            if result:
                return '连接成功'
            else:
                return '连接失败'
        except Exception as e:
            print(e)
            return '连接失败:' + str(e)


class MysqlDelete(MethodView):

    def post(self):
        return post_del(Mysql, '数据库配置')


class MysqlNameValidate(MethodView):

    def post(self):
        name, mysql_id, user_id = get_values('name', 'mysql_id', 'user_id')
        print('mysql_id')
        if mysql_id:
            mysql = Mysql.query.filter(Mysql.id != mysql_id, Mysql.name == name, Mysql.user_id == user_id).count()
            if mysql != 0:
                return jsonify(False)
            else:
                return jsonify(True)
        mysql = Mysql.query.filter(Mysql.name == name, Mysql.user_id == user_id).count()
        if mysql != 0:
            return jsonify(False)
        else:
            return jsonify(True)


mysql_blueprint.add_url_rule('/mysql_edit', view_func=MysqlUpdate.as_view('mysql_edit'))
mysql_blueprint.add_url_rule('/mysql_list', view_func=MysqlList.as_view('mysql_list'))
mysql_blueprint.add_url_rule('/mysql_del', view_func=MysqlDelete.as_view('mysql_del'))

mysql_blueprint.add_url_rule('/mysql_run', view_func=MysqlRun.as_view('mysql_run'))
mysql_blueprint.add_url_rule('/mysql_test/', view_func=MysqlTest.as_view('mysql_test'))

mysql_blueprint.add_url_rule('/mysql_validate', view_func=MysqlNameValidate.as_view('mysql_validate'))
