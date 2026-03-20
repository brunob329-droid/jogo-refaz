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
    # Risco não pode ficar negativo
    risco_ajustado = max(0, t["risco"])

    # Pesos do cálculo final
    PESO_RESULTADO = 2.0
    PESO_TECNICA = 1.3
    PESO_ESG = 0.8
    PESO_RISCO = 0.6

    score = (
        (t["resultado"] * PESO_RESULTADO)
        + (t["tecnica"] * PESO_TECNICA)
        + (t["esg"] * PESO_ESG)
        - (risco_ajustado * PESO_RISCO)
    )

    return round(score, 2)

# =============================
# DILEMAS (OBRIGATÓRIO ESTAR COMPLETO)
# =============================

dilemas = {

    "consignacao": {
        "titulo": "1. Consignação: Reconhecimento, Controle e Risco",

        "contexto": """
A Refaz recebeu 800 peças em consignação de parceiros (brechós e influenciadores), com preço médio estimado de R$ 80 por unidade.

Pelo contrato, 60% do valor da venda pertence à Refaz e 40% ao consignante, sendo o repasse realizado somente após a venda ao consumidor final.

Apesar de estarem fisicamente no estoque da empresa, essas peças não pertencem juridicamente à Refaz. Ainda assim, a diretoria avalia registrá-las no ativo para demonstrar maior volume operacional e melhorar indicadores perante investidores.

Simultaneamente, a empresa também envia peças próprias para venda por terceiros, o que levanta dúvidas adicionais sobre controle, reconhecimento e evidenciação.

O dilema central envolve:
• O conceito de controle econômico (CPC 00)  
• O reconhecimento de ativos  
• O risco de superavaliação patrimonial  
• A necessidade de transparência nas demonstrações  
        """,

        "avatar_1": {
            "nome": "Daniela (CEO)",
            "fala": "Se registrarmos essas peças no ativo, mostramos crescimento e ganhamos força com investidores."
        },

        "avatar_2": {
            "nome": "Vitor (Contador)",
            "fala": "Sem controle econômico real, isso pode distorcer completamente o balanço."
        },

        "tem_contabilizacao": True,

        "opcoes": {

            "Conservador": {
                "texto": """
Não reconhecer as peças consignadas no ativo, mantendo controle extracontábil e divulgação em notas explicativas.

Para peças enviadas a terceiros, manter em conta de “estoque em poder de terceiros” até a efetiva venda.


                """,
                "motivo": "Aplicou essência sobre a forma, evitando superavaliação e garantindo conformidade conceitual.",
                "impacto": {"resultado": -15, "risco": -5, "esg": 5, "tecnica": 15}
            },

            "Moderado": {
                "texto": """
Registrar as peças em conta de ativo com contrapartida em passivo, evidenciando a operação no balanço.

Ainda que não haja transferência de propriedade, busca-se transparência informacional para usuários externos.
                """,
                "motivo": "Buscou transparência, porém com fragilidade conceitual quanto à definição de ativo.",
                "impacto": {"resultado": 5, "risco": 15, "esg": 3, "tecnica": -2}
            },

            "Agressivo": {
                "texto": """
Registrar as peças consignadas como estoque próprio e reconhecer receita antecipada no envio para terceiros.

.
                """,
                "motivo": "Inflou ativos e receitas sem base econômica, elevando risco e distorcendo a informação contábil.",
                "impacto": {"resultado": 25, "risco": 28, "esg": -8, "tecnica": -10}
            }
        }
    },

    "prove_em_casa": {
        "titulo": "2. Venda Condicional: Modelo 'Prove em Casa'",

        "contexto": """
A Refaz implementou a estratégia “prove em casa”, enviando 300 peças para clientes experimentarem por até 7 dias, com possibilidade de devolução sem custo.

Ao final do período:
• 180 peças foram efetivamente compradas  
• 120 foram devolvidas  

Cada peça possui preço médio de R$ 70 e custo de R$ 22.

A dúvida central é o momento do reconhecimento da receita:
• No envio?  
• Na aceitação do cliente?  

Essa decisão impacta diretamente:
• Receita  
• Estoques  
• Resultado  
• Confiabilidade das demonstrações  

Fundamentação relevante: CPC 47 (receita de contrato com cliente).
        """,

        "avatar_1": {
            "nome": "Renata (Operações)",
            "fala": "O produto saiu do estoque, isso já deveria contar como venda."
        },

        "avatar_2": {
            "nome": "Vitor (Contador)",
            "fala": "Sem transferência de controle, não podemos reconhecer receita."
        },

        "tem_contabilizacao": True,

        "opcoes": {

            "Conservador": {
                "texto": """
Reconhecer receita apenas das 180 peças efetivamente aceitas pelos clientes.

As demais permanecem registradas como “estoque em poder de clientes”.


                """,
                "motivo": "Aplicou corretamente o CPC 47, priorizando prudência e confiabilidade.",
                "impacto": {"resultado": -20, "risco": -10, "esg": 5, "tecnica": 15}
            },

            "Moderado": {
                "texto": """
Reconhecer as 300 peças como receita com base em estimativa de devolução, registrando provisão para perdas.


                """,
                "motivo": "Utilizou estimativa válida, porém com antecipação parcial de receita.",
                "impacto": {"resultado": 8, "risco": 15, "esg": 3, "tecnica": 0}
            },

            "Agressivo": {
                "texto": """
Reconhecer receita integral no envio das 300 peças.


                """,
                "motivo": "Antecipou receita sem base econômica, comprometendo a qualidade da informação.",
                "impacto": {"resultado": 22, "risco": 22, "esg": -5, "tecnica": -8}
            }
        }
    },

    "fretes": {
        "titulo": "3. Fretes: Custo, Despesa ou Ativo?",

        "contexto": """
A Refaz passou a incorrer em custos logísticos relevantes:

• R$ 6.400 em fretes de entrada de peças em consignação  
• R$ 4.500 em fretes do modelo “prove em casa”  
• Subsídio de frete estimado em R$ 14.400 mensais  

O dilema é definir se esses valores devem:
• Ser ativados como estoque  
• Ou reconhecidos como despesa  

O risco envolve:
• Inflar artificialmente o ativo  
• Distorcer o resultado  
• Comprometer análise de desempenho  

Fundamentação: CPC 16 (estoques).
        """,

        "avatar_1": {
            "nome": "Financeiro",
            "fala": "Se tratarmos tudo como despesa, o lucro despenca , e podemos perder os investidores ."
        },

        "avatar_2": {
            "nome": "Vitor (Contador)",
            "fala": "Só podemos ativar o que gera benefício econômico futuro."
        },

        "tem_contabilizacao": False,

        "opcoes": {

            "Conservador": {
                "texto": """
Reconhecer os fretes como despesa, exceto quando diretamente atribuíveis ao estoque próprio.


                """,
                "motivo": "Evitou ativação indevida e manteve aderência normativa.",
                "impacto": {"resultado": -18, "risco": -5, "esg": 2, "tecnica": 8}
            },

            "Moderado": {
                "texto": """
Capitalizar parcialmente fretes, incluindo itens com menor vínculo direto ao estoque.


                """,
                "motivo": "Erro conceitual moderado na classificação de custos.",
                "impacto": {"resultado": -3, "risco": 12, "esg": 5, "tecnica": -3}
            },

            "Agressivo": {
                "texto": """
Ativar todos os fretes como estoque, independentemente da natureza.


                """,
                "motivo": "Manipulação contábil para inflar resultado e ativo.",
                "impacto": {"resultado": 18, "risco": 18, "esg": -4, "tecnica": -8}
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

    # Não mostra líder no início
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

            # trava risco mínimo em zero
            teams[t_k]["risco"] = max(0, teams[t_k]["risco"])

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

    # compatível com o final.html que usa "vencedora"
    return render_template("final.html", ranking=ranking, vencedora=vencedor)


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
