from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

Base = declarative_base()

"""
one-to-one
one-to-many - many-to-one
many-to-many
"""

class Entity:
    id = Column(Integer, primary_key=True, autoincrement=True)


class MixIdUrl(Entity):
    url = Column(String, nullable=False, unique=True)


tag_post = Table(
    'tag_post',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)


class Post(Base, MixIdUrl):
    __tablename__ = 'post'
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey('author.id'), nullable=False)
    author = relationship('Author')
    published_date = Column(DateTime)
    picture_url = Column(String)
    tags = relationship('Tag', secondary=tag_post)
    comments = relationship('Comment')


class Author(Base, MixIdUrl):
    __tablename__ = 'author'
    name = Column(String, nullable=False)
    posts = relationship('Post')
    comments = relationship('Comment')


class Tag(Base, MixIdUrl):
    __tablename__ = 'tag'
    name = Column(String, nullable=False)
    posts = relationship('Post', secondary=tag_post)


class Comment(Base, Entity):
    __tablename__ = 'comment'
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('author.id'), nullable=False)
    author = relationship('Author')
    post = relationship('Post')
    text = Column(String)
