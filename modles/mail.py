# coding=utf-8
from . import BaseModel, db, User


class Mail(BaseModel, db.Model):
    __tablename__ = 'mail'
    subject = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    to_user_list = db.Column(db.String(50))
    email_method = db.Column(db.Integer)

    def __init__(self, name='', subject='', user_id=1,
                 to_user_list='', email_method=1):
        super().__init__(name)
        self.subject = subject
        self.to_user_list = to_user_list
        self.user_id = user_id
        self.email_method = email_method

    def to_dict(self):
        return dict(name=self.name, id=self.id, subject=self.subject, to_user_list=self.to_user_list,
                    email_method=self.email_method)
