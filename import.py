# Import: Provided for you in this project is a file called books.csv, which is a spreadsheet in CSV format of 5000 different books.
# Each one has an ISBN nubmer, a title, an author, and a publication year.
# In a Python file called import.py separate from your web application, write a program that will take the books and import them into your PostgreSQL database.
# You will first need to decide what table(s) to create, what columns those tables should have, and how they should relate to one another.
# Run this program by running python3 import.py to import the books into your database, and submit this program with the rest of your project code.

import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
    reaise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
