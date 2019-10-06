from flask import request


def get_values(*args, post=True):
    print('args:', args)
    arg_list = []
    if post:
        for arg in args:
            arg_list.append(request.get_json().get(arg))
        if len(arg_list) == 1:
            arg_list = arg_list[0]
    else:
        for arg in args:
            arg_list.append(request.values.get(arg, default=''))
        if len(arg_list) == 1:
            arg_list = arg_list[0]
    return arg_list
