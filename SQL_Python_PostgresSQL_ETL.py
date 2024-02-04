# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 00:35:36 2024

@author: jasdh
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import pandas as pd

# good practice to store uid and password elsewhere
# i.e. from environment variable rather than hardcoding
pwd = "your_password"
# make sure user etl has superuser permissions in postgresql 
# in SQL user etl needs execute/db_datareade permissions
uid = "your_id"

# sql db details
driver = "{your_driver}"
server = r"SQL_Server_hostname"
psql_server = r"psql_server_name"
database = r"your_database;"

# Extract data from sql server
def extract():
    src_conn = None
    try:
        # use the trusted connections to use windows authentification to a
        conn_str = 'DRIVER='+ driver + ';SERVER=' + server + ';DATABASE=' + database + ';Trusted_Connection=yes;'  
        # ';Integrated Security=SSPI;UID=' + uid + ';PWD=' + pwd
        conn_url = URL.create("mssql+pyodbc", query={"odbc_connect": conn_str})
        src_engine = create_engine(conn_url)
        src_conn = src_engine.connect()
        
        # Execute query to get table names and schema
        query= """SELECT s.TABLE_SCHEMA,
            t.name AS table_name FROM sys.tables t
            JOIN INFORMATION_SCHEMA.TABLES s ON t.name = s.TABLE_NAME
            WHERE t.name IN ('Table1', 'Table2', 'Table3', 'Table4')
            """
        src_tables = pd.read_sql_query(query, src_conn).to_dict()['table_name']
        src_schema = pd.read_sql_query(query, src_conn).to_dict()['TABLE_SCHEMA']
        
        for id in src_tables:
            table_name = src_tables[id]
            schema = src_schema[id]
            df = pd.read_sql_query(f'select * FROM {schema}.{table_name}', src_conn)
            load(df,table_name) 
            
    except Exception as e:
        print("Data server extraction error: " + str(e))
    finally:
        if src_conn is not None:
            src_conn.close()


# load data to postgres; database: AdventureWorks
def load(df,tbl):
    try:
        rows_imported = 0
        engine = create_engine(f'postgresql://{uid}:{pwd}@{psql_server}:5432/AdventureWorks')
        print(f'importing rows {rows_imported} to {rows_imported + len(df)}... for table {tbl}')
        # save df to postgres
        df.to_sql(f'stg_{tbl}', engine, if_exists='replace', index=False)
    except Exception as e:
        print("Data server loading error: " + str(e))


try:
    # call extract function
    extract()
    print('Loading completed')
except Exception as e:
    print("Execution error: " + str(e))
