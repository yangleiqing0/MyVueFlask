from flask.views import MethodView
from flask import Blueprint, jsonify
from common import get_values
from modles import CaseGroup, db
from . import get_list, post_edit, post_del


case_group_blueprint = Blueprint('case_group_blueprint', __name__)


class CaseGroupList(MethodView):

    def post(self):
        return get_list(CaseGroup)


class CaseGroupUpdate(MethodView):

    def post(self):
        name, description, _id, user_id = get_values('name', 'description', 'id', 'user_id')
        return post_edit(CaseGroup, _id, '用例分组', name=name, description=description, user_id=user_id)


class CaseGroupDel(MethodView):

    def post(self):
        return post_del(CaseGroup, '用例分组')


class CaseGroupValidata(MethodView):

    def post(self):
        user_id, name, group_id = get_values('user_id', 'name', 'group_id')
        if group_id:
            case_group = CaseGroup.query.filter(
                CaseGroup.id != group_id, CaseGroup.name == name, CaseGroup.user_id == user_id).count()
            if case_group != 0:
                return jsonify(False)
            else:
                return jsonify(True)
        case_group = CaseGroup.query.filter(CaseGroup.name == name, CaseGroup.user_id == user_id).count()
        if case_group != 0:
            return jsonify(False)
        else:
            return jsonify(True)


case_group_blueprint.add_url_rule('/group_list', view_func=CaseGroupList.as_view('group_list'))
case_group_blueprint.add_url_rule('/group_edit', view_func=CaseGroupUpdate.as_view('group_edit'))
case_group_blueprint.add_url_rule('/group_del', view_func=CaseGroupDel.as_view('group_del'))

case_group_blueprint.add_url_rule('/group_validate', view_func=CaseGroupValidata.as_view('group_validate'))
