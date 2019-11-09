import xlsxwriter
import os
from flask import session
from . import cdb, AnalysisParams
from modles import db, TestCaseStartTimes, TestCaseScene, TestCaseSceneResult, CaseGroup, RequestHeaders
from config.app_config import TESTCASE_XLSX_PATH


def test_report(testcase_time_id, allocation, testcase_scene_list):
    data = {'testcase_scene': []}
    testcase_scene_count_dict = {}
    for testcase_scene in testcase_scene_list:
        testcase_scene_count_dict.update({'testcase_scene_' + str(testcase_scene.name): testcase_scene})

    testcase_time = TestCaseStartTimes.query.get(testcase_time_id)
    testcase_scene_counts_sql = 'select testcase_scenes.name, count(*),testcase_scenes.id from test_case_start_times,test_case_result,testcases,testcase_scenes where test_case_start_times.id=' \
    'test_case_result.testcase_start_time_id and testcases.id=test_case_result.testcase_id and testcases.testcase_scene_id=testcase_scenes.id ' \
    'and test_case_start_times.id=%s and testcases.testcase_scene_id is not Null group by testcases.testcase_scene_id' % testcase_time_id

    testcase_scene_counts = cdb().query_db(testcase_scene_counts_sql)
    print('testcase_scene_counts count:', testcase_scene_counts)
    for testcase_scene_count in testcase_scene_counts:
        testcase_scene_count_dict.update({testcase_scene_count[0]: [testcase_scene_count[1], testcase_scene_count[2]]})

    testcase_results_query_sql = 'select testcases.name,testcases.url,testcases.method,testcases.data,test_case_result.response_body,' \
                                 ' testcases.hope_result,test_case_result.old_sql_value,test_case_result.new_sql_value,' \
                                 'test_case_result.testcase_test_result,test_case_result.old_sql_value_result,test_case_result.new_sql_value_result,' \
                                 'testcases.old_sql_hope_result,testcases.new_sql_hope_result,test_case_result.result,' \
                                 'testcases.testcase_scene_id' \
                                 ' from testcases,test_case_result where testcases.id=test_case_result.testcase_id ' \
                                 'and test_case_result.testcase_start_time_id=%s' % testcase_time_id
    testcase_results = cdb().query_db(testcase_results_query_sql)
    for testcase_result in testcase_results:
        if testcase_result[14]:
            scene = TestCaseScene.query.get(testcase_result[14])
            testcase_scene_name = scene.name
            testcase_scene_id = scene.id
        else:
            testcase_scene_name = ''
            testcase_scene_id = ''
        t_name = AnalysisParams().analysis_params(testcase_result[0])
        t_url = AnalysisParams().analysis_params(testcase_result[1])
        t_method = testcase_result[2]
        t_request_body = AnalysisParams().analysis_params(testcase_result[3])
        t_response_body = testcase_result[4]
        t_hope = AnalysisParams().analysis_params(testcase_result[5])
        old_database_value = testcase_result[6]
        new_database_value = testcase_result[7]
        t_result = testcase_result[13]
        # print('testcase_result: ', testcase_result)
        content = {"t_name": t_name,
                   "t_url": t_url,
                   "t_method": t_method,
                   "t_request_body": t_request_body,
                   "t_hope": t_hope,
                   "t_response_body": t_response_body,
                   "old_database_value": old_database_value,
                   "new_database_value": new_database_value,
                   "t_result": testcase_result[8],
                   "t_old_sql_value_result": testcase_result[9],
                   "t_new_sql_value_result": testcase_result[10],
                   "t_testcase_scene": testcase_scene_name,
                   "t_testcase_result": t_result,
                   "t_old_sql_hope": AnalysisParams().analysis_params(testcase_result[11]),
                   "t_new_sql_hope": AnalysisParams().analysis_params(testcase_result[12])
                   }
        if testcase_scene_id:
            if data.get('testcase_scene_%s' % testcase_scene_id):
                data['testcase_scene_%s' % testcase_scene_id].append(content)
            else:
                data.update({'testcase_scene_%s' % testcase_scene_id: [content, ]})
        else:
            data['testcase_scene'].append(content)
        
    content_list = []
    for data_ in data:
        if 'testcase_scene_' in data_:
            content_list += data[data_][::-1]
    content_list = content_list + data['testcase_scene'][::-1]

    from config.app_config import project_path
    filename = os.path.join(project_path, testcase_time.filename)
    data_title = {"test_name": allocation.test_name, "test_version": allocation.zdbm_version, "test_pl": allocation.test_pl, "test_net": allocation.test_net}
    data_re = {"test_sum": allocation.test_sum, "test_success": allocation.test_success, "test_failed": allocation.fail_sum,
               "test_date": allocation.time_strftime}
    r = Report()
    # print("data_re", data_title, data_re, allocation.time_strftime, filename)
    if allocation.test_success == 0:
        score = 0
    else:
        score = int(allocation.test_success * 100 / allocation.test_sum)
    r.init(data_title, data_re, score, title_name=allocation.title_name, filename=filename)
    r.test_detail(content_list, len(content_list), len(content_list), testcase_scene_count_dict, testcase_time_id)


class Report:

    def get_format(self, wd, option):
        return wd.add_format(option)
    # 设置居中

    def get_format_center(self, wb, num=1, color='black'):
        return wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': num, 'text_wrap': 1, 'color': color})

    def set_border_(self, wb, num=1):
        return wb.add_format({}).set_border(num)
    # 写数据
    
    def write_center(self, worksheet, cl, data, wb, color='black'):
        return worksheet.write(cl, data, self.get_format_center(wb, color=color))

    def init(self, data, data1, score, filename, title_name):
        print(filename)
        self.workbook = xlsxwriter.Workbook(filename)

        # print(self.workbook)
        self.worksheet = self.workbook.add_worksheet("%s总况" % title_name)
        self.worksheet2 = self.workbook.add_worksheet("%s详情" % title_name)
        # 设置列行的宽高
        self.worksheet.set_column("A:A", 15)
        self.worksheet.set_column("B:B", 20)
        self.worksheet.set_column("C:C", 20)
        self.worksheet.set_column("D:D", 20)
        self.worksheet.set_column("E:E", 20)
        self.worksheet.set_column("F:F", 20)
        self.worksheet.set_column("F:F", 20)
        self.worksheet.set_row(1, 30)
        self.worksheet.set_row(2, 30)
        self.worksheet.set_row(3, 30)
        self.worksheet.set_row(4, 30)
        self.worksheet.set_row(5, 30)
        self.worksheet.set_row(6, 30)

        define_format_H1 = self.get_format(self.workbook, {'bold': True, 'font_size': 18})
        define_format_H2 = self.get_format(self.workbook, {'bold': True, 'font_size': 14})
        define_format_H1.set_border(1)

        define_format_H2.set_border(1)
        define_format_H1.set_align("center")
        define_format_H2.set_align("center")
        define_format_H2.set_bg_color("#70DB93")
        define_format_H2.set_color("#ffffff")
        # Create a new Chart object.

        self.worksheet.merge_range('A1:F1', '%s总概况' % title_name, define_format_H1)
        self.worksheet.merge_range('A2:F2', '%s概括' % title_name, define_format_H2)
        self.worksheet.merge_range('A3:A6', '项目图片', self.get_format_center(self.workbook))

        self.write_center(self.worksheet, "B3", '项目名称', self.workbook)
        self.write_center(self.worksheet, "B4", '项目版本', self.workbook)
        self.write_center(self.worksheet, "B5", '运行环境', self.workbook)
        self.write_center(self.worksheet, "B6", '测试网络', self.workbook)

        self.write_center(self.worksheet, "C3", data['test_name'], self.workbook)
        self.write_center(self.worksheet, "C4", data['test_version'], self.workbook)
        self.write_center(self.worksheet, "C5", data['test_pl'], self.workbook)
        self.write_center(self.worksheet, "C6", data['test_net'], self.workbook)

        self.write_center(self.worksheet, "D3", "用例总数", self.workbook)
        self.write_center(self.worksheet, "D4", "通过总数", self.workbook)
        self.write_center(self.worksheet, "D5", "失败总数", self.workbook)
        self.write_center(self.worksheet, "D6", "测试时间", self.workbook)

        self.write_center(self.worksheet, "E3", data1['test_sum'], self.workbook)
        self.write_center(self.worksheet, "E4", data1['test_success'], self.workbook)
        self.write_center(self.worksheet, "E5", data1['test_failed'], self.workbook)
        self.write_center(self.worksheet, "E6", data1['test_date'], self.workbook)

        self.write_center(self.worksheet, "F3", "分数", self.workbook)

        self.worksheet.merge_range('F4:F6', '%s'% score, self.get_format_center(self.workbook))

        self.pie(self.workbook, self.worksheet, title_name)

     # 生成饼形图
    def pie(self, wob, wos, title_name):
        chart1 = wob.add_chart({'type': 'pie'})
        chart1.add_series({
            'name': '%s统计' % title_name,
            'categories': '=%s总况!$D$4:$D$5' % title_name,
            'values': '=%s总况!$E$4:$E$5' % title_name,
        })
        chart1.set_title({'name': '%s统计' % title_name})
        chart1.set_style(10)
        wos.insert_chart('A9', chart1, {'x_offset': 25, 'y_offset': 10})

    def test_detail(self, data, tmp, row, testcase_scene_count_dict, testcase_time_id):
        print('data:', data)
        # 设置列行的宽高
        self.worksheet2.set_column("A:A", 16)
        self.worksheet2.set_column("B:B", 16)
        self.worksheet2.set_column("C:C", 8)
        self.worksheet2.set_column("D:D", 30)
        self.worksheet2.set_column("E:E", 35)
        self.worksheet2.set_column("F:F", 10)
        self.worksheet2.set_column("G:G", 11)
        self.worksheet2.set_column("H:H", 11)
        self.worksheet2.set_column("I:I", 11)
        self.worksheet2.set_column("J:J", 10)
        self.worksheet2.set_column("K:K", 10)
        self.worksheet2.set_column("L:L", 10)
        self.worksheet2.set_column("M:M", 10)
        self.worksheet2.set_column("N:N", 10)
        self.worksheet2.set_column("O:O", 10)
        self.worksheet2.set_column("P:P", 10)
        for i in range(1, (row+2)):
            self.worksheet2.set_row(i, 40)
        self.worksheet2.merge_range('A1:P1', '测试详情', self.get_format(self.workbook, {'bold': True, 'font_size': 18 ,'align': 'center','valign': 'vcenter','bg_color': '#70DB93', 'font_color': '#ffffff'}))
        self.write_center(self.worksheet2, "A2", '用例名称', self.workbook)
        self.write_center(self.worksheet2, "B2", '请求接口', self.workbook)
        self.write_center(self.worksheet2, "C2", '请求方法', self.workbook)
        self.write_center(self.worksheet2, "D2", '请求报文', self.workbook)
        self.write_center(self.worksheet2, "E2", '响应报文', self.workbook)
        self.write_center(self.worksheet2, "F2", '响应预期', self.workbook)
        self.write_center(self.worksheet2, "G2", '响应验证', self.workbook)
        self.write_center(self.worksheet2, "H2", '数据库原值', self.workbook)
        self.write_center(self.worksheet2, "I2", '原值预期', self.workbook)
        self.write_center(self.worksheet2, "J2", '原值验证', self.workbook)
        self.write_center(self.worksheet2, "K2", '数据库现值', self.workbook)
        self.write_center(self.worksheet2, "L2", '现值预期', self.workbook)
        self.write_center(self.worksheet2, "M2", '现值验证', self.workbook)
        self.write_center(self.worksheet2, "N2", '测试结果', self.workbook)
        self.write_center(self.worksheet2, "O2", '场景归属', self.workbook)
        self.write_center(self.worksheet2, "P2", '场景结果', self.workbook)

        temp = tmp+2

        for item in data:
            self.write_center(self.worksheet2,"A"+str(temp), item["t_name"], self.workbook)
            self.write_center(self.worksheet2,"B"+str(temp), item["t_url"], self.workbook)
            self.write_center(self.worksheet2,"C"+str(temp), item["t_method"], self.workbook)
            self.write_center(self.worksheet2,"D"+str(temp), item["t_request_body"], self.workbook)
            self.write_center(self.worksheet2,"E"+str(temp), item["t_response_body"], self.workbook)
            self.write_center(self.worksheet2,"F"+str(temp), item["t_hope"], self.workbook)
            self.write_center(self.worksheet2,"G"+str(temp), item["t_result"], self.workbook)
            self.write_center(self.worksheet2, "H" + str(temp), item["old_database_value"], self.workbook)
            self.write_center(self.worksheet2, "I" + str(temp), item["t_old_sql_hope"], self.workbook)
            self.write_center(self.worksheet2, "J" + str(temp), item["t_old_sql_value_result"], self.workbook)
            self.write_center(self.worksheet2, "K" + str(temp), item["new_database_value"], self.workbook)
            self.write_center(self.worksheet2, "L" + str(temp), item["t_new_sql_hope"], self.workbook)
            self.write_center(self.worksheet2, "M" + str(temp), item["t_new_sql_value_result"], self.workbook)
            if item["t_testcase_result"] != '测试成功':
                self.write_center(self.worksheet2, "N" + str(temp), item["t_testcase_result"], self.workbook, color='red')
            else:
                self.write_center(self.worksheet2, "N" + str(temp), item["t_testcase_result"], self.workbook)
            if item['t_testcase_scene']:
                if testcase_scene_count_dict.get(item['t_testcase_scene'], None):
                    testcase_scene_count = testcase_scene_count_dict[item['t_testcase_scene']][0]
                    testcase_scene = testcase_scene_count_dict['testcase_scene_' + item['t_testcase_scene']]
                    print('testcase_scene_count:', testcase_scene_count, testcase_scene)
                    if testcase_scene_count == 1:
                        self.write_center(self.worksheet2, "O" + str(temp), item["t_testcase_scene"], self.workbook)
                    else:
                        self.worksheet2.merge_range('%s:%s' % ("O" + str(temp - testcase_scene_count + 1), "O" + str(temp)),
                                                     item["t_testcase_scene"], self.get_format_center(self.workbook))
                    if TestCaseSceneResult.query.filter(TestCaseSceneResult.time_id == testcase_time_id,
                                                        TestCaseSceneResult.scene_id == testcase_scene_count_dict[item['t_testcase_scene']][1]).count():
                        pass
                    else:
                        testcase_scene_result = TestCaseSceneResult(testcase_scene_count_dict[item['t_testcase_scene']][1],
                                                                    item['t_testcase_scene'],
                                                                    testcase_scene_count, testcase_scene.result, testcase_time_id)
                        db.session.add(testcase_scene_result)
                    if testcase_scene.result != '测试成功':
                        if testcase_scene_count == 1:
                            self.write_center(self.worksheet2, "P" + str(temp), testcase_scene.result,
                                              self.workbook, color='red')
                        else:
                            self.worksheet2.merge_range('%s:%s' % ("P" + str(temp - testcase_scene_count + 1), "P" + str(temp)),
                                 testcase_scene.result, self.get_format_center(self.workbook,  color='red'))
                    else:
                        if testcase_scene_count == 1:
                            self.write_center(self.worksheet2, "P" + str(temp), testcase_scene.result,
                                              self.workbook)
                        else:
                            self.worksheet2.merge_range('%s:%s' % ("P" + str(temp - testcase_scene_count + 1), "P" + str(temp)),
                                testcase_scene.result, self.get_format_center(self.workbook))
                    testcase_scene_count_dict.pop(item['t_testcase_scene'])
            else:
                self.write_center(self.worksheet2, "O" + str(temp), item["t_testcase_scene"], self.workbook)
                if item["t_testcase_result"] != "测试成功":
                    self.write_center(self.worksheet2, "P" + str(temp), "测试失败",
                                      self.workbook, color='red')
                else:
                    self.write_center(self.worksheet2, "P" + str(temp), item["t_testcase_result"],
                                      self.workbook)

            temp = temp-1
        db.session.commit()

        self.worksheet.hide_gridlines(2)    # 隐藏网格线
        self.worksheet2.hide_gridlines(2)   # 隐藏网格线

        # self.worksheet2.freeze_panes(2, 16)  # 冻结首2行
        self.worksheet2.autofilter('A2:P2')  # 设置自动筛选

    def __del__(self):
        self.workbook.close()


class WriterXlsx:

    def __init__(self, name, data, method="download"):
        self.name = name
        self.method = method
        self.data = data
        self.workbook = self.worksheet = None

    @staticmethod
    def get_format(workbook, option):
        return workbook.add_format(option)

    @staticmethod
    def add_format(workbook, num=1, color='black'):
        return workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': num,
                                    'text_wrap': 1, 'color': color})

    @staticmethod
    def write_center(worksheet, colum, data, workbook, color='black'):
        return worksheet.write(colum, data, WriterXlsx.add_format(workbook, color=color))

    def open_xlsx(self):

        dir_path = os.path.join(session.get('app_rootpath'), TESTCASE_XLSX_PATH + self.method)
        xlsx_name = self.name + '.xlsx'
        path = dir_path + '/' + xlsx_name
        print('path:', path)
        self.workbook = xlsxwriter.Workbook(path)
        self.write_xlsx()
        return dir_path, xlsx_name

    def write_xlsx(self):
        self.worksheet = self.workbook.add_worksheet('测试用例列表')
        self.worksheet.set_column("A:A", 8)
        self.worksheet.set_column("B:B", 25)
        self.worksheet.set_column("C:C", 30)
        self.worksheet.set_column("D:D", 8)
        self.worksheet.set_column("E:E", 35)
        self.worksheet.set_column("F:F", 50)
        self.worksheet.set_column("G:G", 15)
        self.worksheet.set_column("H:H", 15)
        self.worksheet.set_column("I:I", 15)
        self.worksheet.set_column("J:J", 20)

        row = len(self.data)
        for i in range(1, (row + 2)):
            self.worksheet.set_row(i, 40)
        self.worksheet.merge_range('A1:J1', '测试用例列表', self.get_format(self.workbook,
                                                                     {'bold': True, 'font_size': 18, 'align': 'center',
                                                                      'valign': 'vcenter', 'bg_color': '#70DB93',
                                                                      'font_color': '#ffffff'}))
        self.write_center(self.worksheet, "A2", '用例ID', self.workbook)
        self.write_center(self.worksheet, "B2", '用例名称', self.workbook)
        self.write_center(self.worksheet, "C2", '请求接口', self.workbook)
        self.write_center(self.worksheet, "D2", '请求方法', self.workbook)
        self.write_center(self.worksheet, "E2", '请求头部', self.workbook)
        self.write_center(self.worksheet, "F2", '请求报文', self.workbook)
        self.write_center(self.worksheet, "G2", '响应预期', self.workbook)
        self.write_center(self.worksheet, "H2", '注册变量', self.workbook)
        self.write_center(self.worksheet, "I2", '注册规则', self.workbook)
        self.write_center(self.worksheet, "J2", '用例分组', self.workbook)

        temp = 3

        for item in self.data:
            if item.group_id:
                group_name = CaseGroup.query.get(item.group_id).name
            else:
                group_name = ''
            request_headers = RequestHeaders.query.get(item.request_headers_id).value
            self.write_center(self.worksheet, "A" + str(temp), item.id, self.workbook)
            self.write_center(self.worksheet, "B" + str(temp), item.name, self.workbook)
            self.write_center(self.worksheet, "C" + str(temp), item.url, self.workbook)
            self.write_center(self.worksheet, "D" + str(temp), item.method, self.workbook)
            self.write_center(self.worksheet, "E" + str(temp), request_headers, self.workbook)
            self.write_center(self.worksheet, "F" + str(temp), item.data, self.workbook)
            self.write_center(self.worksheet, "G" + str(temp), item.hope_result, self.workbook)
            self.write_center(self.worksheet, "H" + str(temp), item.regist_variable, self.workbook)
            self.write_center(self.worksheet, "I" + str(temp), item.regular, self.workbook)
            self.write_center(self.worksheet, "J" + str(temp), group_name, self.workbook)
            temp = temp + 1

    def __del__(self):
        self.workbook.close()
