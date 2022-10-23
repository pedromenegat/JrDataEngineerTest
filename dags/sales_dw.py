from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator

default_args = {
    'owner': 'pedromenegat',
    'retries': 5,
    'retry_delay': timedelta(minutes=2)
}

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

    task1
