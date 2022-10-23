from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python_operator import PythonOperator

import requests
import pandas as pd
import pyarrow.parquet as pq
import json


default_args = {
    'owner': 'pedromenegat',
    'retries': 1,
    'retry_delay': timedelta(minutes=2)
}

def get_vendas(ti):
    hook = PostgresHook(postgres_conn_id="banco_vendas")
    df_vendas = hook.get_pandas_df("SELECT * FROM venda")
    ids_funcionarios = json.dumps(df_vendas.id_funcionario.unique().tolist())
    ti.xcom_push(key='ids_funcionarios', value=ids_funcionarios)
    #return df_vendas

def get_funcionarios(ti):
    ids_funcionarios = ti.xcom_pull(task_ids="get_vendas", key="ids_funcionarios")
    '''
    funcionarios = []
    for id in ids_funcionarios:
        response = requests.get(
            "https://us-central1-bix-tecnologia-prd.cloudfunctions.net/api_challenge_junior?id=" + str(id))
        funcionarios.append({
            "id": id,
            "nome": response.text
        })
    print(pd.DataFrame(funcionarios))
    '''
    print(ids_funcionarios)

with DAG(
        dag_id='sales_datawarehouse',
        default_args=default_args,
        start_date=datetime(2022, 10, 22),
        schedule_interval='@daily'
) as dag:
    task1 = PostgresOperator(
        task_id='create_tables',
        postgres_conn_id='postgres_localhost',
        sql = """
        CREATE TABLE IF NOT EXISTS funcionarios(		
            id_funcionario INTEGER PRIMARY KEY NOT NULL,
            nome_funcionario VARCHAR(30) NOT NULL
	    );
        CREATE TABLE IF NOT EXISTS categorias(		
            id_categoria INTEGER PRIMARY KEY NOT NULL,
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
                REFERENCES categorias (id_categoria)
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

    task1 >> task2 >> task3
