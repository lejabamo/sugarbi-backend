import pymysql

try:
    conn = pymysql.connect(host='localhost', user='root', password='toor', database='sugarbi')
    cursor = conn.cursor()
    cursor.execute('SHOW TABLES')
    tables = cursor.fetchall()
    
    print(f'Total de tablas: {len(tables)}')
    for table in tables:
        print(f'- {table[0]}')
    
    conn.close()
    print('Verificación completada exitosamente')
    
except Exception as e:
    print(f'Error: {e}')
