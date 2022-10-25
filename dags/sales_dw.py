from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python_operator import PythonOperator

from datetime import datetime, timedelta
import requests
import pandas as pd
import pyarrow.parquet as pq
import json
from sqlalchemy import create_engine

default_args = {
    'owner': 'pedromenegat',
    'retries': 1,
    'retry_delay': timedelta(minutes=2)
}


def get_vendas(ti):
    hook = PostgresHook(postgres_conn_id="banco_vendas")
    df_vendas = hook.get_pandas_df("SELECT * FROM venda")
    ids_funcionarios = json.dumps(df_vendas.id_funcionario.unique().tolist())
    data_vendas = df_vendas.to_json(date_format='iso')
    print(data_vendas)
    print(df_vendas.head())
    ti.xcom_push(key='ids_funcionarios', value=ids_funcionarios)
    ti.xcom_push(key='data_vendas', value=data_vendas)


def get_funcionarios(ti):
    ids_funcionarios = json.loads(ti.xcom_pull(task_ids="get_vendas", key="ids_funcionarios"))

    funcionarios = []
    for id in ids_funcionarios:
        response = requests.get(
            "https://us-central1-bix-tecnologia-prd.cloudfunctions.net/api_challenge_junior?id=" + str(id))
        funcionarios.append({
            "id_funcionario": id,
            "nome_funcionario": response.text
        })

    data_funcionarios = pd.DataFrame(funcionarios).to_json()
    ti.xcom_push(key='data_funcionarios', value=data_funcionarios)
    # print(pd.DataFrame(funcionarios))


def get_categorias(ti):
    categorias = pd.read_parquet("https://storage.googleapis.com/challenge_junior/categoria.parquet")
    data_categorias = pd.DataFrame(categorias).to_json()
    ti.xcom_push(key='data_categorias', value=data_categorias)


def insert_funcionarios(ti):
    funcionarios = json.loads(ti.xcom_pull(task_ids="get_funcionarios", key="data_funcionarios"))
    funcionarios_df = pd.DataFrame(funcionarios)
    engine = create_engine('postgresql+psycopg2://postgres:postgres@host.docker.internal/sales_dw')
    funcionarios_df.to_sql('funcionarios', engine, if_exists='append', index=False)


def insert_categorias(ti):
    categorias = json.loads(ti.xcom_pull(task_ids="get_categorias", key="data_categorias"))
    categorias_df = pd.DataFrame(categorias)
    engine = create_engine('postgresql+psycopg2://postgres:postgres@host.docker.internal/sales_dw')
    categorias_df.to_sql('categorias', engine, if_exists='append', index=False)


def insert_vendas(ti):
    vendas = json.loads(ti.xcom_pull(task_ids="get_vendas", key="data_vendas"))
    vendas_df = pd.DataFrame(vendas)
    engine = create_engine('postgresql+psycopg2://postgres:postgres@host.docker.internal/sales_dw')
    vendas_df.to_sql('vendas', engine, if_exists='append', index=False)


with DAG(
        dag_id='sales_datawarehouse',
        default_args=default_args,
        start_date=datetime(2022, 10, 22),
        schedule_interval='@daily'
) as dag:
    task1 = PostgresOperator(
        task_id='create_tables',
        postgres_conn_id='postgres_localhost',
        sql="""
        CREATE TABLE IF NOT EXISTS funcionarios(		
            id_funcionario INTEGER PRIMARY KEY NOT NULL,
            nome_funcionario VARCHAR(30) NOT NULL
	    );
        CREATE TABLE IF NOT EXISTS categorias(		
            id INTEGER PRIMARY KEY NOT NULL,
            nome_categoria VARCHAR(30) NOT NULL
		);		
		CREATE TABLE IF NOT EXISTS vendas(
            id_venda INTEGER PRIMARY KEY NOT NULL,
            id_funcionario INTEGER NOT NULL,
            id_categoria INTEGER NOT NULL,
            data_venda DATE NOT NULL,
            venda NUMERIC(20,5) NOT NULL,
            FOREIGN KEY (id_funcionario) 
                REFERENCES funcionarios (id_funcionario)
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (id_categoria) 
                REFERENCES categorias (id)
                ON UPDATE CASCADE ON DELETE CASCADE
		);
        """
    )

    task2 = PythonOperator(
        task_id='get_vendas',
        python_callable=get_vendas
    )

    task3 = PythonOperator(
        task_id='get_funcionarios',
        python_callable=get_funcionarios
    )

    task4 = PythonOperator(
        task_id='get_categorias',
        python_callable=get_categorias
    )

    task5 = PostgresOperator(
        task_id='truncate_database',
        postgres_conn_id='postgres_localhost',
        sql="""
            TRUNCATE TABLE funcionarios, categorias, vendas;
            """
    )

    task6 = PythonOperator(
        task_id='insert_funcionarios',
        python_callable=insert_funcionarios
    )

    task7 = PythonOperator(
        task_id='insert_categorias',
        python_callable=insert_categorias
    )

    task8 = PythonOperator(
        task_id='insert_vendas',
        python_callable=insert_vendas
    )

    '''
    Task1 para criar o DW.
    Task2 para pegar os dados de venda.
    Task3 pega os distintos valores de id_funcionario para consultara API.
    Task4 lê o arquivo parquet.
    '''

    task1 >> task2 >> [task3, task4] >> task5 >> task6 >> task7 >> task8
