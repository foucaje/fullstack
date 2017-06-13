from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setup_database import Base, Category, Item, User

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()



Category1 = Category(Name='Shirts')
session.add(Category1)
session.commit()

Category2 = Category(Name='Jeans')
session.add(Category2)
session.commit()

Category3 = Category(Name='Shoes')
session.add(Category3)
session.commit()

Category4 = Category(Name='Other Stuff')
session.add(Category4)
session.commit()