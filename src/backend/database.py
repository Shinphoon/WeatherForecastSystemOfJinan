import pyodbc

SERVER = r'LAPTOP-AVTE0SM8'
DATABASE = '济南天气'

def get_connection():
    connection = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={SERVER};'
        f'DATABASE={DATABASE};'
        f'Trusted_Connection=yes;'
        f'TrustServerCertificate=yes;'
    )
    return connection

def test_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print('SQL Server 数据库连接成功：', result[0])
        cursor.close()
        conn.close()
    except Exception as e:
        print('SQL Server 数据库连接失败：')
        print(e)

if __name__ == '__main__':
    test_connection()