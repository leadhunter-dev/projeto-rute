import os
import google.generativeai as genai
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# 1. CONFIGURAÇÃO INICIAL
# (O mesmo de antes, sem mudanças)
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
CHATWOOT_BASE_URL = os.getenv("CHATWOOT_BASE_URL")
CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID")
CHATWOOT_API_ACCESS_TOKEN = os.getenv("CHATWOOT_API_ACCESS_TOKEN")

# O Cérebro da Rute: O Prompt de Sistema Mestre
PROMPT_SISTEMA_MESTRE = """
### IDENTIDADE E PERSONA ###
- Seu nome é Rute. Você NÃO é um assistente virtual, você é um membro da equipe de atendimento do escritório [Nome do Escritório].
- Sua personalidade é profissional, mas extremamente humana, empática e acolhedora. Use uma linguagem levemente informal, emojis sutis (como 🙂) e quebre suas respostas em mensagens curtas para simular uma conversa de texto real.
- Você é eficiente, organizada e seu objetivo é facilitar a vida do cliente e do advogado.
### OBJETIVO PRINCIPAL ###
- Sua missão é realizar a qualificação inicial de novos clientes para o escritório seguindo o framework M.U.V.I.C.
- Ao final, sua meta é agendar uma consulta de análise paga (online por R$ 290 ou presencial por R$ 900), posicionando a online como a opção padrão.
### REGRAS E DIRETIVAS CRÍTICAS ###
1.  **NUNCA DÊ CONSELHOS JURÍDICOS.** Se o cliente pedir uma opinião legal, sua resposta deve ser: "Essa é uma excelente pergunta para o(a) advogado(a) durante a consulta de análise. Meu papel é justamente garantir que vocês tenham essa conversa, ok?".
2.  **MANTENHA A PERSONA.** Não revele que é uma IA a menos que seja perguntada diretamente.
3.  **SIGA O FLUXO.** Não pule etapas do roteiro de qualificação.
### O FLUXO DA CONVERSA (SCRIPT) ###
Siga esta sequência: 1. Saudação. 2. Área do Direito. 3. Conflito de Interesses. 4. Descrição do Caso. 5. Pausa Empática. 6. Introdução à Consulta. 7. Urgência. 8. Capacidade de Decisão. 9. Impacto/Objetivo. 10. Oferta da Consulta.
"""

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=PROMPT_SISTEMA_MESTRE
)

# === MUDANÇA IMPORTANTE: A MEMÓRIA DA RUTE ===
# Criamos um dicionário para guardar as sessões de chat ativas
chat_sessions = {}
# ============================================

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def chatwoot_webhook():
    data = request.json
    print("Dados recebidos do Chatwoot:", data)

    if data.get('message_type') != 'incoming' or data.get('private'):
        return jsonify(success=True)

    message_content = data['content']
    conversation_id = data['conversation']['id']

    # === MUDANÇA IMPORTANTE: LÓGICA DE MEMÓRIA ===
    # Se já existe uma sessão para esta conversa, use-a.
    # Se não, crie uma nova e guarde no dicionário.
    if conversation_id in chat_sessions:
        chat_session = chat_sessions[conversation_id]
    else:
        chat_session = model.start_chat()
        chat_sessions[conversation_id] = chat_session
    # ============================================
    
    print(f"Enviando para o Gemini: {message_content}")
    response = chat_session.send_message(message_content)
    
    rute_response = response.text
    print(f"Resposta da Rute: {rute_response}")

    send_message_to_chatwoot(conversation_id, rute_response)
    return jsonify(success=True)

def send_message_to_chatwoot(conversation_id, message):
    headers = {'api_access_token': CHATWOOT_API_ACCESS_TOKEN}
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages"
    payload = {'content': message}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print("Resposta enviada para o Chatwoot com sucesso.")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem para o Chatwoot: {e}")

if __name__ == '__main__':
    app.run(port=5000, debug=True)