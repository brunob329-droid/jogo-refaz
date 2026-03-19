from flask import Flask, render_template, request, redirect, url_for
import time

app = Flask(__name__)

# =============================
# ESTADO DO JOGO
# =============================

teams = {}
dilemas_usados = []
escolhas_temporarias = {}

rodada_atual = 1
TOTAL_DILEMAS = 3

tempo_inicio_dilema = None
TEMPO_LIMITE = 600  # 10 minutos

# =============================
# FUNÇÕES
# =============================

def criar_time(nome):
    return {
        "nome": nome,
        "resultado": 100,
        "risco": 0,
        "esg": 50,
        "tecnica": 50,
        "motivos": [],
        "historico": [],
        "perfil_contagem": {
            "Conservador": 0,
            "Moderado": 0,
            "Agressivo": 0
        }
    }

def calcular_score(t):
    return round(
        t["resultado"]
        - (t["risco"] * 1.2)
        + t["tecnica"]
        + t["esg"],
        2
    )

# =============================
# DILEMAS (OBRIGATÓRIO ESTAR COMPLETO)
# =============================

dilemas = {

    "consignacao": {
        "titulo": "1. Consignação: Reconhecimento, Controle e Risco",
        "contexto": "A Refaz recebeu 800 peças em consignação...",
        "avatar_1": {"nome": "Daniela", "fala": "Registrar no ativo melhora percepção."},
        "avatar_2": {"nome": "Vitor", "fala": "Sem controle, não há ativo."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Não reconhecer no ativo.",
                "motivo": "Essência sobre forma.",
                "impacto": {"resultado": 0, "risco": -5, "esg": 5, "tecnica": 15}
            },
            "Moderado": {
                "texto": "Registrar com passivo.",
                "motivo": "Transparência parcial.",
                "impacto": {"resultado": 5, "risco": 10, "esg": 5, "tecnica": 0}
            },
            "Agressivo": {
                "texto": "Registrar como estoque próprio.",
                "motivo": "Superavaliação.",
                "impacto": {"resultado": 25, "risco": 30, "esg": -10, "tecnica": -20}
            }
        }
    },

    "prove": {
        "titulo": "2. Prove em Casa",
        "contexto": "Clientes recebem peças e podem devolver.",
        "avatar_1": {"nome": "Renata", "fala": "Saiu = vendeu."},
        "avatar_2": {"nome": "Vitor", "fala": "Sem aceitação, não há receita."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Reconhecer só o vendido.",
                "motivo": "Seguiu CPC 47.",
                "impacto": {"resultado": -10, "risco": -10, "esg": 5, "tecnica": 15}
            },
            "Moderado": {
                "texto": "Estimativa com provisão.",
                "motivo": "Antecipação moderada.",
                "impacto": {"resultado": 5, "risco": 10, "esg": 5, "tecnica": 5}
            },
            "Agressivo": {
                "texto": "Reconhecer tudo.",
                "motivo": "Antecipação indevida.",
                "impacto": {"resultado": 20, "risco": 25, "esg": -5, "tecnica": -15}
            }
        }
    },

    "fretes": {
        "titulo": "3. Fretes",
        "contexto": "Custos logísticos relevantes.",
        "avatar_1": {"nome": "Financeiro", "fala": "Impacta lucro."},
        "avatar_2": {"nome": "Vitor", "fala": "Nem tudo é ativo."},
        "tem_contabilizacao": False,
        "opcoes": {
            "Conservador": {
                "texto": "Despesa.",
                "motivo": "Evita distorção.",
                "impacto": {"resultado": -12, "risco": -5, "esg": 2, "tecnica": 10}
            },
            "Moderado": {
                "texto": "Capitalizar parcialmente.",
                "motivo": "Erro leve.",
                "impacto": {"resultado": -5, "risco": 5, "esg": 5, "tecnica": -5}
            },
            "Agressivo": {
                "texto": "Ativar tudo.",
                "motivo": "Manipulação.",
                "impacto": {"resultado": 15, "risco": 20, "esg": -5, "tecnica": -15}
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
    global teams, dilemas_usados, escolhas_temporarias, rodada_atual, tempo_inicio_dilema

    teams = {}
    dilemas_usados = []
    escolhas_temporarias = {}
    rodada_atual = 1
    tempo_inicio_dilema = None

    nomes = request.form.getlist("nomes_grupos")
    nomes = [n.strip() for n in nomes if n.strip()]

    if not nomes:
        nomes = ["Grupo A", "Grupo B"]

    for i, nome in enumerate(nomes):
        teams[f"time_{i}"] = criar_time(nome)

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():

    if not teams:
        return redirect(url_for("index"))

    dilemas_disp = {k: v for k, v in dilemas.items() if k not in dilemas_usados}
    jogo_encerrado = len(dilemas_disp) == 0

    for t in teams.values():
        t["score"] = calcular_score(t)

        if sum(t["perfil_contagem"].values()) > 0:
            t["perfil_predominante"] = max(t["perfil_contagem"], key=t["perfil_contagem"].get)
        else:
            t["perfil_predominante"] = "Aguardando"

    # 🚫 NÃO MOSTRA LÍDER NO INÍCIO
    equipe_venc = None
    if any(t["historico"] for t in teams.values()):
        equipe_venc = max(teams.values(), key=lambda x: x["score"])

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
    global tempo_inicio_dilema

    if tempo_inicio_dilema is None:
        tempo_inicio_dilema = time.time()

    votos = escolhas_temporarias.get(id_dilema, {})

    tempo_passado = int(time.time() - tempo_inicio_dilema)
    tempo_restante = TEMPO_LIMITE - tempo_passado

    return render_template(
        "dilema.html",
        dilema=dilemas[id_dilema],
        id_dilema=id_dilema,
        teams=teams,
        votos_atuais=votos,
        tempo_restante=max(0, tempo_restante)
    )


@app.route("/registrar/<id_dilema>/<perfil>/<time_key>")
def registrar(id_dilema, perfil, time_key):
    global escolhas_temporarias, rodada_atual, tempo_inicio_dilema

    if tempo_inicio_dilema:
        if time.time() - tempo_inicio_dilema > TEMPO_LIMITE:
            return redirect(url_for("mostrar_dilema", id_dilema=id_dilema))

    if id_dilema not in escolhas_temporarias:
        escolhas_temporarias[id_dilema] = {}

    escolhas_temporarias[id_dilema][time_key] = perfil

    if len(escolhas_temporarias[id_dilema]) == len(teams):

        for t_k, p_esc in escolhas_temporarias[id_dilema].items():
            dados = dilemas[id_dilema]["opcoes"][p_esc]

            for stat in ["resultado", "risco", "esg", "tecnica"]:
                teams[t_k][stat] += dados["impacto"][stat]

            teams[t_k]["motivos"].append(dados["motivo"])

            teams[t_k]["historico"].append({
                "rodada": rodada_atual,
                "perfil": p_esc,
                "motivo": dados["motivo"]
            })

            teams[t_k]["perfil_contagem"][p_esc] += 1

        dilemas_usados.append(id_dilema)
        del escolhas_temporarias[id_dilema]

        if rodada_atual < TOTAL_DILEMAS:
            rodada_atual += 1

        tempo_inicio_dilema = None

        return redirect(url_for("dashboard"))

    return redirect(url_for("mostrar_dilema", id_dilema=id_dilema))


@app.route("/resultado_final")
def resultado_final():

    for t in teams.values():
        t["score"] = calcular_score(t)

        if sum(t["perfil_contagem"].values()) > 0:
            t["perfil_predominante"] = max(t["perfil_contagem"], key=t["perfil_contagem"].get)
        else:
            t["perfil_predominante"] = "Indefinido"

    ranking = sorted(teams.values(), key=lambda x: x["score"], reverse=True)
    vencedor = ranking[0] if ranking else None

    return render_template("final.html", ranking=ranking, vencedor=vencedor)


@app.route("/reiniciar")
def reiniciar():
    global teams, dilemas_usados, escolhas_temporarias, rodada_atual, tempo_inicio_dilema

    teams = {}
    dilemas_usados = []
    escolhas_temporarias = {}
    rodada_atual = 1
    tempo_inicio_dilema = None

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
