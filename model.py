from sqlalchemy import Column, String, create_engine, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('mysql+mysqlconnector://root:password@localhost:3306/test')
DBSession = sessionmaker(bind=engine)


class Post(Base):

    __tablename__ = "post"

    # post info
    originalId = Column(String(128), primary_key=True)
    createTime = Column(TIMESTAMP())
    doc_url = Column(String(256))
    title = Column(String(128))
    content = Column(String(256))
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
        self.__s.commit()

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

    bookId = Column(String(128), primary_key=True)
    share_url = Column(String(256))

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

    def query(self):
        raise NotImplementedError("to do")


# todo: implement DB query
