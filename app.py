from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# =============================
# ESTRUTURA DOS TIMES E JOGO
# =============================

teams = {}
dilemas_usados = []
escolhas_temporarias = {} 

def criar_time(nome):
    return {
        "nome": nome,
        "resultado": 100,
        "risco": 0,
        "esg": 50,
        "tecnica": 50,
        "motivos": [], # Justificativas aparecem aqui
        "perfil_contagem": {"Conservador": 0, "Moderado": 0, "Agressivo": 0}
    }

# ==========================================
# DILEMAS (NOMENCLATURA ORIGINAL)
# ==========================================

dilemas = {
    "consignacao": {
        "titulo": "1. Consignação (Influenciadores e Parceiros)",
        "contexto": "A Refaz recebeu 800 peças em consignação (R$ 80/un). A empresa fica com 60% na venda. Segundo o CPC 00, o ativo exige controle e riscos. Como tratar essas peças e o envio de peças próprias para terceiros?",
        "avatar_1": {"nome": "Daniela (CEO)", "fala": "Se lançarmos as 800 peças no Ativo, o estoque cresce e atraímos investidores com um patrimônio mais robusto!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "Cuidado! O CPC 16 e o CPC 00 são claros: sem transferência de riscos e controle, não há Ativo. Isso pode inflar o balanço indevidamente."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Manter controle extracontábil das peças recebidas. No envio de peças próprias a terceiros, manter no Ativo em conta segregada ('Estoque em poder de terceiros').",
                "motivo": "Fiel ao CPC 00 e 16: Evitou inflar o Ativo com bens de terceiros e manteve a propriedade das peças enviadas, garantindo representação fidedigna.",
                "impacto": {"resultado": 0, "risco": -5, "esg": +5, "tecnica": +15}
            },
            "Moderado": {
                "texto": "Registrar peças recebidas no Ativo com um Passivo compensatório. Reconhecer receita e repasse ao consignante apenas na venda final.",
                "motivo": "Buscou transparência, mas gerou 'poluição' no balanço ao registrar ativos de terceiros, embora tenha acertado o momento da receita (CPC 47).",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": 0}
            },
            "Agressivo": {
                "texto": "Registrar as 800 peças como Estoque Próprio imediatamente e reconhecer receita na remessa simples para terceiros.",
                "motivo": "Erro Grave: Inflou o patrimônio indevidamente e antecipou receita sem transferência de controle, violando o CPC 47 e o CPC 16.",
                "impacto": {"resultado": +25, "risco": +30, "esg": -10, "tecnica": -20}
            }
        }
    },
    "prove_em_casa": {
        "titulo": "2. Venda Condicional (Prove em Casa)",
        "contexto": "300 peças enviadas (Custo R$ 22, Preço R$ 70). Apenas 180 confirmadas. O CPC 47 orienta que a receita só existe quando a obrigação de desempenho é cumprida (aceite do cliente).",
        "avatar_1": {"nome": "Renata (Ops)", "fala": "O produto já saiu da prateleira! Precisamos bater a meta do mês, vamos registrar a venda total das 300 peças!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "A transferência física não é transferência de controle. Reconhecer 300 unidades infla o lucro sem garantia de realização econômica."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Reconhecer receita apenas das 180 peças confirmadas. As 120 restantes ficam em subconta 'Estoque em Teste'.",
                "motivo": "Aplicação estrita do CPC 47: Receita apenas após o controle. Evitou a superavaliação do faturamento e preservou a prudência.",
                "impacto": {"resultado": -10, "risco": -10, "esg": +5, "tecnica": +15}
            },
            "Moderado": {
                "texto": "Reconhecer a venda total, mas criar uma 'Provisão para Devoluções' baseada na estimativa de retorno das 120 peças.",
                "motivo": "Uso de estimativa contábil (CPC 47). Embora aceitável, antecipa um resultado que ainda depende do prazo de 7 dias.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": +5}
            },
            "Agressivo": {
                "texto": "Reconhecer receita integral (300 unidades) no ato do envio, tratando como venda definitiva.",
                "motivo": "Prática abusiva: Contraria o CPC 47 e a Estrutura Conceitual, apresentando uma imagem mais otimista do que a realidade.",
                "impacto": {"resultado": +20, "risco": +25, "esg": -5, "tecnica": -15}
            }
        }
    },
    "fretes": {
        "titulo": "3. Logística e Fretes Estratégicos",
        "contexto": "R$ 6.400 de frete na consignação recebida e R$ 4.500 no 'prove em casa'. O CPC 16 permite capitalizar fretes apenas para colocar o bem em condição de venda.",
        "avatar_1": {"nome": "Financeiro", "fala": "Esses gastos logísticos estão destruindo nossa margem! Vamos ativar tudo no estoque para recuperar isso no futuro!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "Frete de venda (entrega) é despesa operacional. Capitalizar frete de itens que não são nossos (consignados) viola o CPC 16."},
        "tem_contabilizacao": False,
        "opcoes": {
            "Conservador": {
                "texto": "Lançar todos os fretes de entrega e consignação recebida como Despesa com Vendas/Comercial no resultado.",
                "motivo": "Conformidade com CPC 16: Frete de saída não é custo de estoque. Evitou capitalização indevida em ativos de terceiros.",
                "impacto": {"resultado": -12, "risco": -5, "esg": +2, "tecnica": +10}
            },
            "Moderado": {
                "texto": "Capitalizar o frete da consignação recebida no estoque (R$ 8/un) e lançar os fretes do 'prove em casa' como despesa.",
                "motivo": "Capitalização incorreta: Ativou custos em bens de terceiros, contrariando a premissa de propriedade e controle.",
                "impacto": {"resultado": -5, "risco": +5, "esg": +5, "tecnica": -5}
            },
            "Agressivo": {
                "texto": "Ativar 100% dos fretes (recebimento e entrega) no Ativo Circulante, diferindo a despesa para os meses seguintes.",
                "motivo": "Maquiagem de resultado: Diferiu despesas operacionais como se fossem ativos, mascarando a baixa rentabilidade atual.",
                "impacto": {"resultado": +15, "risco": +20, "esg": -5, "tecnica": -15}
            }
        }
    }
}
# =============================
# ROTAS
# =============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/iniciar", methods=["POST"])
def iniciar():
    global teams, dilemas_usados, escolhas_temporarias
    teams, dilemas_usados, escolhas_temporarias = {}, [], {}
    nomes_grupos = request.form.getlist("nomes_grupos")
    if not nomes_grupos: nomes_grupos = ["Grupo 1", "Grupo 2", "Grupo 3", "Grupo 4"]

    for i, nome in enumerate(nomes_grupos):
        if nome.strip():
            teams[f"time_{i}"] = criar_time(nome)
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    dilemas_disponiveis = {k: v for k, v in dilemas.items() if k not in dilemas_usados}
    jogo_encerrado = len(dilemas_disponiveis) == 0
    equipe_vencedora = max(teams.values(), key=lambda x: x["resultado"]) if teams else None
    
    for key, time in teams.items():
        if sum(time["perfil_contagem"].values()) > 0:
            time["perfil_predominante"] = max(time["perfil_contagem"], key=time["perfil_contagem"].get)
        else:
            time["perfil_predominante"] = "Aguardando"
    return render_template("dashboard.html", teams=teams, dilemas=dilemas_disponiveis, 
                           jogo_encerrado=jogo_encerrado, equipe_vencedora=equipe_vencedora)

@app.route('/professor_ajuste/<time_key>/<tipo>')
def professor_ajuste(time_key, tipo):
    if time_key in teams:
        if tipo == 'bonus':
            teams[time_key]['resultado'] += 10
            teams[time_key]['tecnica'] += 10
            teams[time_key]['motivos'].append("Bônus: Lançamento contábil correto no quadro.")
        elif tipo == 'penalidade':
            teams[time_key]['resultado'] -= 10
            teams[time_key]['tecnica'] -= 10
            teams[time_key]['motivos'].append("Ressalva: Erro de contabilização no quadro.")
    return redirect(url_for('dashboard'))

@app.route("/dilema/<id_dilema>")
def mostrar_dilema(id_dilema):
    votos_atuais = escolhas_temporarias.get(id_dilema, {})
    return render_template("dilema.html", dilema=dilemas[id_dilema], id_dilema=id_dilema, teams=teams, votos_atuais=votos_atuais)

@app.route("/registrar/<id_dilema>/<perfil>/<time_key>")
def registrar(id_dilema, perfil, time_key):
    global escolhas_temporarias
    if id_dilema not in escolhas_temporarias: escolhas_temporarias[id_dilema] = {}
    escolhas_temporarias[id_dilema][time_key] = perfil

    if len(escolhas_temporarias[id_dilema]) == len(teams):
        for t_key, p_escolhido in escolhas_temporarias[id_dilema].items():
            opcao_dados = dilemas[id_dilema]["opcoes"][p_escolhido]
            for stat in ["resultado", "risco", "esg", "tecnica"]:
                teams[t_key][stat] += opcao_dados["impacto"][stat]
            teams[t_key]["motivos"].append(opcao_dados["motivo"])
            teams[t_key]["perfil_contagem"][p_escolhido] += 1
        dilemas_usados.append(id_dilema)
        del escolhas_temporarias[id_dilema]
        return redirect(url_for("dashboard"))
    return redirect(url_for("mostrar_dilema", id_dilema=id_dilema))

@app.route("/disparar_evento/<id_evento>")
def disparar_evento(id_evento):
    if id_evento == "fiscalizacao":
        for t in teams.values():
            if t["risco"] > 30: t["resultado"] -= 20
    elif id_evento == "investidor":
        for t in teams.values():
            if t["esg"] > 60: t["resultado"] += 15
    return redirect(url_for("dashboard"))

@app.route("/reiniciar")
def reiniciar():
    global teams, dilemas_usados, escolhas_temporarias
    teams, dilemas_usados, escolhas_temporarias = {}, [], {}
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
