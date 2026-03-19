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

# ⏱️ CONTROLE DE TEMPO
tempo_inicio_dilema = None
TEMPO_LIMITE = 600  # 10 minutos

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
        "historico": [],
        "perfil_contagem": {
            "Conservador": 0,
            "Moderado": 0,
            "Agressivo": 0
        }
    }

# =============================
# SCORE INTELIGENTE
# =============================

def calcular_score(t):
    return round(
        t["resultado"]
        - (t["risco"] * 1.2)
        + t["tecnica"]
        + t["esg"],
        2
    )

# =============================
# DILEMAS (MANTIDOS)
# =============================

dilemas = {
    # ⚠️ MANTENHA SEU BLOCO COMPLETO AQUI (não alterado)
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
    dilemas_disp = {k: v for k, v in dilemas.items() if k not in dilemas_usados}
    jogo_encerrado = len(dilemas_disp) == 0

    for t in teams.values():
        t["score"] = calcular_score(t)

        if sum(t["perfil_contagem"].values()) > 0:
            t["perfil_predominante"] = max(
                t["perfil_contagem"],
                key=t["perfil_contagem"].get
            )
        else:
            t["perfil_predominante"] = "Aguardando"

    equipe_venc = max(teams.values(), key=lambda x: x["score"]) if teams else None

    return render_template(
        "dashboard.html",
        teams=teams,
        dilemas=dilemas_disp,
        jogo_encerrado=jogo_encerrado,
        equipe_vencedora=equipe_venc,
        rodada=rodada_atual,
        total_rodadas=TOTAL_DILEMAS
    )


# =============================
# DILEMA COM CRONÔMETRO
# =============================

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


# =============================
# REGISTRO COM BLOQUEIO DE TEMPO
# =============================

@app.route("/registrar/<id_dilema>/<perfil>/<time_key>")
def registrar(id_dilema, perfil, time_key):
    global escolhas_temporarias, rodada_atual, tempo_inicio_dilema

    # 🚨 BLOQUEIO POR TEMPO
    if tempo_inicio_dilema:
        tempo_passado = time.time() - tempo_inicio_dilema
        if tempo_passado > TEMPO_LIMITE:
            return redirect(url_for("mostrar_dilema", id_dilema=id_dilema))

    if id_dilema not in escolhas_temporarias:
        escolhas_temporarias[id_dilema] = {}

    escolhas_temporarias[id_dilema][time_key] = perfil

    # TODOS VOTARAM
    if len(escolhas_temporarias[id_dilema]) == len(teams):

        for t_k, p_esc in escolhas_temporarias[id_dilema].items():
            dados = dilemas[id_dilema]["opcoes"][p_esc]

            for stat in ["resultado", "risco", "esg", "tecnica"]:
                teams[t_k][stat] += dados["impacto"][stat]

            teams[t_k]["motivos"].append(dados["motivo"])

            teams[t_k]["historico"].append({
                "rodada": rodada_atual,
                "perfil": p_esc,
                "decisao": dados["texto"],
                "motivo": dados["motivo"]
            })

            teams[t_k]["perfil_contagem"][p_esc] += 1

        dilemas_usados.append(id_dilema)
        del escolhas_temporarias[id_dilema]

        rodada_atual += 1

        # 🔄 RESET DO TEMPO PARA PRÓXIMO DILEMA
        tempo_inicio_dilema = None

        return redirect(url_for("dashboard"))

    return redirect(url_for("mostrar_dilema", id_dilema=id_dilema))


# =============================
# AJUSTE DO PROFESSOR
# =============================

@app.route("/ajuste/<time_key>/<tipo>")
def ajuste(time_key, tipo):

    if time_key in teams:

        if tipo == "bonus":
            teams[time_key]["resultado"] += 10
            teams[time_key]["tecnica"] += 10
            teams[time_key]["motivos"].append(
                "Bônus do professor: excelente fundamentação contábil."
            )

        elif tipo == "penalidade":
            teams[time_key]["resultado"] -= 10
            teams[time_key]["tecnica"] -= 10
            teams[time_key]["motivos"].append(
                "Penalidade do professor: falha na sustentação técnica."
            )

    return redirect(url_for("dashboard"))
    
@app.route("/resultado_final")
def resultado_final():

    for t in teams.values():
        t["score"] = calcular_score(t)

        if sum(t["perfil_contagem"].values()) > 0:
            t["perfil_predominante"] = max(
                t["perfil_contagem"],
                key=t["perfil_contagem"].get
            )
        else:
            t["perfil_predominante"] = "Indefinido"

    ranking = sorted(teams.values(), key=lambda x: x["score"], reverse=True)
    vencedor = ranking[0] if ranking else None

    return render_template(
        "final.html",
        ranking=ranking,
        vencedor=vencedor
    )


# =============================
# RESET
# =============================

@app.route("/reiniciar")
def reiniciar():
    global teams, dilemas_usados, escolhas_temporarias, rodada_atual, tempo_inicio_dilema

    teams = {}
    dilemas_usados = []
    escolhas_temporarias = {}
    rodada_atual = 1
    tempo_inicio_dilema = None

    return redirect(url_for("index"))


# =============================
# EXECUÇÃO
# =============================

if __name__ == "__main__":
    app.run(debug=True)
