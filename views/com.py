from common import get_values, all_to_dict
from modles import Variables, db, TestCaseStartTimes
from flask import jsonify


def get_list(_object):
    search, user_id = get_values('search', 'user_id', post=False)
    print('search', search, user_id)
    if user_id:
        if _object == Variables:
            _list = _object.query.filter(_object.user_id == user_id, _object.is_private == 0). \
                order_by(_object.timestamp.desc()).all()
        elif _object == TestCaseStartTimes:
            _list = _object.query.filter(_object.name != "", _object.user_id == user_id).order_by(
                _object.timestamp.desc()).all()
        else:
            _list = _object.query.filter(_object.user_id == user_id). \
                order_by(_object.timestamp.desc()).all()
        all_to_dict(_list)
    else:
        _list = [{}]
    return jsonify({'list': _list})


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
            case_group = _object.query.get(g.get('id'))
            db.session.delete(case_group)
        db.session.commit()
        return jsonify(msg='删除{}列表成功'.format(_name))
    case_group = _object.query.get(__object.get('id'))
    db.session.delete(case_group)
    db.session.commit()
    return jsonify(msg='删除{}成功'.format(_name))