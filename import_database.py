import pymysql

def import_database():
    try:
        # Conectar a MySQL
        conn = pymysql.connect(host='localhost', user='root', password='toor')
        cursor = conn.cursor()
        
        # Crear base de datos si no existe
        cursor.execute('CREATE DATABASE IF NOT EXISTS sugarbi')
        cursor.execute('USE sugarbi')
        
        # Leer y ejecutar el archivo SQL
        with open('database_sugarbi.sql', 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Dividir en comandos individuales
        commands = sql_content.split(';')
        
        for command in commands:
            command = command.strip()
            if command and not command.startswith('--') and not command.startswith('/*'):
                try:
                    cursor.execute(command)
                except Exception as e:
                    print(f"Error ejecutando comando: {e}")
                    print(f"Comando: {command[:100]}...")
        
        conn.commit()
        conn.close()
        print('Base de datos importada exitosamente')
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    import_database()
