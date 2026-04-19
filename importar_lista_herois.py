import sqlite3
import pandas as pd
import os

# --- CONFIGURAÇÃO ---
# Se você renomeou o arquivo, coloque o nome novo aqui:
ARQUIVO_EXCEL = 'lista_herois.xlsx' 
BANCO_DADOS = 'junkrat_data.db'

if not os.path.exists(ARQUIVO_EXCEL):
    print(f"❌ Erro: O arquivo '{ARQUIVO_EXCEL}' não foi encontrado na pasta!")
else:
    # 1. Carrega o Excel
    # Se a sua planilha não for a primeira aba, use: pd.read_excel(ARQUIVO_EXCEL, sheet_name='NomeDaAba')
    df = pd.read_excel(ARQUIVO_EXCEL)

    # 2. Conecta ao banco
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()

    # 3. Limpa e recria a tabela
    cursor.execute("DROP TABLE IF EXISTS bios")
    cursor.execute('''
        CREATE TABLE bios (
            id_nome TEXT PRIMARY KEY,
            info TEXT,
            funcao TEXT
        )
    ''')

    # 4. Importação
    print("Iniciando detonação de dados... 🧨")
    for index, row in df.iterrows():
        # id_nome: Limpa o nome do herói para o comando (ex: "D.Va" vira "dva")
        id_nome = str(row['Herói']).lower().strip().replace(" ", "").replace(":", "").replace("-", "").replace(".", "")
        
        # Monta a info bonitinha
        # Nota: Se alguma coluna estiver vazia no Excel, o pandas pode ler como 'nan'
        nome_comp = str(row['Nome Completo']) if pd.notna(row['Nome Completo']) else "Desconhecido"
        niver = str(row['Aniversário']) if pd.notna(row['Aniversário']) else "???"
        nacao = str(row['Nacionalidade']) if pd.notna(row['Nacionalidade']) else "Desconhecida"
        
        info_formatada = f"🎂 **{niver}** | 👤 **{nome_comp}** | 🌍 **{nacao}**"
        
        classe = str(row['Classe']).strip()
        
        cursor.execute("INSERT INTO bios (id_nome, info, funcao) VALUES (?, ?, ?)", (id_nome, info_formatada, classe))

    conn.commit()
    conn.close()
    print(f"💥 BOOM! {len(df)} heróis importados com sucesso!")