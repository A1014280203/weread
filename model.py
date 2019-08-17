from sqlalchemy import Column, String, create_engine, TIMESTAMP, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine("mysql+pymysql://root:password@node:port/database?charset=utf8")
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

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.__s = None
        self.refresh_session()

    def __del__(self):
        if self.__s:
            self.close_session()

    def refresh_session(self):
        self.__s = DBSession()

    def close_session(self):
        if self.__s:
            self.__s.close()
            self.__s = None

    def add(self, c: [dict, ]):
        """
        :param c: [{field: value}, ]
        :return:
        """
        if self.__s is None:
            self.refresh_session()
        for data in c:
            self.__s.add(Post(**data))

    def commit(self):
        try:
            self.__s.commit()
        except Exception:
            return False
        return True

    def __pre_check(self, data: dict):
        """

        :param data: {field: value}
        :return: True for pass
        """
        pass

    def query(self):
        raise NotImplementedError("to do")


class Book(Base):

    __tablename__ = "book"

    bid = Column(Integer(), autoincrement=True)
    bookId = Column(String(128), primary_key=True)
    share_url = Column(String(256))
    state = Column(Integer(), default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.__s = None
        self.refresh_session()

    def __del__(self):
        if self.__s:
            self.close_session()

    def refresh_session(self):
        self.__s = DBSession()

    def close_session(self):
        if self.__s:
            self.__s.close()
            self.__s = None

    def add(self, mp: dict):
        """
        :param mp: {field: value}
        :return:
        """
        if self.__s is None:
            self.refresh_session()
            self.__s.add(Book(**mp))

    def commit(self):
        self.__s.commit()

    def __pre_check(self, data: dict):
        """

        :param data: {field: value}
        :return: True for pass
        """
        pass

    def query_all(self):
        return self.__s.query(Book).all()

    def query_all_json(self):
        rows = self.query_all()
        mps = list()
        for row in rows:
            _mp = dict()
            _mp["bookId"] = row.bookId
            _mp["share_url"] = row.share_url
            mps.append(_mp)
        return mps
