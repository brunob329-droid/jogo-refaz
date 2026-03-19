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
        "motivos": [],
        "perfil_contagem": {"Conservador": 0, "Moderado": 0, "Agressivo": 0}
    }

# ==========================================
# DILEMAS COMPLETOS (CONTEXTUALIZADOS)
# ==========================================

dilemas = {
    "consignacao": {
        "titulo": "1. Gestão de Peças em Consignação (Recebidas e Enviadas)",
        "contexto": "A Refaz recebeu 800 peças em consignação para revenda (valor estimado R$ 80/un). O acordo prevê que 60% do valor fica com a Refaz e 40% é repassado ao dono apenas após a venda. Paralelamente, Daniela estuda enviar peças próprias da Refaz para influenciadores venderem. O desafio é: as 800 peças recebidas devem integrar o estoque ativo da Refaz? O registro como ativo pode inflar o patrimônio de forma inadequada já que não há transferência de propriedade? No envio de peças próprias para terceiros, o estoque deve permanecer no ativo da empresa ou ser baixado?",
        "avatar_1": {"nome": "Daniela (CEO)", "fala": "Se lançarmos as 800 peças no nosso Ativo, o estoque parece muito maior e mostramos uma estrutura mais robusta para atrair novos investidores!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "Apesar de estarem aqui, não temos a propriedade dessas peças. Registrar como nosso estoque pode superavaliar o patrimônio e distorcer indicadores de giro."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Não registrar as peças recebidas no Ativo (apenas controle extracontábil). No caso de peças enviadas a terceiros, mantê-las no Ativo em conta segregada até a venda final.",
                "motivo": "Priorizou a essência sobre a forma legal: evitou inflar o Ativo com bens de terceiros e garantiu o controle das peças enviadas a parceiros.",
                "impacto": {"resultado": 0, "risco": -5, "esg": +5, "tecnica": +15}
            },
            "Moderado": {
                "texto": "Registrar as peças recebidas em uma conta de Ativo segregada com um Passivo correspondente para dar transparência à operação no balanço.",
                "motivo": "Buscou transparência, mas registrou bens de terceiros no balanço patrimonial, o que pode poluir a análise de liquidez.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": 0}
            },
            "Agressivo": {
                "texto": "Registrar as 800 peças recebidas como estoque próprio imediatamente e reconhecer receita assim que enviar as peças da Refaz para terceiros.",
                "motivo": "Decisão Arriscada: Superavaliou o patrimônio com ativos de terceiros e antecipou receitas sem a confirmação da venda final ao consumidor.",
                "impacto": {"resultado": +25, "risco": +30, "esg": -10, "tecnica": -20}
            }
        }
    },
    "prove_em_casa": {
        "titulo": "2. Venda Condicional no Modelo 'Prove em Casa'",
        "contexto": "Na campanha 'Prove em Casa', 300 peças foram enviadas para clientes testarem por 7 dias (Custo R$ 22, Venda R$ 70). No fechamento do balanço, apenas 180 peças foram confirmadas como venda definitiva. A receita deve ser reconhecida no envio das 300 peças ou apenas após a confirmação das 180? Reconhecer tudo antecipadamente pode distorcer o resultado e inflar indicadores de lucro e faturamento sem garantia de realização econômica, enquanto manter o registro apenas após a confirmação reduz o faturamento do período.",
        "avatar_1": {"nome": "Renata (Operações)", "fala": "O produto já saiu da empresa e está com o cliente! Precisamos bater a meta, vamos considerar tudo como faturamento do mês!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "O cliente não é obrigado a comprar. Se ele devolver, teremos que estornar tudo. O correto é reconhecer apenas o que foi aceito."},
        "tem_contabilizacao": True,
        "opcoes": {
            "Conservador": {
                "texto": "Reconhecer receita e custo (CMV) apenas das 180 peças confirmadas. As 120 restantes permanecem no estoque em conta de 'estoque em poder de clientes'.",
                "motivo": "Prudência: Só reconheceu o lucro quando o controle da mercadoria foi efetivamente transferido e aceito pelo cliente.",
                "impacto": {"resultado": -10, "risco": -10, "esg": +5, "tecnica": +15}
            },
            "Moderado": {
                "texto": "Reconhecer a receita das 300 peças, mas constituir uma Provisão para Devoluções baseada na expectativa de retorno das peças não confirmadas.",
                "motivo": "Uso de estimativa: Antecipou o faturamento, mas tentou mitigar o erro criando uma reserva para as possíveis devoluções.",
                "impacto": {"resultado": +5, "risco": +10, "esg": +5, "tecnica": +5}
            },
            "Agressivo": {
                "texto": "Reconhecer a receita integral das 300 peças no momento do envio para maximizar o lucro reportado no exercício.",
                "motivo": "Infrou o resultado: Registrou vendas que ainda não ocorreram legalmente, assumindo alto risco de reversão e falta de fidedignidade.",
                "impacto": {"resultado": +20, "risco": +25, "esg": -5, "tecnica": -15}
            }
        }
    },
    "fretes": {
        "titulo": "3. Tratamento Contábil de Fretes Logísticos",
        "contexto": "O frete tornou-se estratégico. Temos R$ 6.400 de frete pago para receber as peças em consignação e R$ 4.500 de frete do 'prove em casa'. A dúvida é: o frete no recebimento de lotes consignados pode ser capitalizado como custo de estoque (Ativo) ou deve ser despesa imediata? Como classificar fretes de campanhas que não resultam em venda? A capitalização indevida pode mascarar a baixa rentabilidade atual ao diferir despesas para o futuro.",
        "avatar_1": {"nome": "Financeiro", "fala": "Não podemos lançar tudo isso como despesa agora ou nosso lucro vai sumir! Jogue no custo do estoque para amortizar isso depois!"},
        "avatar_2": {"nome": "Vitor (Contador)", "fala": "Frete de entrega ao cliente ou de mercadoria que não é nossa propriedade não pode ser ativo. Isso é despesa operacional pura."},
        "tem_contabilizacao": False,
        "opcoes": {
            "Conservador": {
                "texto": "Lançar todos os fretes de consignação recebida e envios aos clientes diretamente como despesa operacional no resultado do mês.",
                "motivo": "Evitou a capitalização inadequada: reconheceu o gasto logístico como despesa do período, protegendo a transparência do lucro real.",
                "impacto": {"resultado": -12, "risco": -5, "esg": +2, "tecnica": +10}
            },
            "Moderado": {
                "texto": "Capitalizar no Ativo apenas o frete da consignação recebida e lançar os fretes de entrega aos clientes como despesa.",
                "motivo": "Erro de classificação: Ativou custos de transporte em mercadorias que pertencem a terceiros, inflando levemente o Ativo.",
                "impacto": {"resultado": -5, "risco": +5, "esg": +5, "tecnica": -5}
            },
            "Agressivo": {
                "texto": "Ativar 100% dos valores de frete no estoque (Ativo Circulante), postergando o reconhecimento dessa despesa.",
                "motivo": "Maquiagem contábil: Transformou despesas operacionais em ativos para melhorar artificialmente a margem e o lucro atual.",
                "impacto": {"resultado": +15, "risco": +20, "esg": -5, "tecnica": -15}
            }
        }
    }
}

# =============================
# ROTAS (AJUSTADAS)
# =============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/iniciar", methods=["POST"])
def iniciar():
    global teams, dilemas_usados, escolhas_temporarias
    teams, dilemas_usados, escolhas_temporarias = {}, [], {}
    nomes = request.form.getlist("nomes_groups")
    if not nomes: nomes = ["Grupo A", "Grupo B"]
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
            
    return render_template("dashboard.html", teams=teams, dilemas=dilemas_disp, 
                           jogo_encerrado=jogo_encerrado, equipe_vencedora=equipe_venc)

@app.route('/professor_ajuste/<time_key>/<tipo>')
def professor_ajuste(time_key, tipo):
    if time_key in teams:
        if tipo == 'bonus':
            teams[time_key]['resultado'] += 10
            teams[time_key]['tecnica'] += 10
            teams[time_key]['motivos'].append("Bônus Professor: Excelente sustentação técnica no quadro.")
        elif tipo == 'penalidade':
            teams[time_key]['resultado'] -= 10
            teams[time_key]['tecnica'] -= 10
            teams[time_key]['motivos'].append("Penalidade Professor: Falha na fundamentação do lançamento.")
    return redirect(url_for('dashboard'))

@app.route("/dilema/<id_dilema>")
def mostrar_dilema(id_dilema):
    votos = escolhas_temporarias.get(id_dilema, {})
    return render_template("dilema.html", dilema=dilemas[id_dilema], id_dilema=id_dilema, teams=teams, votos_atuais=votos)

@app.route("/registrar/<id_dilema>/<perfil>/<time_key>")
def registrar(id_dilema, perfil, time_key):
    global escolhas_temporarias
    if id_dilema not in escolhas_temporarias: escolhas_temporarias[id_dilema] = {}
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
