from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    UserID = Column(Integer, primary_key=True)
    Name = Column(String(250), nullable=False)
    Email = Column(String(250), nullable=False)


class Category(Base):
    __tablename__ = 'category'

    CategoryID = Column(Integer, primary_key=True)
    Name = Column(String(250), nullable=False)


    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.Name,
            'id': self.CategoryID
        }


class Item(Base):
    __tablename__ = 'item'

    ItemID = Column(Integer, primary_key=True)
    Name = Column(String(80), nullable=False)
    Description = Column(String(250))
    Category_ID = Column(Integer, ForeignKey('category.CategoryID'))
    Category = relationship(Category)
    User_ID = Column(Integer, ForeignKey('user.UserID'))
    User = relationship(User)
    Created = Column(DateTime, server_default=func.now())

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.Name,
            'description': self.Description,
            'id': self.ItemID,
            'added': self.Created
        }


engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)