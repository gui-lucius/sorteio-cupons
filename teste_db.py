import psycopg2

try:
    conn = psycopg2.connect(
        dbname="sorteio_db_utf8",
        user="postgres",
        password="novaSenha123",  # Substitua pela nova senha simples
        host="localhost",
        port="5432",
        options="-c client_encoding=UTF8"
    )
    print("✅ Conexão bem-sucedida!")
    conn.close()
except Exception as e:
    print("❌ Erro ao conectar ao PostgreSQL:")
    print(e)
