from sqlalchemy import Column, String, create_engine, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()
engine = create_engine("mysql+pymysql://user:password@ip:port/weread?charset=utf8")
DBSession = sessionmaker(bind=engine)


class Post(Base):

    __tablename__ = "post"

    # post info
    pid = Column(Integer(), autoincrement=True, index=True, unique=True)
    originalId = Column(String(128), primary_key=True)
    createTime = Column(Integer())
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

    bid = Column(Integer(), primary_key=True)
    bookId = Column(String(128))
    share_url = Column(String(256))
    state = Column(Integer(), default=0)
    last_update = Column(Integer(), default=0)


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

    def update(self, cls, col, new_d):
        if self.__s is None:
            self.refresh_session()
        self.__s.query(cls).filter(getattr(cls, col) == new_d[col]).update(new_d)

    def query_all(self, cls):
        return self.__s.query(cls).all()

    def commit(self):
        """
        documented as bad form
        :return:
        """
        try:
            self.__s.commit()
        except Exception as e:
            self.__s.rollback()
            return False
        return True

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
