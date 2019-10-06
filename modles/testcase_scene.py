
from . import BaseModel, db, User, CaseGroup


class TestCaseScene(BaseModel, db.Model):
    __tablename__ = 'testcase_scenes'
    description = db.Column(db.String(50))
    group_id = db.Column(db.Integer, db.ForeignKey(CaseGroup.id))
    is_model = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    testcases = db.relationship('TestCases', backref='testcase_scene')

    def __init__(self, name, group_id=1, description='', is_model=0, user_id=1):
        super().__init__(name)
        self.group_id = group_id
        self.description = description
        self.is_model = is_model
        self.user_id = user_id

    def __repr__(self):
        return "<TestCaseScene:%s,%s,%s, %s, %s, %s>" % (
            self.id, self.name, self.group_id, self.description, self.is_model, self.user_id)

    def to_json(self):
        return dict(id=self.id, name=self.name, group_id=self.group_id, description=self.description,
                    is_model=self.is_model, user_id=self.user_id)
