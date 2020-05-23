This README describes motivation, setup, and usage for the Python `transfer` module I wrote
to exchange data between Python and MySQL databases. 

My common workflow involves pulling data from database tables, transforming it 
with Python, and writing the transformed data to another table or file. When
using existing open-source tools like PyMySQL in this workflow, I found myself 
repeating blocks of similar code, especially when extracting and combining data 
from many different tables in the same script. 

I created the `transfer` module to enable extraction of data, insertion of 
data, or creation of new tables in a database from within Python in one line of 
code. 


# Setup
Use of the `transfer` module requires two additional files in the directory,
.config and schema.json. Both are explained below.   

###### `.config`
Project or user-specific database settings are imported to  `transfer` and used
as arguments for creating the PyMySQL connection object. Within the `.config` 
under the [Settings] label, enter five settings needed to connect to a MySQL server. 

    [Settings]          # used to label the configuration group, leave as is
    host = 000.0.0.0    # host where the database server is located
    port = 3306         # MySQL port to use
    user = root         # username to log in as
    pwd = mypassword    # password to use
    db = database_name  # name of database to access


###### `schema.json`
To create a new table from a specified schema, the schema must be defined in 
schema.json. Table names are keys and table specifications are given in a list of dictionary
elements, where each element contains key:value pairs for the name and type of a column.
Below is an example schema used to create tables for customers and purchases. Note
that column types must adhere to [MySQL format](https://dev.mysql.com/doc/refman/8.0/en/data-types.html).

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
### The `DBAssist` Class
Begin by importing the DBAssist class and creating an instance. This action creates
a database using the settings in `.config` and stores the connection as an attribute. 
    
    from transfer.transfer import DBAssist
    dba = DBAssist()
    
The connection remains open until explicitly closed by calling `dba.close()`. 


#### `DBAssist` methods
While the connection is open the following methods can be used to interact with
the database.

##### `dba.create_from_data`
Create a new table from a 2-dimensional Python data object. Permitted objects are
a pandas dataframe or a list of lists with column names in the first list.
`create_from_data` uses the column names and data types to generate a "CREATE TABLE" query
and commit it to the database. If the column contains only numeric values, the 
column type is set as FLOAT, otherwise the column type is VARCHAR.

    # create using a dataframe
    df = pd.read_csv('students.csv')
    dba.create_from_data('students', df)
    
    # create using a list
    data = [['name', 'age'], ['Joe', 15], ['Mary', 16]]
    dba.create_from_data('students', data)


##### `dba.create_from_schema`
Create a new table using the specifications in the schema file. Table name must
be assigned in the json object keys

    dba.create_from_schema('customers')


##### `dba.insert_rows()`
Insert all rows from 2-dimensional data as new rows in database table. 
By default, all rows are included in a multi-line insert query and committed at
once. This is typically faster but may exceed the max query buffer allowed for
the default database settings, and any errors will prevent insertion of all rows.
Set at_once=False to insert one row at a time. 

    df = pd.read_csv('new_students.csv')
    dba.insert_rows('students', df, at_once=True)


##### `dba.return_data()`
Return data from a table as a pandas dataframe. By default all data in the table
is extracted. Submit a string or list of strings to the `subset` parameter to 
select specific columns. To filter rows, submit a string permitted for a MySQL 
WHERE statement to the `modifier` parameter.

    # all data in customers table
    df = dba.return_data('customers')
    
    # return customer names only
    df = dba.return_data('customers', subset='name')
    
    # select customers younger than 25
    df = dba.return_data('customers', modifier="AGE < 25")


##### `dba.query_result()`
Return the result of MySQL query. Default result type is a list of dicts,
where each dict contains pairs of column names and values for a table row.

    # write desired query
    young_customers = "SELECT name, age FROM customers WHERE age < 25"
    result = dba.query_result(young_customers)


##### `dba.table_columns()`
Return names of table columns as a list. 

    customer_columns = dba.table_columns('customers')


##### `dba.delete_rows()`
Delete all rows from a table (the table remains, only rows are deleted). 

    dba.delete_rows('old_customers')


##### `dba.replace_rows(table_name, data, at_once=True)`
A combination of `delete_rows` and `insert_rows`. 

    df = pd.read_csv('new_customers.csv')
    dba.replace_rows('customers', df)


# Dependencies
pandas (tested with version 0.24.2)
PyMySQL (tested with version 0.9.3)
