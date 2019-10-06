# coding=utf-8
from flask.views import MethodView
from flask import Blueprint, jsonify
from common import get_values
from modles import Mail
from views import get_list, post_del, post_edit, re

mail_blueprint = Blueprint('mail_blueprint', __name__)


class MailUpdate(MethodView):

    def post(self):
        _id, name, subject, to_user_list, email_method, user_id = get_values(
            'id', 'name', 'subject', 'to_user_list', 'email_method', 'user_id')
        return post_edit(Mail, _id, '邮件配置', name=name, subject=subject, to_user_list=to_user_list,
                         email_method=email_method, user_id=user_id)


class MailList(MethodView):
    def get(self):
        return get_list(Mail)


class MailDelete(MethodView):

    def post(self):
        return post_del(Mail, '邮件配置')


class MailNameValidate(MethodView):

    def post(self):
        name, mail_id, user_id = get_values('name', 'email_id', 'user_id')
        if mail_id:
            mail = Mail.query.filter(Mail.id != mail_id, Mail.name == name, Mail.user_id == user_id).count()
            if mail != 0:
                return jsonify(False)
            else:
                return jsonify(True)
        mail = Mail.query.filter(Mail.name == name, Mail.user_id == user_id).count()
        if mail != 0:
            return jsonify(False)
        else:
            return jsonify(True)


class MailUserListValidate(MethodView):

    def post(self):
        to_user_list = get_values('to_user_list')
        print('to_user_list:', to_user_list)
        to_user_list = to_user_list.split(',')
        all_is_email = True
        for email in to_user_list:
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) is None:
                all_is_email = False
        if all_is_email:
            return jsonify(True)
        else:
            return jsonify(False)


mail_blueprint.add_url_rule('/email_edit', view_func=MailUpdate.as_view('email_edit'))
mail_blueprint.add_url_rule('/email_list', view_func=MailList.as_view('email_list'))
mail_blueprint.add_url_rule('/email_del', view_func=MailDelete.as_view('email_del'))

mail_blueprint.add_url_rule('/email_validate', view_func=MailNameValidate.as_view('email_validate'))
mail_blueprint.add_url_rule('/email_user_list_validate', view_func=MailUserListValidate.as_view(
    'email_user_list_validate'))
