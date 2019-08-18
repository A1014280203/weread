from sqlalchemy import Column, String, create_engine, TIMESTAMP, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()
engine = create_engine("mysql+pymysql://root:AbLvx5gOcUw02BG@49.235.9.27:3306/weread?charset=utf8")
DBSession = sessionmaker(bind=engine)


class Post(Base):

    __tablename__ = "post"

    # post info
    pid = Column(Integer(), autoincrement=True)
    originalId = Column(String(128), primary_key=True)
    createTime = Column(TIMESTAMP())
    doc_url = Column(String(256))
    title = Column(String(128))
    content = Column(String(256))
    state = Column(Integer(), default=0)
    # mp info
    mp_name = Column(String(64))
    avatar = Column(String(256))
    bookId = Column(String(128))


class Book(Base):

    __tablename__ = "book"

    bid = Column(Integer(), autoincrement=True)
    bookId = Column(String(128), primary_key=True)
    share_url = Column(String(256))
    state = Column(Integer(), default=0)
    last_update = Column(TIMESTAMP())


class DBC(object):

    def __init__(self):
        self.__s = None
        self.refresh_session()

    def __del__(self):
        self.close_session()

    def refresh_session(self):
        self.__s = DBSession()

    def close_session(self):
        if self.__s:
            self.__s.close()
            self.__s = None

    def add(self, obj):
        if self.__s is None:
            self.refresh_session()
        self.__s.add(obj)

    def __pre_check(self, data: dict):
        """

        :param data: {field: value}
        :return: True for pass
        """
        pass

    def commit(self):
        try:
            self.__s.commit()
        except Exception as e:
            return False
        return True

    def query_all(self, cls):
        return self.__s.query(cls).all()

    @staticmethod
    def orm2dict(rows: list):
        """
        :param rows: must be iterable
        :return:
        """
        if not len(rows):
            return rows
        cols = [x.name for x in rows[0].__mapper__.columns]
        data = []
        for row in rows:
            _d = {name: getattr(row, name) for name in cols}
            data.append(_d)
        return data

    def query_all_pretty(self, cls):
        rows = self.query_all(cls)
        return self.orm2dict(rows)
