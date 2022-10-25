from google.cloud import storage
from google.cloud import bigquery
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import requests
import pandas as pd
import pyarrow.parquet as pq


def psql_connect():
    conn = psycopg2.connect(
        host="34.173.103.16",
        database="postgres",
        user="junior",
        password="|?7LXmg+FWL&,2(",
        port="5432"
    )

    cur = conn.cursor()
    cur.execute("SELECT * FROM venda limit 10;")
    dados = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]

    print(colnames)
    for dado in dados:
        print(dado)


def api_responses():
    for employee_id in range(12):
        response = requests.get(
            "https://us-central1-bix-tecnologia-prd.cloudfunctions.net/api_challenge_junior?id=" + str(employee_id + 1))
        print(str(employee_id + 1) + " " + response.text + " " + str(response.status_code))


def read_parquet_file():
    arquivo2 = pq.read_pandas('C:/Users/Pedro Menegat/Desktop/JrDataEngineerTest/files/categoria.parquet').to_pandas()
    print(arquivo2)


def create_database():
    # connection establishment
    conn = psycopg2.connect(
        database="postgres",
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'
    )

    conn.autocommit = True

    # Creating a cursor object
    cursor = conn.cursor()

    # query to create a database
    sql = ''' CREATE database testeB ''';

    # executing above query
    cursor.execute(sql)
    print("Database has been created successfully !!")

    conn_2 = psycopg2.connect(
        database="testeb",
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'
    )

    conn_2.autocommit = True

    cursor_2 = conn_2.cursor()

    commands = (
        """
        CREATE TABLE funcionarios(		
            id_funcionario INTEGER PRIMARY KEY NOT NULL,
            nome_funcionario VARCHAR(30) NOT NULL
	    )
        """,
        """ 
        CREATE TABLE categorias(		
            id_categoria INTEGER PRIMARY KEY NOT NULL,
            nome_categoria VARCHAR(30) NOT NULL
		)
        """,
        """
        CREATE TABLE vendas(
            id_venda INTEGER PRIMARY KEY NOT NULL,
            id_funcionario INTEGER NOT NULL,
            id_categoria INTEGER NOT NULL,
            data_venda DATE NOT NULL,
            venda NUMERIC(20,5) NOT NULL,
            FOREIGN KEY (id_funcionario) 
                REFERENCES funcionarios (id_funcionario)
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (id_categoria) 
                REFERENCES categorias (id_categoria)
                ON UPDATE CASCADE ON DELETE CASCADE
		)
        """)

    for command in commands:
        cursor_2.execute(command)
        print("Foi")

    # Closing the connection
    cursor.close()
    cursor_2.close()
    conn.close()
    conn_2.close()

def google_file():
    arq = pd.read_parquet("https://storage.googleapis.com/challenge_junior/categoria.parquet")
    print(arq)

#create_database()
psql_connect()
# api_responses()
# read_parquet_file()

#google_file()