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
        "auditorias_restantes": 2
    }

# =============================
# DILEMAS (BASEADOS NO ROTEIRO REFAZ)
# =============================

dilemas = {
    "doacoes": {
        "titulo": "1. Doações e Compras sem Nota (O Início)",
        "contexto": "O estoque físico tem 10.000 peças: 7.000 doadas e 3.000 compradas por R$ 120 mil sem NF. Vitor precisa decidir como mensurar esse ativo inicial.",
        "conflito": "Daniela: 'O estoque é nosso maior ativo, não pode ser zero!' | Vitor: 'Sem NF, como comprovar o custo em uma auditoria?'",
        "desc_conservadora": "Registra doações a R$ 1 e compras sem NF como despesa. Foco em compliance fiscal.",
        "desc_moderada": "Avalia pelo Valor Justo (similares) e registra compras pelo valor de mercado (R$ 120 mil).",
        "desc_agressiva": "Registra pelo preço de venda futuro e capitaliza os R$ 15 mil de higienização.",
        "conservadora": {"resultado": -15, "risco": -10, "esg": +5, "tecnica": +10},
        "moderada": {"resultado": -5, "risco": +5, "esg": +10, "tecnica": +10},
        "agressiva": {"resultado": +20, "risco": +25, "esg": -5, "tecnica": -15}
    },
    "obsolescencia": {
        "titulo": "2. Obsolescência (Marketing vs. Financeiro)",
        "contexto": "1.500 peças (R$ 15.000) têm VRL próximo de zero. São itens fora de moda ou manchados.",
        "conflito": "Marketing: 'Mantenha no site para atrair visitantes!' | Financeiro: 'Isso é estoque podre, vamos limpar o balanço!'",
        "desc_conservadora": "Baixa integral imediata dos R$ 15.000. Prioriza a prudência e liquidez real.",
        "desc_moderada": "Mantém no sistema com Provisão para Perdas (PVL) de 80%. Equilibra operação e técnica.",
        "desc_agressiva": "Mantém valor de custo integral (R$ 10/un). Justifica como 'estoque de marketing'.",
        "conservadora": {"resultado": -15, "risco": -5, "esg": +5, "tecnica": +15},
        "moderada": {"resultado": -8, "risco": +5, "esg": +5, "tecnica": +10},
        "agressiva": {"resultado": +5, "risco": +20, "esg": -10, "tecnica": -10}
    },
    "verao_sustentavel": {
        "titulo": "3. Coleção Verão (Custo R$ 30k vs. VRL R$ 10k)",
        "contexto": "A coleção ocupa 40% do estoque. O custo é R$ 30 mil, mas o valor de mercado (VRL) caiu para R$ 10 mil.",
        "conflito": "Diretoria: 'Não faça promoções agressivas para não desvalorizar a marca!' | Vitor: 'O CPC 16 exige o ajuste ao VRL!'",
        "desc_conservadora": "Reconhece perda integral de R$ 20.000 imediatamente. Rigor absoluto com a norma.",
        "desc_moderada": "Reconhece perda parcial e detalha a estratégia de marca em Nota Explicativa.",
        "desc_agressiva": "Mantém os R$ 30 mil. Alega que o valor 'retornará' no próximo verão (Sazonalidade).",
        "conservadora": {"resultado": -20, "risco": -10, "esg": +5, "tecnica": +15},
        "moderada": {"resultado": -10, "risco": +5, "esg": +5, "tecnica": +8},
        "agressiva": {"resultado": +10, "risco": +25, "esg": -5, "tecnica": -15}
    },
    "consignacao": {
        "titulo": "4. Consignação (Influenciadores)",
        "contexto": "800 itens recebidos (R$ 80/un). A Refaz ganha 60% da venda. Devemos registrar essas peças como nosso Ativo?",
        "conflito": "Daniela: 'Se o estoque parecer maior, atraímos mais investidores!' | Vitor: 'O controle e riscos são diferentes.'",
        "desc_conservadora": "Controle apenas extracontábil (Contas de Compensação). Não infla o Ativo.",
        "desc_moderada": "Registra em conta segregada com passivo correspondente. Transparência na posse.",
        "desc_agressiva": "Registra como estoque próprio. Aumenta artificialmente o tamanho da empresa.",
        "conservadora": {"resultado": 0, "risco": -5, "esg": +5, "tecnica": +10},
        "moderada": {"resultado": 0, "risco": +5, "esg": +5, "tecnica": +5},
        "agressiva": {"resultado": +25, "risco": +30, "esg": -10, "tecnica": -20}
    },
    "prove_em_casa": {
        "titulo": "5. Venda Condicional (Prove em Casa)",
        "contexto": "300 peças enviadas, mas apenas 180 confirmadas. Vitor precisa decidir o momento da receita (CPC 47).",
        "conflito": "Renata: 'O produto saiu da prateleira, já é venda!' | Vitor: 'O cliente ainda pode devolver tudo em 7 dias.'",
        "desc_conservadora": "Reconhece receita apenas após os 7 dias (Confirmação). Prudência máxima.",
        "desc_moderada": "Reconhece as 300 peças com Provisão de Devolução (estimativa de 40%).",
        "desc_agressiva": "Reconhece as 300 peças como receita definitiva no envio. Infla o giro de estoque.",
        "conservadora": {"resultado": -10, "risco": -10, "esg": +5, "tecnica": +15},
        "moderada": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": +8},
        "agressiva": {"resultado": +20, "risco": +25, "esg": -5, "tecnica": -15}
    },
    "fretes": {
        "titulo": "6. Logística e Fretes (Custo ou Despesa?)",
        "contexto": "R$ 6.400 de frete na consignação recebida e R$ 4.500 no 'Prove em Casa'. Onde alocar esses custos?",
        "conflito": "Financeiro: 'Jogue no estoque para não cair o lucro do mês!' | Vitor: 'Nem todo frete é custo de aquisição.'",
        "desc_conservadora": "Lança 100% como despesa logística do período. Reduz o lucro imediato.",
        "desc_moderada": "Capitaliza no estoque apenas o frete proporcional às peças vendidas (Rateio).",
        "desc_agressiva": "Ativa todo o frete no estoque. Posterga a despesa e aumenta o Ativo.",
        "conservadora": {"resultado": -12, "risco": -5, "esg": +2, "tecnica": +10},
        "moderada": {"resultado": -5, "risco": +5, "esg": +5, "tecnica": +5},
        "agressiva": {"resultado": +15, "risco": +20, "esg": -5, "tecnica": -10}
    }
}

# =============================
# CARTAS DE EVENTO (GAMIFICAÇÃO)
# =============================

eventos_disponiveis = {
    "fiscalizacao": {
        "titulo": "🚨 FISCALIZAÇÃO SURPRESA!",
        "mensagem": "Receita Federal identificou falhas no compliance. Grupos com RISCO > 30 perdem 20 pts de lucro!",
        "impacto_risco_limite": 30,
        "penalidade": -20
    },
    "investidor": {
        "titulo": "💰 APORTE INVESTIDOR ESG",
        "mensagem": "Fundo de impacto premiou a transparência. Grupos com ESG > 60 ganham 15 pts de lucro!",
        "impacto_esg_minimo": 60,
        "bonus": 15
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
    teams = {}
    dilemas_usados = []
    escolhas_temporarias = {}
    nome1 = request.form["grupo1"]
    nome2 = request.form["grupo2"]
    teams["alpha"] = criar_time(nome1)
    teams["beta"] = criar_time(nome2)
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    dilemas_disponiveis = {k: v for k, v in dilemas.items() if k not in dilemas_usados}
    jogo_encerrado = len(dilemas_disponiveis) == 0
    equipe_vencedora = max(teams.values(), key=lambda x: x["resultado"]) if teams else None
    return render_template("dashboard.html", teams=teams, dilemas=dilemas_disponiveis, 
                           dilemas_usados=dilemas_usados, jogo_encerrado=jogo_encerrado, 
                           equipe_vencedora=equipe_vencedora)

@app.route("/dilema/<id_dilema>")
def mostrar_dilema(id_dilema):
    votos_atuais = escolhas_temporarias.get(id_dilema, {})
    return render_template("dilema.html", dilema=dilemas[id_dilema], id_dilema=id_dilema, 
                           teams=teams, votos_atuais=votos_atuais)

@app.route("/registrar/<id_dilema>/<perfil>/<time>")
def registrar(id_dilema, perfil, time):
    global escolhas_temporarias
    if id_dilema not in escolhas_temporarias: escolhas_temporarias[id_dilema] = {}
    escolhas_temporarias[id_dilema][time] = perfil

    if len(escolhas_temporarias[id_dilema]) == 2:
        for t_key, p_escolhido in escolhas_temporarias[id_dilema].items():
            impacto = dilemas[id_dilema][p_escolhido]
            for stat in ["resultado", "risco", "esg", "tecnica"]:
                teams[t_key][stat] += impacto[stat]
        dilemas_usados.append(id_dilema)
        del escolhas_temporarias[id_dilema]
        return redirect(url_for("dashboard"))
    return redirect(url_for("mostrar_dilema", id_dilema=id_dilema))

@app.route("/auditar/<time_key>")
def auditar(time_key):
    global teams
    if time_key in teams:
        if teams[time_key]["auditorias_restantes"] > 0:
            teams[time_key]["tecnica"] -= 15
            teams[time_key]["resultado"] -= 10
            teams[time_key]["auditorias_restantes"] -= 1
    return redirect(url_for("dashboard"))

@app.route("/disparar_evento/<id_evento>")
def disparar_evento(id_evento):
    evento = eventos_disponiveis.get(id_evento)
    if evento:
        for t_key in teams:
            if id_evento == "fiscalizacao":
                if teams[t_key]["risco"] > evento["impacto_risco_limite"]:
                    teams[t_key]["resultado"] += evento["penalidade"]
            elif id_evento == "investidor":
                if teams[t_key]["esg"] > evento["impacto_esg_minimo"]:
                    teams[t_key]["resultado"] += evento["bonus"]
    return redirect(url_for("dashboard"))

@app.route("/reiniciar")
def reiniciar():
    global teams, dilemas_usados, escolhas_temporarias
    teams, dilemas_usados, escolhas_temporarias = {}, [], {}
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)