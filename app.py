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
        "auditorias_restantes": 2,
        "motivos": [], # Guarda o histórico das decisões tomadas
        "perfil_contagem": {"Conservador": 0, "Moderado": 0, "Agressivo": 0} # Para definir o perfil final
    }

# ==========================================
# DILEMAS (COM DECISÕES TÉCNICAS REAIS E AVATARES)
# ==========================================

dilemas = {
    "consignacao": {
        "titulo": "1. Consignação (Influenciadores e Parceiros)",
        "contexto": "A Refaz recebeu 800 peças em consignação (R$ 80/un). A empresa fica com 60% na venda. Além disso, estuda enviar peças próprias para terceiros venderem.",
        "avatar_1": {"nome": "Daniela (CEO)", "fala": "Se lançarmos as 800 peças recebidas no nosso Ativo, o estoque parece maior e atraímos mais investidores focados em impacto!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "Mas não temos a propriedade, Daniela. E sobre enviar nossas peças para fora, os riscos mudam completamente."},
        "tem_contabilizacao": True, # Exige quadro de contabilização
        "opcoes": {
            "Conservador": {
                "texto": "Não reconhecer as peças recebidas no Ativo (controle extracontábil). As peças enviadas a terceiros continuam no estoque da Refaz até a venda final.",
                "motivo": "Priorizou a essência sobre a forma jurídica (CPC 00), mantendo controle extracontábil da consignação e não inflando o Ativo.",
                "impacto": {"resultado": 0, "risco": -5, "esg": +5, "tecnica": +15}
            },
            "Moderado": {
                "texto": "Registrar as peças recebidas em conta segregada com um passivo correspondente para dar transparência, e reconhecer receita na emissão da nota de remessa.",
                "motivo": "Buscou um meio-termo na consignação, mas cometeu um leve desvio técnico ao antecipar receitas na remessa.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": -5}
            },
            "Agressivo": {
                "texto": "Registrar as 800 peças como estoque próprio para inflar o balanço e registrar as peças enviadas a terceiros como receita imediata.",
                "motivo": "Assumiu alto risco fiscal e contábil ao inflar o Ativo com peças de terceiros e registrar venda sem transferência de controle.",
                "impacto": {"resultado": +25, "risco": +30, "esg": -10, "tecnica": -20}
            }
        }
    },
    "prove_em_casa": {
        "titulo": "2. Venda Condicional (Prove em Casa)",
        "contexto": "300 peças foram enviadas para clientes provarem por 7 dias. Até o fechamento do balanço, apenas 180 peças foram confirmadas como venda definitiva. Custo médio: R$ 22. Preço de venda: R$ 70.",
        "avatar_1": {"nome": "Renata (Operações)", "fala": "O produto já saiu da prateleira e está na casa do cliente! Para mim, isso já é faturamento garantido!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "O CPC 47 diz que a transferência física não é transferência de controle. O cliente ainda pode devolver 120 peças."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Reconhecer receita (R$ 12.600) e CMV (R$ 3.960) apenas das 180 peças confirmadas. As 120 peças restantes continuam no estoque em uma subconta 'estoque em poder de clientes'.",
                "motivo": "Aplicou rigorosamente o CPC 47, reconhecendo receita apenas após a transferência definitiva de controle pelo cliente.",
                "impacto": {"resultado": -10, "risco": -10, "esg": +5, "tecnica": +15}
            },
            "Moderado": {
                "texto": "Reconhecer a receita total das 300 peças, mas constituir uma Provisão para Devoluções baseada no histórico esperado.",
                "motivo": "Reconheceu receita antecipada no 'prove em casa' compensando com provisão para devoluções.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": +5}
            },
            "Agressivo": {
                "texto": "Reconhecer a receita de todas as 300 peças enviadas imediatamente no envio para melhorar o giro de estoque e o lucro do período.",
                "motivo": "Infrou artificialmente o faturamento e o lucro reconhecendo vendas que ainda não foram aceitas pelo cliente.",
                "impacto": {"resultado": +20, "risco": +25, "esg": -5, "tecnica": -15}
            }
        }
    },
    "fretes": {
        "titulo": "3. Logística e Fretes (Custo ou Despesa?)",
        "contexto": "Temos R$ 6.400 de frete pago para receber as peças em consignação, e R$ 4.500 de frete do 'prove em casa'.",
        "avatar_1": {"nome": "Financeiro", "fala": "Não podemos jogar tudo isso como despesa do mês! Jogue no custo do estoque para não derrubar nosso lucro agora!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "Nem todo frete é custo de aquisição (CPC 16). Não temos propriedade das peças consignadas, e as outras já saíram para o cliente."},
        "tem_contabilizacao": False,
        "opcoes": {
            "Conservador": {
                "texto": "Lançar 100% dos fretes de consignação recebida e envios aos clientes diretamente como despesa de vendas/comercial no resultado.",
                "motivo": "Evitou capitalizar custos indevidos, lançando fretes logísticos como despesa do período conforme normas técnicas.",
                "impacto": {"resultado": -12, "risco": -5, "esg": +2, "tecnica": +10}
            },
            "Moderado": {
                "texto": "Capitalizar no estoque o frete da consignação e lançar o frete das vendas como despesa.",
                "motivo": "Capitalizou de forma incorreta o frete de itens que não são de propriedade da empresa (consignados).",
                "impacto": {"resultado": -5, "risco": +5, "esg": +5, "tecnica": -5}
            },
            "Agressivo": {
                "texto": "Ativar todos os valores de frete no Ativo (Estoque), postergando o reconhecimento da despesa para aumentar a margem atual.",
                "motivo": "Postergou despesas agressivamente, capitalizando fretes operacionais como ativo para mascarar o resultado.",
                "impacto": {"resultado": +15, "risco": +20, "esg": -5, "tecnica": -15}
            }
        }
    }
}

# =============================
# CARTAS DE EVENTO
# =============================

eventos_disponiveis = {
    "fiscalizacao": {
        "titulo": "🚨 FISCALIZAÇÃO SURPRESA!",
        "mensagem": "Receita Federal identificou falhas no compliance.",
        "impacto_risco_limite": 30,
        "penalidade": -20
    },
    "investidor": {
        "titulo": "💰 APORTE INVESTIDOR ESG",
        "mensagem": "Fundo de impacto premiou a transparência.",
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
    
    nomes_grupos = request.form.getlist("nomes_grupos")
    if not nomes_grupos:
        nomes_grupos = ["Grupo Alpha", "Grupo Beta"]

    for i, nome in enumerate(nomes_grupos):
        if nome.strip():
            t_key = f"time_{i}"
            teams[t_key] = criar_time(nome)
            
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    dilemas_disponiveis = {k: v for k, v in dilemas.items() if k not in dilemas_usados}
    jogo_encerrado = len(dilemas_disponiveis) == 0
    equipe_vencedora = max(teams.values(), key=lambda x: x["resultado"]) if teams else None
    
    # Define o perfil predominante dinamicamente para exibição
    for key, time in teams.items():
        if time["perfil_contagem"]:
            perfil_max = max(time["perfil_contagem"], key=time["perfil_contagem"].get)
            time["perfil_predominante"] = perfil_max
        else:
            time["perfil_predominante"] = "N/A"

    return render_template("dashboard.html", teams=teams, dilemas=dilemas_disponiveis, 
                           dilemas_usados=dilemas_usados, jogo_encerrado=jogo_encerrado, 
                           equipe_vencedora=equipe_vencedora)
@app.route('/professor_ajuste/<time_key>/<tipo>')
def professor_ajuste(time_key, tipo):
    if time_key in teams:
        if tipo == 'bonus':
            teams[time_key]['resultado'] += 10
            teams[time_key]['tecnica'] += 5
            # Opcional: adicionar uma mensagem de log
            teams[time_key]['motivos'].append("Bônus: Excelente sustentação técnica no quadro.")
        elif tipo == 'penalidade':
            teams[time_key]['resultado'] -= 10
            teams[time_key]['tecnica'] -= 5
            teams[time_key]['motivos'].append("Ressalva: Falha na demonstração de D/C no quadro.")
            
    return redirect(url_for('dashboard'))

@app.route("/dilema/<id_dilema>")
def mostrar_dilema(id_dilema):
    votos_atuais = escolhas_temporarias.get(id_dilema, {})
    return render_template("dilema.html", dilema=dilemas[id_dilema], id_dilema=id_dilema, 
                           teams=teams, votos_atuais=votos_atuais)

@app.route("/registrar/<id_dilema>/<perfil>/<time_key>")
def registrar(id_dilema, perfil, time_key):
    global escolhas_temporarias
    if id_dilema not in escolhas_temporarias: 
        escolhas_temporarias[id_dilema] = {}
    
    escolhas_temporarias[id_dilema][time_key] = perfil

    # Finaliza o dilema quando todos os grupos cadastrados votarem
    if len(escolhas_temporarias[id_dilema]) == len(teams):
        for t_key, p_escolhido in escolhas_temporarias[id_dilema].items():
            
            # Pega os dados da opção escolhida (texto, motivo, impacto)
            opcao_dados = dilemas[id_dilema]["opcoes"][p_escolhido]
            impacto = opcao_dados["impacto"]
            motivo = opcao_dados["motivo"]
            
            # Aplica os impactos numéricos
            for stat in ["resultado", "risco", "esg", "tecnica"]:
                teams[t_key][stat] += impacto[stat]
            
            # Salva o histórico para o Dashboard
            teams[t_key]["motivos"].append(motivo)
            teams[t_key]["perfil_contagem"][p_escolhido] += 1
        
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
