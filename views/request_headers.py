import json
from urllib import parse
from flask.views import MethodView
from common import get_values, all_to_dict
from flask import render_template, Blueprint, request, redirect, url_for, current_app, jsonify, session
from modles import db, RequestHeaders
from views import get_list, post_del, post_edit

request_headers_blueprint = Blueprint('request_headers_blueprint', __name__)


class RequestHeadersList(MethodView):

    def post(self):
        return get_list(RequestHeaders)


class RequestHeadersUpdate(MethodView):

    def post(self):
        name, description, _id, value, user_id = get_values('name', 'description', 'id', 'value', 'user_id')
        print('edit', name, description)
        return post_edit(RequestHeaders, _id, '请求头部', name=name, value=value, description=description, user_id=user_id)


class RequestHeadersDelete(MethodView):

    def post(self):

        return post_del(RequestHeaders, '请求头部')


class RequestHeadersValidata(MethodView):

    def post(self):
        name, request_headers_id, user_id = get_values('name', 'header_id', 'user_id')
        if request_headers_id:
            request_headers = RequestHeaders.query.filter(
                RequestHeaders.id != request_headers_id, RequestHeaders.name == name,
                RequestHeaders.user_id == user_id).count()
            if request_headers != 0:
                return jsonify(False)
            else:
                return jsonify(True)
        request_headers = RequestHeaders.query.filter(RequestHeaders.name == name, RequestHeaders.user_id == user_id).count()
        if request_headers != 0:
            return jsonify(False)
        else:
            return jsonify(True)


class RequestHeadersValueValidata(MethodView):

    def post(self):
        value = get_values('value')
        value = parse.unquote(value)
        try:
            if isinstance(eval(value), dict):
                return jsonify(True)
            else:
                return jsonify(False)
        except Exception as e:
            print(e)
            return jsonify(False)


request_headers_blueprint.add_url_rule('/header_list', view_func=RequestHeadersList.as_view('header_list'))
request_headers_blueprint.add_url_rule('/header_edit', view_func=RequestHeadersUpdate.as_view('header_edit'))
request_headers_blueprint.add_url_rule('/header_del', view_func=RequestHeadersDelete.as_view('header_del'))

request_headers_blueprint.add_url_rule('/header_validate', view_func=RequestHeadersValidata.as_view('header_validate'))

request_headers_blueprint.add_url_rule('/header_value_validate', view_func=RequestHeadersValueValidata.as_view('header_value_validate'))

