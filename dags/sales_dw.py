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

#Configurando os argumentos padrão para a DAG
default_args = {
    'owner': 'pedromenegat',
    'retries': 1,
    'retry_delay': timedelta(minutes=2)
}


def get_vendas(ti):
    '''
    - Função que consulta o banco PostgreSQL com dados de vendas.
    - Retorna um dataframe com toda a tabela vendas e uma lista com os valores distintos
        da coluna id_funcionários para ser usada na função get_funcionários.
    '''
    hook = PostgresHook(postgres_conn_id="banco_vendas")
    df_vendas = hook.get_pandas_df("SELECT * FROM venda")
    ids_funcionarios = json.dumps(df_vendas.id_funcionario.unique().tolist())
    data_vendas = df_vendas.to_json(date_format='iso')
    print(data_vendas)
    print(df_vendas.head())
    ti.xcom_push(key='ids_funcionarios', value=ids_funcionarios)
    ti.xcom_push(key='data_vendas', value=data_vendas)


def get_funcionarios(ti):
    '''
    Função que consulta a API para obter os dados de funcionários.
    Usa como entrada uma lista com todos os valores de id_funcionário para consultar a API.
    Retorna um dataframe com os ids e nomes dos funcionários.
    '''
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
    '''
    Função para obter o arquivo parquet com dados de categorias de produtos.
    Retorna um dataframe com dados de categorias.
    '''
    categorias = pd.read_parquet("https://storage.googleapis.com/challenge_junior/categoria.parquet")
    data_categorias = pd.DataFrame(categorias).to_json()
    ti.xcom_push(key='data_categorias', value=data_categorias)


def insert_funcionarios(ti):
    '''
    Função para inserir os dados de funcionários no banco "sales_dw", tabela dim_funcionarios.
    '''
    funcionarios = json.loads(ti.xcom_pull(task_ids="get_funcionarios", key="data_funcionarios"))
    funcionarios_df = pd.DataFrame(funcionarios)
    engine = create_engine('postgresql+psycopg2://postgres:postgres@host.docker.internal/sales_dw')
    funcionarios_df.to_sql('dim_funcionarios', engine, if_exists='append', index=False)


def insert_categorias(ti):
    '''
    Função para inserir os dados de categorias no banco "sales_dw", tabela dim_categorias.
    '''
    categorias = json.loads(ti.xcom_pull(task_ids="get_categorias", key="data_categorias"))
    categorias_df = pd.DataFrame(categorias)
    engine = create_engine('postgresql+psycopg2://postgres:postgres@host.docker.internal/sales_dw')
    categorias_df.to_sql('dim_categorias', engine, if_exists='append', index=False)


def insert_vendas(ti):
    '''
    Função para inserir os dados de vendas no banco "sales_dw", tabela fato_vendas.
    '''
    vendas = json.loads(ti.xcom_pull(task_ids="get_vendas", key="data_vendas"))
    vendas_df = pd.DataFrame(vendas)
    engine = create_engine('postgresql+psycopg2://postgres:postgres@host.docker.internal/sales_dw')
    vendas_df.to_sql('fato_vendas', engine, if_exists='append', index=False)


with DAG(
        dag_id='sales_datawarehouse',
        default_args=default_args,
        start_date=datetime(2022, 10, 22),
        schedule_interval='@daily'
) as dag:
    create_tables = PostgresOperator(
        task_id='create_tables',
        postgres_conn_id='postgres_localhost',
        sql="""
        CREATE TABLE IF NOT EXISTS dim_funcionarios(		
            id_funcionario INTEGER PRIMARY KEY NOT NULL,
            nome_funcionario VARCHAR(30) NOT NULL
	    );
        CREATE TABLE IF NOT EXISTS dim_categorias(		
            id INTEGER PRIMARY KEY NOT NULL,
            nome_categoria VARCHAR(30) NOT NULL
		);		
		CREATE TABLE IF NOT EXISTS fato_vendas(
            id_venda INTEGER PRIMARY KEY NOT NULL,
            id_funcionario INTEGER NOT NULL,
            id_categoria INTEGER NOT NULL,
            data_venda DATE NOT NULL,
            venda NUMERIC(20,5) NOT NULL,
            FOREIGN KEY (id_funcionario) 
                REFERENCES dim_funcionarios (id_funcionario)
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (id_categoria) 
                REFERENCES dim_categorias (id)
                ON UPDATE CASCADE ON DELETE CASCADE
		);
        """
    )

    call_get_vendas = PythonOperator(
        task_id='get_vendas',
        python_callable=get_vendas
    )

    call_get_funcionarios = PythonOperator(
        task_id='get_funcionarios',
        python_callable=get_funcionarios
    )

    call_get_categorias = PythonOperator(
        task_id='get_categorias',
        python_callable=get_categorias
    )

    truncate_tables = PostgresOperator(
        task_id='truncate_tables',
        postgres_conn_id='postgres_localhost',
        sql="""
            TRUNCATE TABLE dim_funcionarios, dim_categorias, fato_vendas;
            """
    )

    insert_dim_funcionarios = PythonOperator(
        task_id='insert_dim_funcionarios',
        python_callable=insert_funcionarios
    )

    insert_dim_categorias = PythonOperator(
        task_id='insert_dim_categorias',
        python_callable=insert_categorias
    )

    insert_fato_vendas = PythonOperator(
        task_id='insert_fato_vendas',
        python_callable=insert_vendas
    )


    create_tables >> call_get_vendas >> [call_get_funcionarios, call_get_categorias] >> truncate_tables >> insert_dim_funcionarios >> insert_dim_categorias >> insert_fato_vendas
