from common import get_values, all_to_dict
from modles import Variables, db, TestCaseStartTimes
from flask import jsonify


def get_list(_object):
    search, user_id,  page, pagesize, _all = get_values('search', 'user_id', 'page', 'pagesize', 'all')
    print('search', search, user_id,  page, pagesize)
    if not isinstance(page, int) or page <= 0:
        page = 1
    if user_id:
        if _all:
            _list = _object.query.filter(_object.user_id == user_id). \
                order_by(_object.timestamp.desc(), _object.id.desc()).all()
            count = len(_list)

        elif _object == Variables:
            _list = _object.query.filter(_object.user_id == user_id, _object.is_private == 0). \
                order_by(_object.timestamp.desc(), _object.id.desc()).limit(pagesize).offset(pagesize*(page-1)).all()
            count = _object.query.filter(_object.user_id == user_id, _object.is_private == 0). \
                order_by(_object.timestamp.desc(), _object.id.desc()).count()
        else:
            _list = _object.query.filter(_object.user_id == user_id). \
                order_by(_object.timestamp.desc(), _object.id.desc()).limit(pagesize).offset(pagesize*(page-1)).all()
            count = _object.query.filter(_object.user_id == user_id). \
                order_by(_object.timestamp.desc(), _object.id.desc()).count()
        all_to_dict(_list)

    else:
        _list, count = [{}], 0
    return jsonify({'list': _list, 'count': count})


def post_edit(_object, _id, _name, **kwargs):
    print('edit:::', _id, _name, kwargs)
    if not _id:
        __object = _object(**kwargs)
        db.session.add(__object)
        db.session.commit()
        return jsonify(msg='添加{}成功'.format(_name))
    __object = _object.query.get(_id)
    for kwarg in kwargs:
        setattr(__object, kwarg, kwargs[kwarg])
    db.session.commit()
    # app.logger.info('message:update case_group success, name: %s' % name)
    return jsonify(msg='编辑{}成功'.format(_name))


def post_del(_object, _name):
    __object = get_values('id')
    if isinstance(__object, list):
        for g in __object:
            _g = _object.query.get(g.get('id'))
            db.session.delete(_g)
        db.session.commit()
        return jsonify(msg='删除{}列表成功'.format(_name))
    o = _object.query.get(__object.get('id'))
    db.session.delete(o)
    db.session.commit()
    return jsonify(msg='删除{}成功'.format(_name))