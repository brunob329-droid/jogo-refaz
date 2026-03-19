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
        "contexto": "A Refaz recebeu 800 peças em consignação (R$ 80/un). A empresa fica com 60% na venda.",
        "avatar_1": {"nome": "Daniela (CEO)", "fala": "Se lançarmos no Ativo, o estoque parece maior e atraímos investidores!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "Mas não temos a propriedade. O CPC 00 exige controle e riscos para ser Ativo."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Não reconhecer no Ativo (controle extracontábil).",
                "motivo": "Seguiu CPC 00: Essência sobre a forma e não inflou o Ativo indevidamente.",
                "impacto": {"resultado": 0, "risco": -5, "esg": +5, "tecnica": +15}
            },
            "Moderado": {
                "texto": "Registrar em conta segregada com passivo correspondente.",
                "motivo": "Buscou transparência, mas gerou registro de bens de terceiros no balanço patrimonial.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": 0}
            },
            "Agressivo": {
                "texto": "Registrar como estoque próprio para inflar o balanço.",
                "motivo": "Erro Técnico: Inflou o Ativo com ativos de terceiros para parecer maior ao mercado.",
                "impacto": {"resultado": +25, "risco": +30, "esg": -10, "tecnica": -20}
            }
        }
    },
    "prove_em_casa": {
        "titulo": "2. Venda Condicional (Prove em Casa)",
        "contexto": "300 peças enviadas; 180 confirmadas. O cliente tem 7 dias para devolver.",
        "avatar_1": {"nome": "Renata (Operações)", "fala": "O produto saiu, já é faturamento!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "O CPC 47 diz que sem transferência de controle, não há receita."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Reconhecer receita apenas das 180 peças confirmadas.",
                "motivo": "Aplicou CPC 47: Só reconheceu receita após o aceite definitivo do cliente.",
                "impacto": {"resultado": -10, "risco": -10, "esg": +5, "tecnica": +15}
            },
            "Moderado": {
                "texto": "Reconhecer receita total com Provisão para Devoluções.",
                "motivo": "Antecipou receita baseada em estimativa, assumindo risco de reversão.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": +5}
            },
            "Agressivo": {
                "texto": "Reconhecer receita total das 300 peças no envio.",
                "motivo": "Infrou o faturamento sem garantir a transferência de controle do bem.",
                "impacto": {"resultado": +20, "risco": +25, "esg": -5, "tecnica": -15}
            }
        }
    },
    "fretes": {
        "titulo": "3. Logística e Fretes (Custo ou Despesa?)",
        "contexto": "Fretes de peças consignadas e de envio para clientes provarem.",
        "avatar_1": {"nome": "Financeiro", "fala": "Jogue no custo do estoque para não derrubar o lucro agora!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "Frete de venda e de itens de terceiros não é custo de aquisição (CPC 16)."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Lançar 100% como despesa de vendas no resultado.",
                "motivo": "Prudência: Lançou gastos logísticos como despesa do período conforme o CPC 16.",
                "impacto": {"resultado": -12, "risco": -5, "esg": +2, "tecnica": +10}
            },
            "Moderado": {
                "texto": "Capitalizar frete da consignação e lançar venda como despesa.",
                "motivo": "Capitalizou custo em itens que não compõem o estoque próprio da entidade.",
                "impacto": {"resultado": -5, "risco": +5, "esg": +5, "tecnica": -5}
            },
            "Agressivo": {
                "texto": "Ativar todos os fretes no Estoque (Ativo).",
                "motivo": "Diferimento indevido de despesas para mascarar o resultado mensal.",
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
