import os
from dotenv import load_dotenv
import pandas as pd
import psycopg2
from sshtunnel import SSHTunnelForwarder
import paramiko
import pandas as pd

load_dotenv()

class Client:
    """
    Class to connect to and communicate with a PostgreSQL database hosted on a remote server.
      This class uses ssh tunneling (via sshtunnel and paramiko) to connect to the remote server and
      psycopg2 for database utilities
    """
    def __init__(self, local_port: int):
        self.ssh_host = os.getenv("SSH_HOST")
        self.ssh_username = os.getenv("SSH_USERNAME")
        self.ssh_private_key = os.getenv("SSH_PRIVATE_KEY_PATH")
        self.ssh_password = os.getenv("SSH_PRIVATE_KEY_PASSWORD")
        self.database_name = os.getenv("DATABASE")
        self.db_user = os.getenv("PG_USER")
        self.db_password = os.getenv("PG_PASSWORD")
        self.local_port = local_port

    def connect_to_server(self):
        """
        Sets up ssh tunnel to server hosting PostgreSQL database
        """

        key = paramiko.Ed25519Key.from_private_key_file(self.ssh_private_key, password=self.ssh_password)

        server = SSHTunnelForwarder(
            ('192.168.50.186', 22),
            ssh_username=self.ssh_username,
            ssh_pkey=key,
            remote_bind_address=('localhost', 5432),
            local_bind_address=('127.0.0.1', self.local_port))
        
        return server
    
    def connect_to_db(self, server: SSHTunnelForwarder):
        """Connect to PostgreSQL database using ssh tunnel
        
        Args:
            server (ssh.SSHTunnelForwarder): An instance of ssh.SSHTunnelForwarder
              with the information for connecting to the server that hosts the PostgreSQL Database

        Returns:
            psycopg2 connection
        """

        conn = psycopg2.connect(
        host='localhost',
        port=server.local_bind_port,
        database=self.database_name,
        user=self.db_user,
        password=self.db_password)

        return conn
    
    def pull_data(self, query: str):
        """
        Pulls data from the PostgreSQL database using a passed in select statement

        Args:
            query (str): Postgres SQL select query 

        Returns:
            pandas.DataFrame
        """

        try:
            # Instantiate server tunnel
            server = self.connect_to_server()
            server.start()

            conn = self.connect_to_db(server=server)

            df = pd.read_sql_query(query, conn)
        except Exception as e:
            print(f"Connection Error: {e}")
        finally:
            if server.is_active:
                server.stop()
            return df
        
    def run_statement(self, query: str, return_df: bool = False):
        """
        Executes a specified PostgreSQL statement
        
        Args:
            query (str): PostgreSQL insert statement
            return_df (bool): whether to return a dataframe or not
        """

        try:
            # Instantiate server tunnel
            server = self.connect_to_server()
            server.start()

            # Connect to database
            conn = self.connect_to_db(server=server)

            # Setup cursor
            cur = conn.cursor()

            # Execute query
            cur.execute(query)


        except Exception as e:
            print(f"Connection Error: {e}")
            return(e)
        finally:
            if return_df:
                try:
                    data = cur.fetchall()
                    cols = [desc[0] for desc in cur.description]
                    out = pd.DataFrame(data, columns=cols)
                except:
                    out = pd.DataFrame(['No data to add'], columns=['Query finished successfully'])
            else:
                out = f"Data added to database successfully using {query}"
            # Commit changes
            conn.commit()
            cur.close()
            conn.close()
            if server.is_active:
                server.stop()
            return out
            





