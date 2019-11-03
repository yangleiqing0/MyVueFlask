#coding=utf-8
from . import BaseModel, datetime, db, Mail, User, TestCases, TestCaseScene


class Job(BaseModel, db.Model):
    __tablename__ = 'job'
    testcases = db.Column(db.String(50))
    testcase_scenes = db.Column(db.String(50))
    description = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    triggers = db.Column(db.String(50))
    cron = db.Column(db.String(50))
    is_start = db.Column(db.Integer)
    mail_id = db.Column(db.Integer, db.ForeignKey(Mail.id))

    def __init__(self, testcases='', testcase_scenes='',  description='', user_id=1,
                 triggers='cron', cron='', is_start=0, mail_id=1):
        self.name = '任务' + str(datetime.now())[:19]
        super().__init__(self.name)
        self.testcases = testcases
        self.testcase_scenes = testcase_scenes
        self.description = description
        self.user_id = user_id
        self.triggers = triggers
        self.cron = cron
        self.is_start = is_start
        self.mail_id = mail_id

    def to_dict(self):
        case_list, scene_list = [], []
        if len(self.testcases) > 0:
            for case_id in eval(self.testcases):
                case_list.append(TestCases.query.get(case_id).get_dict('id', 'name'))
        if len(self.testcase_scenes) > 0:
            for scene_id in eval(self.testcase_scenes):
                scene_list.append(TestCaseScene.query.get(scene_id).get_dict('id', 'name'))
        return dict(id=self.id, name=self.name, description=self.description, triggers=self.triggers, cron=self.cron,
                    is_start=self.is_start, mail_id=self.mail_id, testcases=case_list, testcase_scenes=scene_list)
