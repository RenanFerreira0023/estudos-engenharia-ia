import json
import sqlite3
from threading import RLock

from .configuracao import localizar_projeto


class Catalogo:
    def __init__(self):
        self.trava = RLock()
        self.conexao = sqlite3.connect(":memory:", check_same_thread=False)
        self.conexao.row_factory = sqlite3.Row
        pasta = localizar_projeto() / "02_codigo/dados"
        dados = {nome: json.loads((pasta / f"{nome}.json").read_text(encoding="utf-8-sig"))
                 for nome in ("veiculos", "produtos", "aplicacoes")}
        # SQLITE importa IDs, preços em centavos e os documentos completos, incluindo os limites da simulação.
        self.conexao.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE veiculos (id TEXT PRIMARY KEY, dados TEXT NOT NULL);
            CREATE TABLE produtos (id TEXT PRIMARY KEY, sku TEXT UNIQUE, categoria TEXT,
                preco_centavos INTEGER CHECK(preco_centavos >= 0), estoque INTEGER CHECK(estoque >= 0), dados TEXT NOT NULL);
            CREATE TABLE aplicacoes (id TEXT PRIMARY KEY, produto_id TEXT REFERENCES produtos(id),
                veiculo_id TEXT REFERENCES veiculos(id), dados TEXT NOT NULL);
        """)
        self.conexao.executemany("INSERT INTO veiculos VALUES (?, ?)",
                                 [(v["id"], json.dumps(v, ensure_ascii=False)) for v in dados["veiculos"]])
        self.conexao.executemany("INSERT INTO produtos VALUES (?, ?, ?, ?, ?, ?)",
                                 [(v["id"], v["sku"], v["categoria"], v["preco_centavos"], v["estoque"], json.dumps(v, ensure_ascii=False)) for v in dados["produtos"]])
        self.conexao.executemany("INSERT INTO aplicacoes VALUES (?, ?, ?, ?)",
                                 [(v["id"], v["produto_id"], v["veiculo_id"], json.dumps(v, ensure_ascii=False)) for v in dados["aplicacoes"]])
        self.conexao.commit()
        # SOMENTE LEITURA depois da carga. Não há ferramenta que aceite SQL arbitrário nesta fase.
        self.conexao.execute("PRAGMA query_only = ON")
        self.conexao.set_authorizer(lambda acao, tabela, coluna, banco, gatilho:
            sqlite3.SQLITE_OK if acao == sqlite3.SQLITE_SELECT or
            (acao == sqlite3.SQLITE_READ and tabela in ("produtos", "veiculos", "aplicacoes")) else sqlite3.SQLITE_DENY)

    def ler(self, sql, parametros=()):
        with self.trava:
            return self.conexao.execute(sql, parametros).fetchall()

    def listar_veiculos(self):
        sql = "SELECT dados FROM veiculos ORDER BY id"
        return {"status": "ok", "veiculos": [json.loads(v["dados"]) for v in self.ler(sql)],
                "sql_executado": sql, "parametros_sql": [], "natureza": "recortes_academicos_propostos"}

    def consultar(self, produto_id=None, veiculo_id=None, categoria=None):
        if not produto_id and not veiculo_id:
            return {"status": "identificacao_pendente", "produtos": [], "aplicacoes": [],
                    "pendencias": ["Informe código do produto ou identifique a configuração do veículo."]}
        if veiculo_id and not self.ler("SELECT id FROM veiculos WHERE id = ?", (veiculo_id,)):
            return {"status": "veiculo_nao_encontrado", "produtos": [], "aplicacoes": []}
        # SQL PARAMETRIZADO consulta dados reais do arquivo fictício. Não é demonstração de text-to-SQL.
        sql = "SELECT DISTINCT p.dados FROM produtos p"
        filtros, parametros = [], []
        if veiculo_id:
            sql += " JOIN aplicacoes a ON a.produto_id = p.id"
            filtros.append("a.veiculo_id = ?")
            parametros.append(veiculo_id)
        if produto_id:
            filtros.append("(p.id = ? OR p.sku = ?)")
            parametros.extend([produto_id.upper(), produto_id.upper()])
        if categoria:
            filtros.append("p.categoria = ?")
            parametros.append(categoria)
        sql += " WHERE " + " AND ".join(filtros) + " ORDER BY p.id"
        produtos = [json.loads(r["dados"]) for r in self.ler(sql, parametros)]
        aplicacoes, consultas = [], [{"sql": sql, "parametros": parametros}]
        for produto in produtos:
            consulta = "SELECT dados FROM aplicacoes WHERE produto_id = ?"
            params = [produto["id"]]
            if veiculo_id:
                consulta += " AND veiculo_id = ?"
                params.append(veiculo_id)
            aplicacoes.extend(json.loads(r["dados"]) for r in self.ler(consulta, params))
            consultas.append({"sql": consulta, "parametros": params})
        return {"status": "ok" if produtos else "produto_nao_encontrado", "produtos": produtos,
                "aplicacoes": aplicacoes, "sql_executado": consultas,
                "limite": "Produtos e vínculos simulados; aplicações não homologadas para uso real. Estoque zero não significa inexistência."}

    def fechar(self):
        self.conexao.close()
