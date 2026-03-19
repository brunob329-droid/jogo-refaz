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
# DILEMAS (VERSÃO COMPLETA)
# =============================

dilemas = {

    # =============================
    # DILEMA 1 - CONSIGNAÇÃO
    # =============================
    "consignacao": {
        "titulo": "1. Consignação: Reconhecimento, Controle e Risco",
        "contexto": """
A Refaz recebeu 800 peças em consignação de parceiros (brechós e influenciadores), com preço médio estimado de R$ 80 por unidade. Pelo acordo, 60% do valor da venda pertence à Refaz e 40% ao consignante, sendo o repasse realizado apenas após a venda ao consumidor final.

Apesar de estarem fisicamente no estoque, essas peças não pertencem juridicamente à empresa. Daniela considera registrá-las no ativo para demonstrar maior volume operacional e atratividade para investidores.

Paralelamente, surge a estratégia inversa: enviar peças próprias da Refaz para venda por terceiros. Nesse caso, as mercadorias deixam o estoque físico, mas continuam sendo propriedade da empresa até a venda.

O desafio envolve definir: o que é controle? Quando reconhecer ativo? Como evitar superavaliação patrimonial? E como garantir governança e rastreabilidade das peças fora da empresa?
        """,

        "avatar_1": {
            "nome": "Daniela (CEO)",
            "fala": "Se registrarmos essas peças no ativo, mostramos crescimento e estrutura para investidores."
        },

        "avatar_2": {
            "nome": "Vitor (Contador)",
            "fala": "Sem controle econômico real, reconhecer como ativo pode distorcer completamente o balanço."
        },

        "tem_contabilizacao": True,

        "opcoes": {

            "Conservador": {
                "texto": """
Não reconhecer as peças consignadas no ativo, mantendo controle extracontábil e divulgação em notas explicativas. Para peças enviadas a terceiros, manter no estoque em conta segregada ("estoque em poder de terceiros") até a venda final.
                """,
                "motivo": "Aplicou essência sobre a forma, evitando superavaliação do ativo e garantindo rastreabilidade.",
                "impacto": {"resultado": 0, "risco": -5, "esg": +5, "tecnica": +15}
            },

            "Moderado": {
                "texto": """
Registrar peças consignadas em conta de ativo com passivo correspondente, evidenciando a operação no balanço, ainda que sem transferência de propriedade plena.
                """,
                "motivo": "Buscou transparência, mas comprometeu a pureza conceitual do ativo.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": 0}
            },

            "Agressivo": {
                "texto": """
Registrar as peças consignadas como estoque próprio e reconhecer receita antecipada na remessa para terceiros.
                """,
                "motivo": "Inflou ativos e receitas sem transferência de controle.",
                "impacto": {"resultado": +25, "risco": +30, "esg": -10, "tecnica": -20}
            }
        }
    },

    # =============================
    # DILEMA 2 - PROVE EM CASA
    # =============================
    "prove_em_casa": {
        "titulo": "2. Venda Condicional: 'Prove em Casa'",
        "contexto": """
Na estratégia "prove em casa", a Refaz enviou 300 peças para clientes experimentarem por até 7 dias. O cliente pode devolver sem custo.

Ao final do período, apenas 180 peças foram confirmadas como venda. Cada peça possui preço médio de R$ 70 e custo de R$ 22.

A dúvida central é: o envio já configura venda? Ou o reconhecimento só ocorre após aceitação do cliente?

Reconhecer antecipadamente aumenta faturamento e lucro, mas pode gerar distorções relevantes. Já o reconhecimento apenas na confirmação pode reduzir desempenho no curto prazo.

A decisão impacta diretamente receita, CMV, estoque e credibilidade das demonstrações.
        """,

        "avatar_1": {
            "nome": "Renata (Operações)",
            "fala": "O produto já saiu! Isso deveria contar como venda."
        },

        "avatar_2": {
            "nome": "Vitor (Contador)",
            "fala": "Sem aceitação, não houve transferência de controle."
        },

        "tem_contabilizacao": True,

        "opcoes": {

            "Conservador": {
                "texto": """
Reconhecer receita apenas das 180 peças confirmadas. Manter as demais em conta de "estoque em poder de clientes".
                """,
                "motivo": "Seguiu o CPC 47: receita só com transferência de controle.",
                "impacto": {"resultado": -10, "risco": -10, "esg": +5, "tecnica": +15}
            },

            "Moderado": {
                "texto": """
Reconhecer as 300 peças com provisão para devolução baseada em estimativa.
                """,
                "motivo": "Utilizou estimativa, mas antecipou receita.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": +5}
            },

            "Agressivo": {
                "texto": """
Reconhecer receita total no envio das 300 peças.
                """,
                "motivo": "Antecipou receita sem base econômica.",
                "impacto": {"resultado": +20, "risco": +25, "esg": -5, "tecnica": -15}
            }
        }
    },

    # =============================
    # DILEMA 3 - FRETES
    # =============================
    "fretes": {
        "titulo": "3. Fretes: Custo, Despesa ou Estratégia?",
        "contexto": """
A Refaz incorreu em diversos custos logísticos:

• R$ 6.400 para transporte de peças recebidas em consignação  
• R$ 4.500 em fretes do modelo "prove em casa"  
• Possibilidade de subsídio de frete (R$ 14.400/mês)

A dúvida é: esses valores devem ser ativados como estoque ou reconhecidos como despesa?

A capitalização pode melhorar artificialmente o resultado, enquanto o reconhecimento imediato reduz lucro no curto prazo.

Além disso, há fretes que não resultam em venda (devoluções), aumentando a complexidade do tratamento contábil.

A decisão impacta diretamente margem, ativo, resultado e percepção de eficiência operacional.
        """,

        "avatar_1": {
            "nome": "Financeiro",
            "fala": "Se jogarmos tudo como despesa, o lucro desaparece."
        },

        "avatar_2": {
            "nome": "Vitor (Contador)",
            "fala": "Frete sem geração de ativo não pode ser capitalizado."
        },

        "tem_contabilizacao": False,

        "opcoes": {

            "Conservador": {
                "texto": """
Reconhecer todos os fretes como despesa operacional, exceto quando diretamente atribuíveis a estoque próprio.
                """,
                "motivo": "Evitou ativação indevida.",
                "impacto": {"resultado": -12, "risco": -5, "esg": +2, "tecnica": +10}
            },

            "Moderado": {
                "texto": """
Capitalizar parcialmente fretes de entrada, mesmo em consignação.
                """,
                "motivo": "Erro conceitual leve.",
                "impacto": {"resultado": -5, "risco": +5, "esg": +5, "tecnica": -5}
            },

            "Agressivo": {
                "texto": """
Ativar todos os fretes como estoque.
                """,
                "motivo": "Distorção contábil para melhorar resultado.",
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

    nomes = request.form.getlist("nomes_grupos")

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
