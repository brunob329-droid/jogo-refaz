from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# =============================
# ESTADO DO JOGO
# =============================

teams = {}
dilemas_usados = []
escolhas_temporarias = {}
rodada_atual = 1
TOTAL_DILEMAS = 3

# =============================
# FUNÇÕES AUXILIARES
# =============================

def criar_time(nome):
    return {
        "nome": nome,
        "resultado": 100,
        "risco": 0,
        "esg": 50,
        "tecnica": 50,
        "motivos": [],
        "perfil_contagem": {
            "Conservador": 0,
            "Moderado": 0,
            "Agressivo": 0
        }
    }

# =============================
# DILEMAS
# =============================

dilemas = {
    "consignacao": {
        "titulo": "1. Gestão de Peças em Consignação (Recebidas e Enviadas)",
        "contexto": "A Refaz recebeu 800 peças em consignação...",
        "avatar_1": {"nome": "Daniela (CEO)", "fala": "Se lançarmos as 800 peças no nosso Ativo..."},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "Apesar de estarem aqui..."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Não registrar no Ativo...",
                "motivo": "Priorizou a essência sobre a forma legal.",
                "impacto": {"resultado": 0, "risco": -5, "esg": +5, "tecnica": +15}
            },
            "Moderado": {
                "texto": "Registrar em conta segregada...",
                "motivo": "Buscou transparência.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": 0}
            },
            "Agressivo": {
                "texto": "Registrar como estoque próprio...",
                "motivo": "Superavaliou o patrimônio.",
                "impacto": {"resultado": +25, "risco": +30, "esg": -10, "tecnica": -20}
            }
        }
    },

    "prove_em_casa": {
        "titulo": "2. Venda Condicional no Modelo 'Prove em Casa'",
        "contexto": "Na campanha 'Prove em Casa'...",
        "avatar_1": {"nome": "Renata (Operações)", "fala": "O produto já saiu..."},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "O cliente não é obrigado..."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Reconhecer apenas 180 peças...",
                "motivo": "Aplicou prudência.",
                "impacto": {"resultado": -10, "risco": -10, "esg": +5, "tecnica": +15}
            },
            "Moderado": {
                "texto": "Reconhecer 300 com provisão...",
                "motivo": "Usou estimativa.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": +5}
            },
            "Agressivo": {
                "texto": "Reconhecer tudo no envio...",
                "motivo": "Inflou o resultado.",
                "impacto": {"resultado": +20, "risco": +25, "esg": -5, "tecnica": -15}
            }
        }
    },

    "fretes": {
        "titulo": "3. Tratamento Contábil de Fretes Logísticos",
        "contexto": "O frete tornou-se estratégico...",
        "avatar_1": {"nome": "Financeiro", "fala": "Não podemos lançar tudo..."},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "Frete não é ativo..."},
        "tem_contabilizacao": False,
        "opcoes": {
            "Conservador": {
                "texto": "Lançar como despesa.",
                "motivo": "Evitou capitalização indevida.",
                "impacto": {"resultado": -12, "risco": -5, "esg": +2, "tecnica": +10}
            },
            "Moderado": {
                "texto": "Capitalizar parcialmente.",
                "motivo": "Erro leve de classificação.",
                "impacto": {"resultado": -5, "risco": +5, "esg": +5, "tecnica": -5}
            },
            "Agressivo": {
                "texto": "Ativar tudo.",
                "motivo": "Maquiagem contábil.",
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
    global teams, dilemas_usados, escolhas_temporarias, rodada_atual
    
    teams = {}
    dilemas_usados = []
    escolhas_temporarias = {}
    rodada_atual = 1

    nomes = request.form.getlist("nomes_groups")
    if not nomes:
        nomes = ["Grupo A", "Grupo B"]

    for i, nome in enumerate(nomes):
        if nome.strip():
            teams[f"time_{i}"] = criar_time(nome)

    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    dilemas_disp = {k: v for k, v in dilemas.items() if k not in dilemas_usados}
    jogo_encerrado = len(dilemas_disp) == 0

    equipe_venc = max(teams.values(), key=lambda x: x["resultado"]) if teams else None

    for t in teams.values():
        if sum(t["perfil_contagem"].values()) > 0:
            t["perfil_predominante"] = max(t["perfil_contagem"], key=t["perfil_contagem"].get)
        else:
            t["perfil_predominante"] = "Aguardando"

    return render_template(
        "dashboard.html",
        teams=teams,
        dilemas=dilemas_disp,
        jogo_encerrado=jogo_encerrado,
        equipe_vencedora=equipe_venc,
        rodada=rodada_atual,
        total_rodadas=TOTAL_DILEMAS
    )

@app.route("/dilema/<id_dilema>")
def mostrar_dilema(id_dilema):
    votos = escolhas_temporarias.get(id_dilema, {})
    return render_template(
        "dilema.html",
        dilema=dilemas[id_dilema],
        id_dilema=id_dilema,
        teams=teams,
        votos_atuais=votos
    )

@app.route("/registrar/<id_dilema>/<perfil>/<time_key>")
def registrar(id_dilema, perfil, time_key):
    global escolhas_temporarias, rodada_atual

    if id_dilema not in escolhas_temporarias:
        escolhas_temporarias[id_dilema] = {}

    escolhas_temporarias[id_dilema][time_key] = perfil

    # Quando todos votarem
    if len(escolhas_temporarias[id_dilema]) == len(teams):

        for t_k, p_esc in escolhas_temporarias[id_dilema].items():
            dados = dilemas[id_dilema]["opcoes"][p_esc]

            for stat in ["resultado", "risco", "esg", "tecnica"]:
                teams[t_k][stat] += dados["impacto"][stat]

            teams[t_k]["motivos"].append(dados["motivo"])
            teams[t_k]["perfil_contagem"][p_esc] += 1

        dilemas_usados.append(id_dilema)
        del escolhas_temporarias[id_dilema]

        rodada_atual += 1

        return redirect(url_for("dashboard"))

    return redirect(url_for("mostrar_dilema", id_dilema=id_dilema))

@app.route("/reiniciar")
def reiniciar():
    global teams, dilemas_usados, escolhas_temporarias, rodada_atual

    teams = {}
    dilemas_usados = []
    escolhas_temporarias = {}
    rodada_atual = 1

    return redirect(url_for("index"))

# =============================
# EXECUÇÃO
# =============================

if __name__ == "__main__":
    app.run(debug=True)
