import requests
import time
from datetime import datetime, timedelta, timezone

TOKEN = "8722896865:AAHUxId3mJCCg105VoEVadKr0_Dl36keSIM"
CHAT_ID = "-1003675313042"

URL = "https://jonbet.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1"

STICKER_GREEN = "CAACAgEAAxkBAAEBuhtkFBbPbho5iUL3Cw0Zs2WBNdupaAACQgQAAnQVwEe3Q77HvZ8W3y8E"
STICKER_LOSS = "CAACAgEAAxkBAAEBuh9kFBbVKxciIe1RKvDQBeDu8WfhFAACXwIAAq-xwEfpc4OHHyAliS8E"

COR_BRANCO = 0

NIVEIS = {
    1: 10,
    2: 20,
    3: 45
}

NIVEL_MAXIMO = 3

sinal_ativo = None
processados = set()

nivel_atual = 1
data_stats = None

stats = {
    "GREEN": 0,
    "LOSS": 0
}

maior_seq_nivel = 0
maior_seq_gale = 0
hora_maior_seq = "--:--"
seq_loss_max_texto = "Nenhum ainda"

mensagem_operacao_id = None


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


def verificar_virada_dia():
    global data_stats, stats, nivel_atual, sinal_ativo, mensagem_operacao_id
    global maior_seq_nivel, maior_seq_gale, hora_maior_seq, seq_loss_max_texto

    hoje = agora_br().date()

    if data_stats is None:
        data_stats = hoje
        return

    if hoje != data_stats:
        stats = {"GREEN": 0, "LOSS": 0}
        nivel_atual = 1
        sinal_ativo = None
        mensagem_operacao_id = None

        maior_seq_nivel = 0
        maior_seq_gale = 0
        hora_maior_seq = "--:--"
        seq_loss_max_texto = "Nenhum ainda"

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
        f"SEQ MAX: {maior_seq_nivel:02d}/{NIVEL_MAXIMO:02d} | {hora_maior_seq}\n\n"
        "SEQ LOSS MAX:\n"
        f"{seq_loss_max_texto}\n\n"
        f"🎯 Assertividade: {assertividade():.2f}%"
    )


def atualizar_seq_loss_max(nivel_final, gale_final, resultado_final):
    global maior_seq_nivel, maior_seq_gale, hora_maior_seq, seq_loss_max_texto

    if nivel_final < maior_seq_nivel:
        return

    if nivel_final == maior_seq_nivel and gale_final <= maior_seq_gale:
        return

    maior_seq_nivel = nivel_final
    maior_seq_gale = gale_final
    hora_maior_seq = agora_br().strftime("%H:%M")

    partes = []

    for n in range(1, nivel_final):
        partes.append(f"N{n}/{NIVEIS[n]}G: ⛔ G{NIVEIS[n]}")

    if resultado_final == "GREEN":
        partes.append(f"N{nivel_final}/{NIVEIS[nivel_final]}G: ✅ G{gale_final}")
    else:
        partes.append(f"N{nivel_final}/{NIVEIS[nivel_final]}G: ⛔ G{gale_final}")

    seq_loss_max_texto = " | ".join(partes)


def enviar_operacao():
    global mensagem_operacao_id

    if mensagem_operacao_id is not None:
        apagar_mensagem(mensagem_operacao_id)
        mensagem_operacao_id = None

    max_gale = NIVEIS[nivel_atual]
    gale_atual = sinal_ativo["etapa"]

    msg = (
        "💎 *JONBET DOUBLE VIP*\n\n"
        "📊 *Estratégia:* BRANCO\n\n"
        "🎯 *⚪ BRANCO*\n\n"
        f"📌 *NÍVEL:* {nivel_atual:02d}/{NIVEL_MAXIMO:02d}\n"
        f"📌 *GALE:* {gale_atual:02d}/{max_gale:02d}"
    )

    mensagem_operacao_id = enviar_com_retorno(msg)


def iniciar_sinal_branco():
    global sinal_ativo

    max_gale = NIVEIS[nivel_atual]

    sinal_ativo = {
        "cor": COR_BRANCO,
        "etapa": 0,
        "max_gale": max_gale
    }

    enviar_operacao()


def enviar_apuracao_green(gale):
    enviar_sticker(STICKER_GREEN)

    texto_green = "✅ *GREEN SG*" if gale == 0 else f"✅ *GREEN G{gale}*"

    msg = (
        f"{texto_green}\n\n"
        "📊 *APURAÇÃO*\n\n"
        f"{texto_stats()}"
    )

    enviar(msg)


def enviar_apuracao_loss_nivel():
    enviar_sticker(STICKER_LOSS)

    max_gale = NIVEIS[nivel_atual]

    msg = (
        f"⛔ *LOSS NÍVEL {nivel_atual:02d}/{NIVEL_MAXIMO:02d}*\n\n"
        "📊 *APURAÇÃO*\n\n"
        f"{texto_stats()}\n\n"
        f"📌 Perdeu no último gale: G{max_gale}"
    )

    enviar(msg)


def finalizar_green():
    global sinal_ativo, nivel_atual, mensagem_operacao_id

    gale = sinal_ativo["etapa"]

    stats["GREEN"] += 1

    atualizar_seq_loss_max(nivel_atual, gale, "GREEN")

    enviar_apuracao_green(gale)

    sinal_ativo = None

    # Mantém a última mensagem de operação como histórico do GREEN.
    mensagem_operacao_id = None

    nivel_atual = 1

    print("✅ GREEN no branco. Reiniciando no nível 01 e entrando novamente.")
    iniciar_sinal_branco()


def finalizar_loss_nivel():
    global sinal_ativo, nivel_atual, mensagem_operacao_id

    max_gale = NIVEIS[nivel_atual]

    stats["LOSS"] += 1

    atualizar_seq_loss_max(nivel_atual, max_gale, "LOSS")

    enviar_apuracao_loss_nivel()

    sinal_ativo = None

    # Mantém a última mensagem do último gale como histórico do LOSS.
    mensagem_operacao_id = None

    if nivel_atual >= NIVEL_MAXIMO:
        nivel_atual = 1
        print("⛔ LOSS no nível 03. Voltando para nível 01 e aguardando novo branco.")
    else:
        nivel_atual += 1
        print(f"⛔ LOSS. Aguardando novo branco para iniciar nível {nivel_atual:02d}.")


def verificar_resultado_sinal(resultado):
    global sinal_ativo

    if sinal_ativo is None:
        return

    cor = resultado["color"]

    if cor == COR_BRANCO:
        finalizar_green()
        return

    sinal_ativo["etapa"] += 1

    if sinal_ativo["etapa"] > sinal_ativo["max_gale"]:
        finalizar_loss_nivel()
        return

    enviar_operacao()


def processar_resultado(resultado, iniciar=False):
    if resultado["id"] in processados:
        return

    processados.add(resultado["id"])

    if iniciar:
        return

    verificar_resultado_sinal(resultado)

    cor = resultado["color"]

    if sinal_ativo is None and cor == COR_BRANCO:
        print(f"⚪ Branco detectado. Iniciando nível {nivel_atual:02d}.")
        iniciar_sinal_branco()


enviar("✅ *Bot BRANCO iniciado com sucesso!*")

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
        print("✅ Histórico inicial carregado. Aguardando sair BRANCO para iniciar...")

    else:
        for resultado in reversed(dados):
            processar_resultado(resultado)

    time.sleep(1)
