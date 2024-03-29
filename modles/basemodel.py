from . import datetime, db


class Base:
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, index=True)
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self):
        self.timestamp = datetime.now()

    def get_dict(self, *args):
        if args:
            return {col: getattr(self, col) for col in args}
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


class BaseModel(Base):
    name = db.Column(db.String(50), nullable=False)

    def __init__(self, name):
        super().__init__()
        self.name = name






