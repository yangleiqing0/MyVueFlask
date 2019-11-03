import requests
from flask import Flask, session
from flask_mail import Mail
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from config import app_config
from common import ConnMysql
from flask_apscheduler import APScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
# flask_mail需要安装0.9.1版本

requests.packages.urllib3.disable_warnings()

from flask_cors import *

app = Flask(__name__)
CORS(app, supports_credentials=True)
#
# CORS(app, resources=r'/*')


def create_app():
    from config import db
    app.debug = True
    app.threaded = True
    app.secret_key = 'asldfwadadw@fwq@#!Eewew'
    app.config.from_object(app_config)
    db.init_app(app)
    from views import view_list
    print('view_list:', view_list)
    [app.register_blueprint(_view) for _view in view_list]
    return db


def return_app():
    return app


db = create_app()


def _create_db():
    # sql = 'drop database if EXISTS flasktest'
    # ConnMysql(config.host, config.port, config.root, config.pwd, '', sql).operate_mysql()
    sql2 = 'create database IF NOT EXISTS %s' % app_config.db
    ConnMysql(app_config.host, app_config.port, app_config.root, app_config.pwd, '', sql2).operate_mysql()


_create_db()


def get_app_mail():
    from modles.variables import Variables
    user_id = session.get('user_id')
    MAIL_DEFAULT_SENDER_NAME = Variables.query.filter(
        Variables.user_id == user_id, Variables.name == '_MAIL_DEFAULT_SENDER_NAME').first().value
    MAIL_DEFAULT_SENDER_EMAIL = Variables.query.filter(
        Variables.user_id == user_id, Variables.name == '_MAIL_DEFAULT_SENDER_EMAIL').first().value
    MAIL_SERVER = Variables.query.filter(Variables.user_id == user_id, Variables.name == '_MAIL_SERVER').first().value,
    MAIL_USERNAME = Variables.query.filter(Variables.user_id == user_id,
                                           Variables.name == '_MAIL_USERNAME').first().value
    MAIL_PASSWORD = Variables.query.filter(Variables.user_id == user_id,
                                           Variables.name == '_MAIL_PASSWORD').first().value
    MAIL_DEFAULT_SENDER = (MAIL_DEFAULT_SENDER_NAME + '<%s>' % MAIL_DEFAULT_SENDER_EMAIL)
    app.config.update(
        MAIL_SERVER=MAIL_SERVER[0],
        MAIL_PORT=465,
        MAIL_USE_SSL=True,
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER=MAIL_DEFAULT_SENDER
    )
    print('发送邮件的参数:', MAIL_SERVER, type(MAIL_SERVER), MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, sep='\n')
    mail = Mail(app)
    return app, mail


def my_listener(event):
    if event.exception:
        print('任务出错了！！！！！！')
    else:
        print('任务照常运行...')


scheduler = APScheduler()

scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.start()

manager = Manager(app)
# 第一个参数是Flask的实例，第二个参数是Sqlalchemy数据库实例

migrate = Migrate(app, db)
# manager是Flask-Script的实例，这条语句在flask-Script中添加一个db命令
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':

    manager.run()
    # manager.run(5001)


