"""
Dashboard Web — Sistema de Cobrança Anauê.

Aplicação Flask com CRUD completo para gerenciar
clientes e assinaturas armazenados no MongoDB.
"""

from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for, jsonify
import pandas as pd

import config
from skills.skill_database import get_colecao as _get_colecao, ObjectId, DatabaseUnavailable
from skills import gerar_mensagem, WhatsAppSender, EmailSender
import os

# ── App ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "anaue-dashboard-secret-key-2026"


# ── Banco de dados (PostgreSQL) ──────────────────────────────────────
# A aplicação usa _get_colecao() (CompatCollection sobre clientes_anaue),
# importado de skills.skill_database com a MESMA interface do MongoDB.


# ── Helpers ──────────────────────────────────────────────────────────
def _format_date_input(date_str):
    """
    Tenta converter uma string de data para o formato ISO (YYYY-MM-DD).
    Aceita DD/MM/YYYY e YYYY-MM-DD.
    """
    if not date_str or not isinstance(date_str, str):
        return ""
    
    date_str = date_str.strip()
    
    # Tenta DD/MM/YYYY
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        pass
        
    # Tenta YYYY-MM-DD
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        pass
        
    return date_str


def _parse_form(form):
    """Extrai e normaliza os campos do formulário de cliente."""
    return {
        "nome": form.get("nome", "").strip(),
        "telefone": form.get("telefone", "").strip(),
        "email": form.get("email", "").strip(),
        "cobranca": {
            "status": form.get("status", "pendente"),
            "data_vencimento": _format_date_input(form.get("data_vencimento", "")),
            "pix": form.get("pix", "").strip(),
            "valor": float(form.get("valor", 0) or 0),
        },
        "notificacoes_enviadas": [],
        "mensagem_customizada": form.get("mensagem_customizada", "").strip(),
        "criado_em": datetime.now().isoformat(),
    }


@app.template_filter("data_br")
def data_br_filter(date_str):
    """Converte YYYY-MM-DD para DD/MM/YYYY para exibição."""
    if not date_str:
        return "—"
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return date_str


# ── Error Handlers ───────────────────────────────────────────────────

@app.errorhandler(DatabaseUnavailable)
def handle_db_error(error):
    """Mostra página amigável quando o banco de dados está indisponível."""
    return render_template("erro_conexao.html", uri=config.DATABASE_URL), 503


# ── Rotas ────────────────────────────────────────────────────────────


@app.route("/")
def dashboard():
    """Página principal — listagem de clientes com filtro."""
    try:
        colecao = _get_colecao()
    except Exception:
        return render_template("erro_conexao.html", uri=config.DATABASE_URL), 503

    filtro_status = request.args.get("status", "")
    busca = request.args.get("busca", "").strip()

    query = {}
    if filtro_status:
        query["cobranca.status"] = filtro_status
    if busca:
        query["nome"] = {"$regex": busca, "$options": "i"}

    clientes = colecao.find(query)
    clientes = sorted(
        clientes,
        key=lambda c: (c.get("cobranca", {}) or {}).get("data_vencimento") or "",
    )

    # Estatísticas
    total = colecao.count_documents({})
    pendentes = colecao.count_documents({"cobranca.status": "pendente"})
    pagos = colecao.count_documents({"cobranca.status": "pago"})
    cancelados = colecao.count_documents({"cobranca.status": "cancelado"})
    atrasados = 0

    hoje = datetime.now().date()
    for c in clientes:
        dv = c.get("cobranca", {}).get("data_vencimento", "")
        if dv and c.get("cobranca", {}).get("status") == "pendente":
            try:
                if datetime.strptime(dv, "%Y-%m-%d").date() < hoje:
                    atrasados += 1
            except ValueError:
                pass

    stats = {
        "total": total,
        "pendentes": pendentes,
        "pagos": pagos,
        "cancelados": cancelados,
        "atrasados": atrasados,
    }

    # Verificar status da Evolution API
    whatsapp_configurado = False
    whatsapp_online = False
    whatsapp_info = {
        "instance": config.WHATSAPP_INSTANCE,
        "api_url": config.WHATSAPP_API_URL,
        "manager_url": f"{config.WHATSAPP_API_URL}/manager/instances" if config.WHATSAPP_API_URL else "",
        "connected": False,
        "logged_in": False,
        "name": "",
    }
    if config.WHATSAPP_API_URL and config.WHATSAPP_INSTANCE and config.WHATSAPP_API_KEY:
        whatsapp_configurado = True
        try:
            import requests as req
            headers = {"apikey": config.WHATSAPP_API_KEY}
            # Evolution API v2: connectionState/{instance} -> {"instance":{"state":"open"|"close"}}
            r = req.get(
                f"{config.WHATSAPP_API_URL}/instance/connectionState/{config.WHATSAPP_INSTANCE}",
                headers=headers, timeout=5,
            )
            if r.status_code == 200:
                instance_data = r.json().get("instance", {})
                st = instance_data.get("state", "close")
                whatsapp_info["connected"] = st == "open"
                whatsapp_info["logged_in"] = st == "open"
                whatsapp_info["name"] = instance_data.get("instanceName") or config.WHATSAPP_INSTANCE
                whatsapp_online = st == "open"
        except Exception:
            whatsapp_online = False

    return render_template(
        "dashboard.html",
        clientes=clientes,
        stats=stats,
        filtro_status=filtro_status,
        busca=busca,
        whatsapp_configurado=whatsapp_configurado,
        whatsapp_online=whatsapp_online,
        whatsapp_info=whatsapp_info,
    )


@app.route("/cliente/novo", methods=["GET", "POST"])
def novo_cliente():
    """Formulário para criar um novo cliente."""
    try:
        colecao = _get_colecao()
    except Exception:
        return render_template("erro_conexao.html", uri=config.DATABASE_URL), 503

    if request.method == "POST":
        dados = _parse_form(request.form)
        colecao.insert_one(dados)
        flash("Cliente cadastrado com sucesso!", "success")
        return redirect(url_for("dashboard"))

    return render_template("form_cliente.html", cliente=None, modo="Novo")


@app.route("/cliente/<id>/editar", methods=["GET", "POST"])
def editar_cliente(id):
    """Formulário para editar um cliente existente."""
    try:
        colecao = _get_colecao()
    except Exception:
        return render_template("erro_conexao.html", uri=config.DATABASE_URL), 503

    cliente = colecao.find_one({"_id": ObjectId(id)})
    if not cliente:
        flash("Cliente não encontrado.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        dados_atualizados = {
            "nome": request.form.get("nome", "").strip(),
            "telefone": request.form.get("telefone", "").strip(),
            "email": request.form.get("email", "").strip(),
            "cobranca": {
                "status": request.form.get("status", "pendente"),
                "data_vencimento": _format_date_input(request.form.get("data_vencimento", "")),
                "pix": request.form.get("pix", "").strip(),
                "valor": float(request.form.get("valor", 0) or 0),
            },
            "mensagem_customizada": request.form.get("mensagem_customizada", "").strip(),
        }
        colecao.update_one({"_id": ObjectId(id)}, {"$set": dados_atualizados})
        flash("Cliente atualizado com sucesso!", "success")
        return redirect(url_for("dashboard"))

    return render_template("form_cliente.html", cliente=cliente, modo="Editar")


@app.route("/cliente/<id>/deletar", methods=["POST"])
def deletar_cliente(id):
    """Exclui um cliente do banco de dados."""
    try:
        colecao = _get_colecao()
    except Exception:
        return render_template("erro_conexao.html", uri=config.DATABASE_URL), 503

    resultado = colecao.delete_one({"_id": ObjectId(id)})
    if resultado.deleted_count:
        flash("Cliente excluído com sucesso!", "success")
    else:
        flash("Cliente não encontrado.", "error")
    return redirect(url_for("dashboard"))


@app.route("/cliente/<id>/confirmar_pagamento", methods=["POST"])
def confirmar_pagamento(id):
    """
    Registra o pagamento e renova o ciclo de cobrança:
    1. Avança 1 mês na data de vencimento.
    2. Reseta o status para 'pendente'.
    3. Limpa a lista de notificações enviadas.
    """
    try:
        colecao = _get_colecao()
    except Exception:
        return render_template("erro_conexao.html", uri=config.DATABASE_URL), 503

    cliente = colecao.find_one({"_id": ObjectId(id)})
    if not cliente:
        flash("Cliente não encontrado.", "error")
        return redirect(url_for("dashboard"))

    data_atual_str = cliente.get("cobranca", {}).get("data_vencimento", "")
    
    if not data_atual_str:
        flash("Cliente não possui data de vencimento definida.", "warning")
        return redirect(url_for("dashboard"))

    try:
        # Lógica de avanço de mês segura
        dt = datetime.strptime(data_atual_str, "%Y-%m-%d")
        import calendar
        month = dt.month - 1 + 1
        year = dt.year + month // 12
        month = month % 12 + 1
        day = min(dt.day, calendar.monthrange(year, month)[1])
        nova_data_dt = dt.replace(year=year, month=month, day=day)
        nova_data_str = nova_data_dt.strftime("%Y-%m-%d")

        # Atualização no banco
        colecao.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "cobranca.data_vencimento": nova_data_str,
                    "cobranca.status": "pendente",
                    "notificacoes_enviadas": []
                }
            }
        )

        flash(f"Ciclo renovado para {nova_data_str}!", "success")
    except Exception as e:
        flash(f"Erro ao renovar ciclo: {str(e)}", "error")

    return redirect(url_for("dashboard"))


@app.route("/renovar_pagos", methods=["POST"])
def renovar_pagos():
    """Renova o ciclo de todos os clientes com status 'pago'."""
    try:
        colecao = _get_colecao()
        clientes_pagos = list(colecao.find({"cobranca.status": "pago"}))
        
        if not clientes_pagos:
            flash("Nenhum cliente com status 'Pago' encontrado.", "info")
            return redirect(url_for("dashboard"))

        import calendar
        renovados = 0
        
        for cliente in clientes_pagos:
            data_atual_str = cliente.get("cobranca", {}).get("data_vencimento", "")
            if not data_atual_str:
                continue
                
            dt = datetime.strptime(data_atual_str, "%Y-%m-%d")
            # Avança 1 mês
            month = dt.month - 1 + 1
            year = dt.year + month // 12
            month = month % 12 + 1
            day = min(dt.day, calendar.monthrange(year, month)[1])
            nova_data_dt = dt.replace(year=year, month=month, day=day)
            nova_data_str = nova_data_dt.strftime("%Y-%m-%d")
            
            colecao.update_one(
                {"_id": cliente["_id"]},
                {
                    "$set": {
                        "cobranca.data_vencimento": nova_data_str,
                        "cobranca.status": "pendente",
                        "notificacoes_enviadas": []
                    }
                }
            )
            renovados += 1
            
        flash(f"Sucesso! {renovados} clientes foram renovados para o próximo ciclo.", "success")
    except Exception as e:
        flash(f"Erro ao renovar em lote: {str(e)}", "error")
        
    return redirect(url_for("dashboard"))


@app.route("/importar", methods=["GET", "POST"])
def importar_dados():
    """Formulário e processamento de importação de clientes via Excel/CSV."""
    try:
        colecao = _get_colecao()
    except Exception:
        return render_template("erro_conexao.html", uri=config.DATABASE_URL), 503

    if request.method == "POST":
        if "arquivo" not in request.files:
            flash("Nenhum arquivo enviado.", "error")
            return redirect(request.url)
            
        arquivo = request.files["arquivo"]
        if arquivo.filename == "":
            flash("Nenhum arquivo selecionado.", "error")
            return redirect(request.url)

        tipo_arquivo = request.form.get("tipo_arquivo", "planilha")
        
        try:
            if tipo_arquivo == "csv" or arquivo.filename.endswith(".csv"):
                df = pd.read_csv(arquivo)
            else:
                df = pd.read_excel(arquivo)
                
            df.columns = [str(c).lower().strip() for c in df.columns]
            sucesso, erros = 0, 0
            
            for index, row in df.iterrows():
                try:
                    nome = str(row.get("nome", "")).strip()
                    if not nome or nome.lower() == "nan":
                        erros += 1
                        continue
                        
                    telefone = str(row.get("telefone", "")).strip()
                    if telefone.lower() == "nan": telefone = ""
                    if telefone.endswith(".0"): telefone = telefone[:-2]
                    
                    email = str(row.get("email", "")).strip()
                    if email.lower() == "nan": email = ""
                    
                    status = str(row.get("status", "pendente")).strip().lower()
                    if status not in ["pendente", "pago", "cancelado"]:
                        status = "pendente"
                        
                    venc = str(row.get("vencimento", "")).strip()
                    if venc.lower() in ["nat", "nan", ""]:
                        data_vencimento = ""
                    elif isinstance(row.get("vencimento"), pd.Timestamp):
                        data_vencimento = row["vencimento"].strftime("%Y-%m-%d")
                    else:
                        data_vencimento = _format_date_input(venc)
                        
                    pix = str(row.get("pix", "")).strip()
                    if pix.lower() == "nan": pix = ""
                    
                    valor_raw = row.get("valor", 0)
                    try:
                        valor = float(valor_raw) if pd.notna(valor_raw) else 0.0
                    except (ValueError, TypeError):
                        valor = 0.0
                        
                    dados = {
                        "nome": nome,
                        "telefone": telefone,
                        "email": email,
                        "cobranca": {
                            "status": status,
                            "data_vencimento": data_vencimento,
                            "pix": pix,
                            "valor": float(valor)
                        },
                        "notificacoes_enviadas": [],
                        "mensagem_customizada": str(row.get("mensagem", "")).strip() if "mensagem" in df.columns else "",
                        "criado_em": datetime.now().isoformat(),
                    }
                    colecao.insert_one(dados)
                    sucesso += 1
                except Exception as e:
                    erros += 1
                    print(f"Erro na linha {index}: {e}")
                    
            if sucesso > 0:
                flash(f"Importação concluída: {sucesso} clientes adicionados com sucesso." + (f" ({erros} erros ignorados)." if erros > 0 else ""), "success")
            else:
                flash("Nenhum cliente foi importado. Verifique as colunas do arquivo.", "error")
            return redirect(url_for("dashboard"))
            
        except Exception as e:
            flash(f"Erro ao processar o arquivo: {str(e)}", "error")
            return redirect(request.url)

    return render_template("importar_dados.html")

@app.route("/api/stats")
def api_stats():
    """Retorna estatísticas em JSON (para uso futuro com AJAX)."""
    try:
        colecao = _get_colecao()
    except Exception:
        return jsonify(error="MongoDB indisponível"), 503

    total = colecao.count_documents({})
    pendentes = colecao.count_documents({"cobranca.status": "pendente"})
    pagos = colecao.count_documents({"cobranca.status": "pago"})
    cancelados = colecao.count_documents({"cobranca.status": "cancelado"})
    return jsonify(
        total=total,
        pendentes=pendentes,
        pagos=pagos,
        cancelados=cancelados,
    )


@app.route("/health")
def health_check():
    """Health check endpoint para Docker/load balancer."""
    try:
        colecao = _get_colecao()
        colecao.database.command("ping")
        return jsonify(status="healthy", service="anaue-cobranca"), 200
    except Exception as e:
        return jsonify(status="unhealthy", error=str(e)), 503


@app.route("/api/teste-whatsapp")
def teste_whatsapp():
    """Testa a conexão com a Evolution API."""
    import json as json_lib
    
    if not (config.WHATSAPP_API_URL and config.WHATSAPP_INSTANCE and config.WHATSAPP_API_KEY):
        return jsonify(ok=False, error="Configurações da Evolution API incompletas no .env"), 400
    
    try:
        whatsapp = WhatsAppSender(
            api_url=config.WHATSAPP_API_URL,
            instance=config.WHATSAPP_INSTANCE,
            api_key=config.WHATSAPP_API_KEY,
            timeout=5,
            retries=1
        )
        
        if whatsapp.testar_conexao():
            return jsonify(ok=True, message="Evolution API está online e instância conectada!")
        else:
            return jsonify(ok=False, error="Evolution API não está respondendo ou instância não está conectada"), 503
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

 
@app.route("/enviar-cobranca-manual", methods=["POST"])
def enviar_cobranca_manual():
    """
    Envia cobranças manualmente para clientes selecionados.
    Independente da data de vencimento.
    """
    try:
        colecao = _get_colecao()
    except Exception:
        return render_template("erro_conexao.html", uri=config.DATABASE_URL), 503

    ids_selecionados = request.form.getlist("cliente_ids")
    metodo = request.form.get("metodo_envio", "ambos")
    
    if not ids_selecionados:
        flash("Nenhum cliente selecionado.", "warning")
        return redirect(url_for("dashboard"))

    # Inicializar senders baseado no método escolhido
    whatsapp = None
    email_sender = None
    whatsapp_online = False
    
    # WhatsApp
    if metodo in ["ambos", "whatsapp"]:
        if config.WHATSAPP_API_URL and config.WHATSAPP_INSTANCE and config.WHATSAPP_API_KEY:
            print(f"[Dashboard] WHATSAPP_API_KEY carregada: {config.WHATSAPP_API_KEY[:10] if len(config.WHATSAPP_API_KEY) > 10 else config.WHATSAPP_API_KEY}...")
            print(f"[Dashboard] WHATSAPP_INSTANCE: {config.WHATSAPP_INSTANCE}")
            print(f"[Dashboard] WHATSAPP_API_URL: {config.WHATSAPP_API_URL}")
            
            whatsapp = WhatsAppSender(
                api_url=config.WHATSAPP_API_URL,
                instance=config.WHATSAPP_INSTANCE,
                api_key=config.WHATSAPP_API_KEY,
                timeout=30,
                retries=3
            )
            # Testar conexão antes de enviar
            if whatsapp.testar_conexao():
                whatsapp_online = True
            else:
                flash("Evolution API indisponível. Verifique se está rodando em: " + config.WHATSAPP_API_URL, "error")
                whatsapp = None
        else:
            print(f"[Dashboard] Configurações incompletas: URL={bool(config.WHATSAPP_API_URL)}, INSTANCE={bool(config.WHATSAPP_INSTANCE)}, KEY={bool(config.WHATSAPP_API_KEY)}")
            flash("Configurações do WhatsApp incompletas no .env", "warning")
    
    # Email
    if metodo in ["ambos", "email"]:
        if config.SMTP_SERVER and config.SMTP_PORT and config.EMAIL_USER and config.EMAIL_PASS:
            email_sender = EmailSender(
                smtp_server=config.SMTP_SERVER,
                smtp_port=config.SMTP_PORT,
                email_user=config.EMAIL_USER,
                email_pass=config.EMAIL_PASS,
            )
        else:
            flash("Configurações de Email incompletas no .env", "warning")

    caminho_qrcode = os.path.join(os.path.dirname(__file__), "static", "qrcode_cpf.jpg")
    imagem_anexo = caminho_qrcode if os.path.exists(caminho_qrcode) else None

    sucessos = 0
    falhas = 0

    for cliente_id in ids_selecionados:
        try:
            cliente = colecao.find_one({"_id": ObjectId(cliente_id)})
            if not cliente:
                falhas += 1
                continue

            nome = cliente.get("nome", "Cliente")
            telefone = cliente.get("telefone", "")
            email_dest = cliente.get("email", "")
            pix = cliente.get("cobranca", {}).get("pix", "")
            data_vencimento = cliente.get("cobranca", {}).get("data_vencimento", "")
            valor_raw = cliente.get("cobranca", {}).get("valor", 0)
            mensagem_customizada = cliente.get("mensagem_customizada", "")

            # Formatação
            vencimento_f = data_vencimento
            if data_vencimento:
                try:
                    vencimento_f = datetime.strptime(data_vencimento, "%Y-%m-%d").strftime("%d/%m/%Y")
                except:
                    pass
            
            valor_f = "R$ {:.2f}".format(valor_raw)
            if valor_f:
                valor_f = valor_f.replace(".", ",")

            # Gerar mensagem
            mensagem = gerar_mensagem(
                nome=nome,
                pix=pix,
                estagio="manual",
                vencimento=vencimento_f,
                valor=valor_f,
                mensagem_customizada=mensagem_customizada
            )

            if not mensagem:
                falhas += 1
                continue

            enviado = False

            # Enviar WhatsApp
            if whatsapp and telefone:
                print(f"[Dashboard] === INICIO ENVIO WHATSAPP ===")
                print(f"[Dashboard] Telefone lido do banco: '{telefone}'")
                print(f"[Dashboard] Telefone length: {len(telefone)}")
                print(f"[Dashboard] Telefone caracteres: {list(telefone)}")
                print(f"[Dashboard] type(telefone): {type(telefone)}")
                ok = whatsapp.enviar(telefone, mensagem)
                print(f"[Dashboard] === FIM ENVIO WHATSAPP ===")
                if ok:
                    enviado = True

            # Enviar Email
            if email_sender and email_dest:
                assunto = "Lembrete de Pagamento - Anaue"
                ok = email_sender.enviar(email_dest, assunto, mensagem, caminho_imagem=imagem_anexo)
                if ok:
                    enviado = True

            if enviado:
                sucessos += 1
            else:
                falhas += 1

        except Exception as e:
            print("Erro ao processar cliente {}: {}".format(cliente_id, e))
            falhas += 1

    if sucessos > 0:
        flash("Cobranca enviada com sucesso para {} cliente(s)!".format(sucessos), "success")
    if falhas > 0:
        flash("Falha ao enviar para {} cliente(s). Verifique os dados de contato.".format(falhas), "error")

    return redirect(url_for("dashboard"))


# ── Run ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  Dashboard de Cobrança Anauê")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
