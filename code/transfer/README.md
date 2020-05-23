This is a package written in Python for quick insertion and extraction of
data from a MySQL database. After I started using SQL databases as the main data 
store in my own projects, I continued using Python to build data cleaning and machine learning
pipelines and needed a way to easily pull data from SQL tables from within Python code. 
Even with the existing open-source tools such as PyMySQL, I found myself repeating 
blocks of similar code, especially when extracting and combining data from multiple different 
tables in the same script. 

To make this process less cumbersome I created this tool to quickly 
create tables, insert data, or extract data in one line of code. By centralizing 
the database settings, this tool also "automates" the database connection process 
across each module or script that accesses the database, thus eliminating the need to 
re-enter those settings every time.

# Setup
Before using the module, two files in the directory need modifications, 
.config (required) and schema.json (optional).   

###### `.config`
Input five settings needed to connect to a MySQL server. These are input as 
arguments when creating the PyMySQL connection object.  

    [Local]             # used to name the configuration group, Local is default
    host = 000.0.0.0    # host where the database server is located
    port = 3306         # MySQL port to use
    user = root         # username to log in as
    pwd = mypassword    # password to use
    db = database_name  # name of database to access

###### `schema.json`
To create a new table from a specified schema, the schema must first be outline in schema.json. 
Table names are keys and column specifications are in a list, where each list element contains a map
of the name and column type for that column.
Below is an example schema used to create a customers and purchases table. Column types must adhere to MySQL format.


    {   "customers":[   {"name": "customer_id", "type": "INTEGER"},
                        {"name": "name", "type": "VARCHAR (64)"},
                        {"name": "age", "type": "INTEGER"}
                    ],
        "purchases":[   {"name": "purchase_id", "type": "INTEGER"},
                        {"name": "customer_id", "type": "INTEGER"},
                        {"name": "item_name", "type": "VARCHAR (64)"},
                        {"name": "item_price", "type": "DECIMAL (5,2)"}
                    ]
    }

# Usage
### `DBAssist`
Begin by initializing an instance of the DBAssist class, which automatically creates
and stores a connection with the database using the configuration set in the .config file. 

    dba = DBAssist()

Then the following methods can be used to interact with the database.

##### `dba.create_from_data(table_name, data)`
Create a new table in the database from 2-dimensional data. Acceptable formats are
a pandas dataframe or a list of lists with column names in the first list. DBAssist will
use the values in each column to set the column types as either FLOAT (if column 
contains only numeric values) or VARCHAR.

    # create using a dataframe
    df = pd.read_csv('students.csv')
    dba.create_from_data('students', df)
    
    # create using a list
    data = [['name', 'age'], ['Joe', 15], ['Mary', 16]]
    dba.create_from_data('students', data)

##### `dba.create_from_schema(table_name)`
Create a new table using the specifications in the schema file.

    dba.create_from_schema('customers')
    
##### `dba.insert_rows(table_name, data, at_once=True)`
Insert new rows into a table using 2-dimensional data. By default, all rows are 
inserted with a single insert query and committed at once. This is typically faster but may exceed 
the max query buffer allowed for the default database settings, and any errors will prevent insertion of all rows.
Set at_once=False to insert one row at a time. 

    df = pd.read_csv('new_students.csv')
    dba.insert_rows('students', df, at_once=True)

##### `dba.return_data(table_name, subset=None, modifier="")`
Return the data in a table as a pandas dataframe. Submit a string or list of strings
to the `subset` parameter to select specific columns. Submit a string containing 
SQL WHERE statement syntax to filter rows.

    # all data in customers table
    df = dba.return_data('customers')
    
    # return customer names only
    df = dba.return_data('customers', subset='name')
    
    # select customers younger than 25
    df = dba.return_data('customers', modifier="AGE < 25")

##### `dba.query_result(query_result, as_dict=True)`
Return data obtained from a full MySQL query. Default result is a list of dicts,
where each dict contains the column: value pairs for a table row. 

    # write desired query
    my_query = "SELECT name, age FROM customers WHERE age < 25"
    result = dba.query_result(my_query)
    
    
##### `dba.table_columns(table_name)`
Return names of table columns as a list. 
    
    customer_columns = dba.table_columns('customers')


##### `dba.delete_rows(table_name)`
Delete all rows from a table. Created to clean values from a temporary or 
intermediate pipeline table. 

    dba.delete_rows('old_customers')
    
##### `dba.replace_rows(table_name, data, at_once=True)`
A combination of `delete_rows` and `insert_rows`. 

    df = pd.read_csv('current_customers.csv')
    dba.replace_rows('customers', df)

# Dependencies
In addition to standard Python packages this package uses pandas (tested with version 0.24.2) 
and PyMySQL (tested with version 0.9.3).
