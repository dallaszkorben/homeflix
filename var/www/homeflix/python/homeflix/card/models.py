"""
SQLAlchemy Models for HomeFlix Database
Defines all database tables as SQLAlchemy models for gradual migration
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DECIMAL, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Association tables for many-to-many relationships
card_genre_table = Table('Card_Genre', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_genre', Integer, ForeignKey('Genre.id'), primary_key=True)
)

card_theme_table = Table('Card_Theme', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_theme', Integer, ForeignKey('Theme.id'), primary_key=True)
)

card_sound_table = Table('Card_Sound', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_sound', Integer, ForeignKey('Language.id'), primary_key=True)
)

card_sub_table = Table('Card_Sub', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_sub', Integer, ForeignKey('Language.id'), primary_key=True)
)

card_origin_table = Table('Card_Origin', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_origin', Integer, ForeignKey('Country.id'), primary_key=True)
)

card_actor_table = Table('Card_Actor', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_actor', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_star_table = Table('Card_Star', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_star', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_voice_table = Table('Card_Voice', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_voice', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_director_table = Table('Card_Director', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_director', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_writer_table = Table('Card_Writer', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_writer', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_host_table = Table('Card_Host', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_host', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_guest_table = Table('Card_Guest', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_guest', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_interviewer_table = Table('Card_Interviewer', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_interviewer', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_interviewee_table = Table('Card_Interviewee', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_interviewee', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_presenter_table = Table('Card_Presenter', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_presenter', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_lecturer_table = Table('Card_Lecturer', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_lecturer', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_performer_table = Table('Card_Performer', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_performer', Integer, ForeignKey('Person.id'), primary_key=True)
)

card_reporter_table = Table('Card_Reporter', Base.metadata,
    Column('id_card', String, ForeignKey('Card.id'), primary_key=True),
    Column('id_reporter', Integer, ForeignKey('Person.id'), primary_key=True)
)

actor_role_table = Table('Actor_Role', Base.metadata,
    Column('id_actor', Integer, ForeignKey('Person.id'), primary_key=True),
    Column('id_role', Integer, ForeignKey('Role.id'), primary_key=True)
)

voice_role_table = Table('Voice_Role', Base.metadata,
    Column('id_voice', Integer, ForeignKey('Person.id'), primary_key=True),
    Column('id_role', Integer, ForeignKey('Role.id'), primary_key=True)
)

# Lookup Tables
class Category(Base):
    __tablename__ = 'Category'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    
    # Relationships
    cards = relationship("Card", back_populates="category")

class Genre(Base):
    __tablename__ = 'Genre'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    
    # Relationships
    cards = relationship("Card", secondary=card_genre_table, back_populates="genres")

class Theme(Base):
    __tablename__ = 'Theme'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    
    # Relationships
    cards = relationship("Card", secondary=card_theme_table, back_populates="themes")

class Language(Base):
    __tablename__ = 'Language'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    
    # Relationships
    users = relationship("User", back_populates="language")
    cards_orig = relationship("Card", back_populates="title_orig_language")
    text_cards = relationship("TextCardLang", back_populates="language")
    sound_cards = relationship("Card", secondary=card_sound_table, back_populates="sounds")
    sub_cards = relationship("Card", secondary=card_sub_table, back_populates="subs")

class Country(Base):
    __tablename__ = 'Country'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    
    # Relationships
    cards = relationship("Card", secondary=card_origin_table, back_populates="origins")

class MediaType(Base):
    __tablename__ = 'MediaType'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    
    # Relationships
    card_media = relationship("CardMedia", back_populates="media_type")

class Person(Base):
    __tablename__ = 'Person'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    
    # Relationships
    actor_cards = relationship("Card", secondary=card_actor_table, back_populates="actors")
    star_cards = relationship("Card", secondary=card_star_table, back_populates="stars")
    voice_cards = relationship("Card", secondary=card_voice_table, back_populates="voices")
    director_cards = relationship("Card", secondary=card_director_table, back_populates="directors")
    writer_cards = relationship("Card", secondary=card_writer_table, back_populates="writers")
    host_cards = relationship("Card", secondary=card_host_table, back_populates="hosts")
    guest_cards = relationship("Card", secondary=card_guest_table, back_populates="guests")
    interviewer_cards = relationship("Card", secondary=card_interviewer_table, back_populates="interviewers")
    interviewee_cards = relationship("Card", secondary=card_interviewee_table, back_populates="interviewees")
    presenter_cards = relationship("Card", secondary=card_presenter_table, back_populates="presenters")
    lecturer_cards = relationship("Card", secondary=card_lecturer_table, back_populates="lecturers")
    performer_cards = relationship("Card", secondary=card_performer_table, back_populates="performers")
    reporter_cards = relationship("Card", secondary=card_reporter_table, back_populates="reporters")
    actor_roles = relationship("Role", secondary=actor_role_table, back_populates="actors")
    voice_roles = relationship("Role", secondary=voice_role_table, back_populates="voices")

# Core Tables
class User(Base):
    __tablename__ = 'User'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, nullable=False)
    id_language = Column(Integer, ForeignKey('Language.id'), nullable=False)
    descriptor_color = Column(String, nullable=False)
    show_original_title = Column(Boolean, nullable=False)
    show_lyrics_anyway = Column(Boolean, nullable=False)
    show_storyline_anyway = Column(Boolean, nullable=False)
    play_continuously = Column(Boolean, nullable=False)
    history_days = Column(Integer, nullable=False)
    created_epoch = Column(Integer, nullable=False)
    
    # Relationships
    language = relationship("Language", back_populates="users")
    history = relationship("History", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    tags = relationship("Tag", back_populates="user")

class Card(Base):
    __tablename__ = 'Card'
    
    id = Column(String, primary_key=True)
    id_title_orig = Column(Integer, ForeignKey('Language.id'), nullable=False)
    id_category = Column(Integer, ForeignKey('Category.id'), nullable=False)
    isappendix = Column(Boolean, nullable=False)
    show = Column(Boolean, nullable=False)
    download = Column(Boolean, nullable=False)
    decade = Column(String)
    date = Column(String)
    length = Column(String)
    full_time = Column(DECIMAL(10, 2))
    net_start_time = Column(DECIMAL(10, 2))
    net_stop_time = Column(DECIMAL(10, 2))
    source_path = Column(String, nullable=False)
    basename = Column(String, nullable=False)
    sequence = Column(Integer)
    id_higher_card = Column(String, ForeignKey('Card.id'))
    level = Column(String)
    title_on_thumbnail = Column(Boolean, nullable=False)
    title_show_sequence = Column(String, nullable=False)
    
    # Relationships
    category = relationship("Category", back_populates="cards")
    title_orig_language = relationship("Language", back_populates="cards_orig")
    parent_card = relationship("Card", remote_side=[id], back_populates="child_cards")
    child_cards = relationship("Card", back_populates="parent_card")
    
    # Many-to-many relationships
    genres = relationship("Genre", secondary=card_genre_table, back_populates="cards")
    themes = relationship("Theme", secondary=card_theme_table, back_populates="cards")
    sounds = relationship("Language", secondary=card_sound_table, back_populates="sound_cards")
    subs = relationship("Language", secondary=card_sub_table, back_populates="sub_cards")
    origins = relationship("Country", secondary=card_origin_table, back_populates="cards")
    actors = relationship("Person", secondary=card_actor_table, back_populates="actor_cards")
    stars = relationship("Person", secondary=card_star_table, back_populates="star_cards")
    voices = relationship("Person", secondary=card_voice_table, back_populates="voice_cards")
    directors = relationship("Person", secondary=card_director_table, back_populates="director_cards")
    writers = relationship("Person", secondary=card_writer_table, back_populates="writer_cards")
    hosts = relationship("Person", secondary=card_host_table, back_populates="host_cards")
    guests = relationship("Person", secondary=card_guest_table, back_populates="guest_cards")
    interviewers = relationship("Person", secondary=card_interviewer_table, back_populates="interviewer_cards")
    interviewees = relationship("Person", secondary=card_interviewee_table, back_populates="interviewee_cards")
    presenters = relationship("Person", secondary=card_presenter_table, back_populates="presenter_cards")
    lecturers = relationship("Person", secondary=card_lecturer_table, back_populates="lecturer_cards")
    performers = relationship("Person", secondary=card_performer_table, back_populates="performer_cards")
    reporters = relationship("Person", secondary=card_reporter_table, back_populates="reporter_cards")
    
    # One-to-many relationships
    text_cards = relationship("TextCardLang", back_populates="card")
    card_media = relationship("CardMedia", back_populates="card")
    roles = relationship("Role", back_populates="card")
    history = relationship("History", back_populates="card")
    ratings = relationship("Rating", back_populates="card")
    tags = relationship("Tag", back_populates="card")

class TextCardLang(Base):
    __tablename__ = 'Text_Card_Lang'
    
    text = Column(Text, nullable=False)
    id_language = Column(Integer, ForeignKey('Language.id'), nullable=False, primary_key=True)
    id_card = Column(String, ForeignKey('Card.id'), nullable=False, primary_key=True)
    type = Column(String, nullable=False, primary_key=True)
    
    # Relationships
    language = relationship("Language", back_populates="text_cards")
    card = relationship("Card", back_populates="text_cards")

class CardMedia(Base):
    __tablename__ = 'Card_Media'
    
    name = Column(String, nullable=False, primary_key=True)
    id_card = Column(String, ForeignKey('Card.id'), nullable=False, primary_key=True)
    id_mediatype = Column(Integer, ForeignKey('MediaType.id'), nullable=False, primary_key=True)
    
    # Relationships
    card = relationship("Card", back_populates="card_media")
    media_type = relationship("MediaType", back_populates="card_media")

class Role(Base):
    __tablename__ = 'Role'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_card = Column(String, ForeignKey('Card.id'), nullable=False)
    name = Column(String, nullable=False)
    
    # Relationships
    card = relationship("Card", back_populates="roles")
    actors = relationship("Person", secondary=actor_role_table, back_populates="actor_roles")
    voices = relationship("Person", secondary=voice_role_table, back_populates="voice_roles")

# User Interaction Tables
class History(Base):
    __tablename__ = 'History'
    
    start_epoch = Column(Integer, nullable=False, primary_key=True)
    recent_epoch = Column(Integer, nullable=False)
    recent_position = Column(DECIMAL(10, 2), nullable=False)
    id_card = Column(String, ForeignKey('Card.id'), nullable=False, primary_key=True)
    id_user = Column(Integer, ForeignKey('User.id'), nullable=False, primary_key=True)
    
    # Relationships
    card = relationship("Card", back_populates="history")
    user = relationship("User", back_populates="history")

class Rating(Base):
    __tablename__ = 'Rating'
    
    id_card = Column(String, ForeignKey('Card.id'), nullable=False, primary_key=True)
    id_user = Column(Integer, ForeignKey('User.id'), nullable=False, primary_key=True)
    rate = Column(Integer)
    skip_continuous_play = Column(Boolean, nullable=False)
    
    # Relationships
    card = relationship("Card", back_populates="ratings")
    user = relationship("User", back_populates="ratings")

class Tag(Base):
    __tablename__ = 'Tag'
    
    id_card = Column(String, ForeignKey('Card.id'), nullable=False, primary_key=True)
    id_user = Column(Integer, ForeignKey('User.id'), nullable=False, primary_key=True)
    name = Column(String, nullable=False, primary_key=True)
    
    # Relationships
    card = relationship("Card", back_populates="tags")
    user = relationship("User", back_populates="tags")