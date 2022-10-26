# JrDataEngineerTest

# Informações Gerais

Repositório criado para o controle de versionamento da realização do desafio técnico do processo seletivo para o cargo de Engenheiro de Dados Jr. 

Linguagens e ferramentas utilizadas: Python, SQL, Airflow, Docker, modelagem de dados, data warehouse.

# Especificações do desafio

O desafio técnico consiste na problemática descrita abaixo.

Temos três fontes com seguintes dados:
- Banco PostgreSQL com dados de vendas.
- API com dados de funcionários.
- Arquivo parquet com dados de categoria.

O objetivo do desafio é criar um pipeline para movimentar esses dados para um banco de dados no seu ambiente, considerando que ao fim vamos ter as vendas, funcionários e categorias em um só lugar.

Um requisito desse desafio é que essa movimentação de dados seja feita diariamente, pois foi informado que todas as fontes recebem dados novos periodicamente e assim os dados no seu ambiente vão ficar atualizados. Considerando isso, é importante que tenha um orquestrador para acionar o pipeline automaticamente.

Ilustração da arquitetura:

![image](https://user-images.githubusercontent.com/62032339/198059805-b12e01b7-c113-45c4-a93a-ce6ad5a12ed0.png)
