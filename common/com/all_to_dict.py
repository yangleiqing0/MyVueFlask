from modles import TestCaseScene


def all_to_dict(objects, *args, wait=False, model=None):
    for i in range(len(objects)):
        if wait:
            if objects[i].wait:
                print('dict', objects[i].wait[0].to_dict())
                objects[i] = objects[i].to_dict(objects[i].wait[0].to_dict())
            else:
                objects[i] = objects[i].to_dict()
        else:
            if model == TestCaseScene:
                if objects[i].testcases:
                    case_list = []
                    for case in objects[i].testcases:
                        case_list.append(case.to_dict())
                    objects[i] = objects[i].to_dict(case_list)
                else:
                    objects[i] = objects[i].to_dict()
            else:
                objects[i] = objects[i].to_dict()
    if args:
        object_list = []
        for arg in args:
            _arg = arg
            del arg
            arg = []
            for a in range(len(_arg)):
                arg.append(_arg[a].to_dict())
            object_list.append(arg)
        return object_list


def to_dict(li):
    for r in range(len(li)):
        li[r] = li[r].get_dict()


def scene_result_dict(scene_list):
    for i in range(len(scene_list)):
        if scene_list[i].test_cases:
            case_result_list = []
            for case in scene_list[i].test_cases:
                case_result_list.append(case.get_dict())
            scene_list[i] = scene_list[i].to_dict(case_result_list)
        else:
            scene_list[i] = scene_list[i].to_dict()