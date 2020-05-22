import os

# create absolute path to this file
PATH_HERE = os.path.abspath(os.path.dirname(__file__))

CONFIG = '.config'
CONFIG_FILE= os.path.join(PATH_HERE, CONFIG)

SCHEMA = 'schema.json'
SCHEMA_FILE = os.path.join(PATH_HERE, SCHEMA)

#DB_NAME = 'database_name'
DB_NAME = 'bball'
