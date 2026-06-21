import requests
import time
from datetime import datetime, timedelta, timezone

TOKEN = "5483533126:AAGIfCbKAXj1dzJa7kgtZKcI83a2dVBdiJA"
CHAT_ID = "-1003961010489"

URL = "https://jonbet.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1"

STICKER_GREEN = "CAACAgEAAxkBAAEBuhtkFBbPbho5iUL3Cw0Zs2WBNdupaAACQgQAAnQVwEe3Q77HvZ8W3y8E"
STICKER_LOSS = "CAACAgEAAxkBAAEBuh9kFBbVKxciIe1RKvDQBeDu8WfhFAACXwIAAq-xwEfpc4OHHyAliS8E"

COR_PRETO = 2
COR_VERDE = 1
NIVEL_MAXIMO = 12

sinal_ativo = None
cor_atual = None
processados = set()

stats = {"GREEN": 0, "LOSS": 0}

nivel_atual = 1
maior_seq = 0
hora_maior_seq = "--:--"
data_stats = None

mensagem_nivel_id = None
mensagem_entrada_id = None


def enviar(msg):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
        print("Telegram:", r.status_code, r.text)
    except Exception as e:
        print("Erro Telegram:", e)


def enviar_com_retorno(msg):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
        print("Telegram:", r.status_code, r.text)

        if r.status_code == 200:
            return r.json()["result"]["message_id"]

    except Exception as e:
        print("Erro Telegram:", e)

    return None


def apagar_mensagem(message_id):
    if message_id is None:
        return

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/deleteMessage",
            data={"chat_id": CHAT_ID, "message_id": message_id},
            timeout=10
        )
        print("Delete:", r.status_code, r.text)
    except Exception as e:
        print("Erro ao apagar mensagem:", e)


def enviar_sticker(sticker_id):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendSticker",
            data={"chat_id": CHAT_ID, "sticker": sticker_id},
            timeout=10
        )
        print("Sticker:", r.status_code, r.text)
    except Exception as e:
        print("Erro Sticker:", e)


def agora_br():
    return datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=-3))
    ).replace(tzinfo=None)


def hora_br(data_api):
    return datetime.fromisoformat(
        data_api.replace("Z", "+00:00")
    ).astimezone(
        timezone(timedelta(hours=-3))
    ).replace(tzinfo=None)


def buscar_resultados():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://jonbet.bet.br/pt/games/double",
            "Origin": "https://jonbet.bet.br"
        }

        r = requests.get(URL, headers=headers, timeout=15)

        if r.status_code != 200:
            print("Erro HTTP:", r.status_code)
            return None

        return r.json()

    except Exception as e:
        print("⚠️ API falhou. Reconectando...", e)
        return None


def texto_cor(cor):
    if cor == COR_PRETO:
        return "⚫ PRETO"
    if cor == COR_VERDE:
        return "🟢 VERDE"
    return str(cor)


def verificar_virada_dia():
    global data_stats, stats, nivel_atual, maior_seq, hora_maior_seq
    global sinal_ativo, cor_atual, mensagem_nivel_id, mensagem_entrada_id

    hoje = agora_br().date()

    if data_stats is None:
        data_stats = hoje
        return

    if hoje != data_stats:
        stats = {"GREEN": 0, "LOSS": 0}

        nivel_atual = 1
        maior_seq = 0
        hora_maior_seq = "--:--"

        sinal_ativo = None
        cor_atual = None

        mensagem_nivel_id = None
        mensagem_entrada_id = None

        data_stats = hoje

        enviar("🔄 *Novo dia iniciado! Estatísticas zeradas.*")


def assertividade():
    total = stats["GREEN"] + stats["LOSS"]

    if total == 0:
        return 0

    return (stats["GREEN"] / total) * 100


def texto_stats():
    return (
        "📈 *GERAL*\n\n"
        f"GREEN: {stats['GREEN']:02d} | LOSS: {stats['LOSS']:02d}\n\n"
        f"SEQ: {nivel_atual:02d}/{NIVEL_MAXIMO:02d}\n"
        f"SEQ MAX: {maior_seq:02d}/{NIVEL_MAXIMO:02d} | {hora_maior_seq}\n\n"
        f"🎯 Assertividade: {assertividade():.2f}%"
    )


def atualizar_seq_max(nivel):
    global maior_seq, hora_maior_seq

    if nivel > maior_seq:
        maior_seq = nivel
        hora_maior_seq = agora_br().strftime("%H:%M")


def enviar_apuracao_green(nivel_green):
    enviar_sticker(STICKER_GREEN)

    msg = (
        "✅ *GREEN SG*\n\n"
        "📊 *APURAÇÃO*\n\n"
        f"{texto_stats()}\n\n"
        f"📌 Recuperou no nível: {nivel_green:02d}/{NIVEL_MAXIMO:02d}"
    )

    print(msg)
    enviar(msg)


def enviar_apuracao_loss_geral():
    enviar_sticker(STICKER_LOSS)

    msg = (
        "⛔ *LOSS GERAL*\n\n"
        "📊 *APURAÇÃO*\n\n"
        f"{texto_stats()}"
    )

    print(msg)
    enviar(msg)


def enviar_mensagem_nivel():
    global mensagem_nivel_id

    msg = (
        "📌 *OPERANDO NÍVEL*\n\n"
        f"SEQ: {nivel_atual:02d}/{NIVEL_MAXIMO:02d}"
    )

    mensagem_nivel_id = enviar_com_retorno(msg)


def enviar_sinal():
    global sinal_ativo, mensagem_entrada_id

    msg = (
        "💎 *JONBET DOUBLE VIP*\n\n"
        "📊 *Estratégia:* COR FIXA SG\n\n"
        "⏰ *ENTRADA:*\n"
        f"🎯 *{texto_cor(cor_atual)}*\n"
        "♻️ *SEM GALE*"
    )

    sinal_ativo = {
        "cor": cor_atual
    }

    print(msg)
    mensagem_entrada_id = enviar_com_retorno(msg)


def apagar_mensagens_pos_apuracao():
    global mensagem_nivel_id, mensagem_entrada_id

    if mensagem_nivel_id is not None:
        apagar_mensagem(mensagem_nivel_id)
        mensagem_nivel_id = None

    if mensagem_entrada_id is not None:
        apagar_mensagem(mensagem_entrada_id)
        mensagem_entrada_id = None


def trocar_cor():
    global cor_atual

    if cor_atual == COR_PRETO:
        cor_atual = COR_VERDE
    else:
        cor_atual = COR_PRETO


def finalizar_green():
    global sinal_ativo, nivel_atual, mensagem_nivel_id, mensagem_entrada_id

    nivel_green = nivel_atual

    stats["GREEN"] += nivel_green
    stats["LOSS"] += nivel_green - 1

    atualizar_seq_max(nivel_green)

    nivel_atual = 1

    enviar_apuracao_green(nivel_green)

    sinal_ativo = None

    # Mantém a última mensagem de nível e entrada como histórico do GREEN.
    mensagem_nivel_id = None
    mensagem_entrada_id = None

    print("✅ GREEN. Mantendo a mesma cor.")
    enviar_sinal()


def finalizar_loss():
    global sinal_ativo, nivel_atual

    nivel_atual += 1

    if nivel_atual > NIVEL_MAXIMO:
        stats["LOSS"] += NIVEL_MAXIMO
        atualizar_seq_max(NIVEL_MAXIMO)

        enviar_apuracao_loss_geral()

        nivel_atual = 1
        print("🔄 LOSS GERAL. Níveis reiniciados.")

    sinal_ativo = None

    trocar_cor()

    print(f"⛔ LOSS. Alternando para {texto_cor(cor_atual)}.")

    apagar_mensagens_pos_apuracao()
    enviar_mensagem_nivel()
    enviar_sinal()


def verificar_resultado_sinal(resultado):
    global sinal_ativo

    if sinal_ativo is None:
        return

    cor_resultado = resultado["color"]

    if cor_resultado == sinal_ativo["cor"]:
        finalizar_green()
    else:
        finalizar_loss()


def processar_resultado(resultado, iniciar=False):
    global cor_atual

    if resultado["id"] in processados:
        return

    processados.add(resultado["id"])

    if iniciar:
        return

    verificar_resultado_sinal(resultado)

    if sinal_ativo is None and cor_atual is None:
        cor = resultado["color"]

        if cor == COR_PRETO:
            cor_atual = COR_PRETO
            print("⚫ Preto detectado. Iniciando estratégia no PRETO.")
            enviar_sinal()


enviar("✅ *Bot COR FIXA SG iniciado com sucesso!*")

primeira_leitura = True

while True:
    verificar_virada_dia()

    dados = buscar_resultados()

    if not dados:
        time.sleep(10)
        continue

    if primeira_leitura:
        for resultado in reversed(dados):
            processar_resultado(resultado, iniciar=True)

        primeira_leitura = False
        print("✅ Histórico inicial carregado. Aguardando sair PRETO para iniciar...")

    else:
        for resultado in reversed(dados):
            processar_resultado(resultado)

    time.sleep(1)
