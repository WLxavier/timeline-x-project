import os
import psycopg2
import pandas as pd
import numpy as np
import zipfile
import io
import time

DB_HOST = os.getenv("DB_HOST", "timescaledb")
DB_NAME = os.getenv("DB_NAME", "cronos_db")
DB_USER = os.getenv("DB_USER", "cronos_user")
DB_PASS = os.getenv("DB_PASS", "cronos_password")
OUTER_ZIP_PATH = "/data/5. Turbofan Engine Degradation Simulation Data Set.zip"
INNER_ZIP_PATH = "6. Turbofan Engine Degradation Simulation Data Set/CMAPSSData.zip" 
TARGET_FILE_SUFFIX = 'train_FD001.txt'
TABLE_NAME = "nasa_turbofan_data"

def get_db_connection():
    retries = 5; conn = None
    while retries > 0 and not conn:
        try: conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        except psycopg2.OperationalError: retries -= 1; time.sleep(5)
    if conn: print("IMPORTER: Conexão com o TimescaleDB estabelecida!")
    return conn

def process_data_from_nested_zip():
    print(f"IMPORTER: Lendo o arquivo ZIP externo em {OUTER_ZIP_PATH}...")
    try:
        with zipfile.ZipFile(OUTER_ZIP_PATH, 'r') as outer_z:
            print(f"IMPORTER: Procurando pelo ZIP interno em '{INNER_ZIP_PATH}'...")
            inner_zip_bytes = outer_z.read(INNER_ZIP_PATH)
            print("IMPORTER: Lendo o ZIP interno a partir da memória...")
            with zipfile.ZipFile(io.BytesIO(inner_zip_bytes), 'r') as inner_z:
                file_to_extract = None
                for filename in inner_z.namelist():
                    if filename.endswith(TARGET_FILE_SUFFIX):
                        file_to_extract = filename
                        break
                if not file_to_extract: raise FileNotFoundError(f"Não foi possível encontrar '{TARGET_FILE_SUFFIX}' dentro do ZIP interno.")
                with inner_z.open(file_to_extract) as f:
                    df = pd.read_csv(f, sep=' ', header=None)
                print(f"IMPORTER: Arquivo {file_to_extract} extraído e lido com sucesso.")
    except (FileNotFoundError, KeyError):
        print(f"ERRO: Arquivo ou caminho não encontrado.")
        return None
    except Exception as e:
        print(f"ERRO: Falha ao ler os arquivos ZIP: {e}")
        return None
    df.drop(columns=[26, 27], inplace=True)
    columns = ['unit_nr', 'cycle', 'setting1', 'setting2', 'setting3'] + [f'sensor{i}' for i in range(1, 22)]
    df.columns = columns
    max_cycles = df.groupby('unit_nr')['cycle'].max().reset_index()
    max_cycles.columns = ['unit_nr', 'max_cycle']
    df = pd.merge(df, max_cycles, on='unit_nr')
    df['RUL'] = df['max_cycle'] - df['cycle']
    df.drop(columns=['max_cycle'], inplace=True)
    print("IMPORTER: Processamento de dados concluído.")
    return df

def create_table_and_insert_data(conn, df):
    """Cria a tabela e insere os dados do DataFrame."""
    with conn.cursor() as cur:
        print(f"IMPORTER: Criando a tabela '{TABLE_NAME}'...")
        cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
        column_definitions = ", ".join([f"{col} REAL" for col in df.columns if col != 'unit_nr'])
        cur.execute(f"CREATE TABLE {TABLE_NAME} (time TIMESTAMPTZ DEFAULT NOW(), unit_nr INTEGER, {column_definitions});")
        print(f"IMPORTER: Inserindo {len(df)} registros no banco de dados...")
        
        data_tuples = list(df.itertuples(index=False, name=None))
        cols = ",".join(list(df.columns))
        
        from psycopg2.extras import execute_values
        execute_values(cur, f"INSERT INTO {TABLE_NAME} ({cols}) VALUES %s", data_tuples)
        conn.commit()
    print("IMPORTER: Inserção de dados concluída com sucesso!")


if __name__ == "__main__":
    connection = get_db_connection()
    if connection:
        try:
            dataframe = process_data_from_nested_zip()
            if dataframe is not None:
                create_table_and_insert_data(connection, dataframe)
        except Exception as e:
            print(f"IMPORTER: Um erro ocorreu durante o processo: {e}")
        finally:
            connection.close()