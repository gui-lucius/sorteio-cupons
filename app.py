from flask import Flask, render_template, request, redirect, url_for, jsonify
import psycopg2
import random
from collections import defaultdict

app = Flask(__name__)

# Função para conectar ao PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        dbname="sorteio_db_utf8",
        user="postgres",
        password="novaSenha123",
        host="localhost",
        port="5432",
        options="-c client_encoding=UTF8"
    )



# Criar as tabelas automaticamente pelo Flask
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            quantidade_cupons INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cupons (
            id SERIAL PRIMARY KEY,
            numero INTEGER NOT NULL,
            colaborador_id INTEGER REFERENCES colaboradores(id)
        )
    ''')

    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_colaborador', methods=['POST'])
def add_colaborador():
    nome = request.form['nome']
    quantidade = int(request.form['quantidade'])

    conn = get_db_connection()
    cursor = conn.cursor()

    # Inserir colaborador e obter seu ID
    cursor.execute("INSERT INTO colaboradores (nome, quantidade_cupons) VALUES (%s, %s) RETURNING id", (nome, quantidade))
    colaborador_id = cursor.fetchone()[0]

    # Buscar todos os cupons já utilizados
    cursor.execute("SELECT numero FROM cupons")
    cupons_existentes = {row[0] for row in cursor.fetchall()}  # Conjunto de cupons já ocupados

    # Criar lista de cupons disponíveis (de 1 a 60000, removendo os já ocupados)
    todos_cupons = set(range(1, 60001))
    cupons_disponiveis = list(todos_cupons - cupons_existentes)

    # Garantir que há cupons suficientes disponíveis
    if len(cupons_disponiveis) < quantidade:
        return "Erro: Não há cupons suficientes disponíveis!", 400

    # Sortear aleatoriamente os cupons para esse colaborador
    cupons_aleatorios = random.sample(cupons_disponiveis, quantidade)

    # Inserir os cupons no banco de dados
    for numero_cupom in cupons_aleatorios:
        cursor.execute("INSERT INTO cupons (numero, colaborador_id) VALUES (%s, %s)", (numero_cupom, colaborador_id))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/sorteio')
def sorteio():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Buscar um cupom aleatório disponível
    cursor.execute("SELECT numero, colaborador_id FROM cupons ORDER BY RANDOM() LIMIT 1")
    resultado = cursor.fetchone()
    
    if resultado:
        numero, colaborador_id = resultado
        if colaborador_id:
            cursor.execute("SELECT nome FROM colaboradores WHERE id = %s", (colaborador_id,))
            colaborador = cursor.fetchone()
            if colaborador:
                nome_colaborador = colaborador[0]
                mensagem = f"Cupom {numero:05d} de {nome_colaborador} foi sorteado!"
            else:
                mensagem = f"Cupom {numero:05d} não pertence a ninguém, sortear novamente!"
        else:
            mensagem = f"Cupom {numero:05d} não pertence a ninguém, sortear novamente!"
        
        cursor.execute("DELETE FROM cupons WHERE numero = %s", (numero,))
        conn.commit()
    
    else:
        mensagem = "Nenhum cupom disponível para sorteio."

    conn.close()
    return jsonify({"mensagem": mensagem})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)