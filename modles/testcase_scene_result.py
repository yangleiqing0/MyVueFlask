
from . import BaseModel, db, TestCaseScene, TestCaseStartTimes


class TestCaseSceneResult(BaseModel, db.Model):

    scene_id = db.Column(db.Integer, db.ForeignKey(TestCaseScene.id))
    count = db.Column(db.Integer)
    result = db.Column(db.String(50))

    time_id = db.Column(db.Integer, db.ForeignKey(TestCaseStartTimes.id))

    scenes = db.relationship('TestCaseScene', backref='scene_result')
    start_time = db.relationship('TestCaseStartTimes', backref='time_scene_results')

    def __init__(self, scene_id, name, count,  result, time_id):
        super().__init__(name)
        self.scene_id = scene_id
        self.count = count
        self.result = result
        self.time_id = time_id

    def to_dict(self, children=''):
        return dict(id=self.id, name=self.name, scene_id=self.scene_id, count=self.count,
                    result=self.result, time_id=self.time_id, children=children)

