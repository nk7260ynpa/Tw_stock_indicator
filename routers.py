import pandas as pd
from sqlalchemy import text

from clients import mysql_conn, mysql_conn_db

class MySQLRouter:
    def __init__(self, host, user, password, db_name=None):
        """
        Initialize the MySQLRouter with the given parameters.

        Args:
            host (str): The MySQL host.
            user (str): The MySQL user.
            password (str): The MySQL password.
            db_name (str, optional): The name of the database. Defaults to None.
        """
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db_name
        self.conn = self._build_mysql_conn()
    
    def _build_mysql_conn(self):
        """
        Build a MySQL connection based on the provided parameters.

        Args:
            self.host (str): The MySQL host.
            self.user (str): The MySQL user.
            self.password (str): The MySQL password.
            self.db_name (str, optional): The name of the database. Defaults to None.

        Returns:
            conn: The MySQL connection object.
        """
        if self.db_name:
            conn = mysql_conn_db(self.host, self.user, self.password, self.db_name)
        else:
            conn = mysql_conn(self.host, self.user, self.password)
        return conn

    @property    
    def mysql_conn(self):
        """
        Get the MySQL connection object.

        Returns:
            conn: The MySQL connection object.

        Example:
        >>> Example:
        >>> router = MySQLRouter(host, user, password, db_name)
        >>> conn = router.mysql_conn
        >>> conn.execute("SELECT 1")
        >>> conn.close()
        """
        return self.conn
    
class MyTWSESQLRouter:
    def __init__(self, host, user, password):
        """
        Initialize the MyTWSESQLRouter with the given parameters.

        Args:
            host (str): The MySQL host.
            user (str): The MySQL user.
            password (str): The MySQL password.
            db_name (str, optional): The name of the database. Defaults to None.
        """
        self.host = host
        self.user = user
        self.password = password
        self.db_name = "TWSE"
        self.conn = self._build_mysql_conn()

    def _data_preprocess(self, data):
        """
        Preprocess the data by converting date columns to datetime format.

        Args:
            data (pd.DataFrame): The DataFrame containing the data.

        Returns:
            pd.DataFrame: The preprocessed DataFrame.
        """
        data['Date'] = pd.to_datetime(data['Date'])
        columns_to_convert = ['TradeVolume', 'OpeningPrice', 'HighestPrice', 'LowestPrice', 'ClosingPrice']
        data[columns_to_convert] = data[columns_to_convert].astype(float)
        data.rename({"Date": "date",
                     "TradeVolume": "volume", 
                     "OpeningPrice": "open",
                     "HighestPrice": "high",
                     "LowestPrice": "low",
                     "ClosingPrice": "close"}, axis=1, inplace=True)
        data.set_index('date', inplace=True)
        return data

    
    def load_data(self, start_date, end_date, security_code):
        """
        Load data from the TWSE database.

        Args:
            start_date (str): The start date for the query.
            end_date (str): The end date for the query.
            security_code (str): The security code to filter the data.

        Returns:
            pd.DataFrame: The loaded data as a DataFrame.
        """
        query = f"""
            SELECT * 
            FROM DailyPrice
            WHERE Date BETWEEN '{start_date}' AND '{end_date}' 
            AND SecurityCode = '{security_code}'
        """
        results = self.conn.execute(text(query)).fetchall()
        data = pd.DataFrame(results)
        data = self._data_preprocess(data)
        return data
    
    def _build_mysql_conn(self):
        """
        Build a MySQL connection based on the provided parameters.

        Args:
            self.host (str): The MySQL host.
            self.user (str): The MySQL user.
            self.password (str): The MySQL password.
            self.db_name (str, optional): The name of the database. Defaults to None.

        Returns:
            conn: The MySQL connection object
        """
        conn = mysql_conn_db(self.host, self.user, self.password, self.db_name)
        return conn
        
        