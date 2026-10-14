"""OpenAI de mentira para gravar a animação do Assistente IA da página de vendas (lp-assistente.mjs).

Responde sempre a mesma estrutura de página (Gramado e Canela), em streaming e devagar, como a
API de verdade: a gravação sai igual toda vez e não gasta crédito. Uso:

    python3 ia-falsa.py            # escuta em 127.0.0.1:8765

e suba a API com GPT_KEY=falsa OPENAI_BASE_URL=http://127.0.0.1:8765/v1.
"""
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ESTRUTURA = """ESTRUTURA SUGERIDA PARA A PÁGINA
Tipo de página: Roteiro de viagem
Objetivo da página: Vender a saída de julho
Público predominante: Casais e famílias

🟩 SEÇÃO: BANNER INICIAL
Função da seção: impacto
Título: Gramado e Canela no inverno
Subtítulo: 4 dias de serra gaúcha com hotel, café da manhã e passeios guiados.
Destaques:
- Hotel com café
- City tour guiado
- Snowland incluso
Data de saída: 10/07/2026
Data de volta: 13/07/2026
Botão: Quero reservar
Busca de imagem: Gramado inverno

🟩 SEÇÃO: ROTEIRO DIA A DIA
Função da seção: programação
Etiqueta: Roteiro
Título: Como vão ser os 4 dias
Dia 1: Chegada e Rua Coberta
Check-in no hotel e noite livre para o fondue na Rua Coberta.
Dia 2: City tour Gramado e Canela
Lago Negro, Catedral de Pedra e Cascata do Caracol com guia.
Dia 3: Dia de neve no Snowland
Parque de neve indoor com esqui, tobogã e patinação.
Dia 4: Café colonial e volta
Café colonial típico e retorno com a bagagem cheia de chocolate.

🟩 SEÇÃO: RESUMO DO PACOTE
Função da seção: inclusos
Etiqueta: Pacote
Título: O que está incluso
Inclui:
- Hospedagem — 3 noites com café da manhã
- City tour — Gramado e Canela com guia
- Ingresso Snowland
- Transfer aeroporto e hotel
Não inclui:
- Passagem aérea
- Jantares

🟩 SEÇÃO: PREÇOS E PACOTES
Função da seção: valores
Etiqueta: Investimento
Título: Escolha seu pacote
Plano: Adulto
Destaque: sim
Valor: R$ 1.290 por pessoa
Parcelamento: em até 10x sem juros
Detalhes: Quarto duplo com café da manhã
Plano: Criança até 11 anos
Valor: R$ 890
Detalhes: No quarto dos pais
Observação geral: Consulte disponibilidade e condições vigentes.

🟩 SEÇÃO: DÚVIDAS FREQUENTES
Função da seção: dúvidas
Etiqueta: Dúvidas
Título: Perguntas frequentes
Pergunta: Precisa levar roupa de neve?
Resposta: Não. O Snowland empresta a roupa térmica na entrada.
Pergunta: Tem parcelamento?
Resposta: Sim, em até 10x sem juros no cartão.
Pergunta: De onde é a saída?
Resposta: Do aeroporto de Porto Alegre, com transfer até o hotel.
"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        pass

    def do_POST(self):
        length = int(self.headers.get("content-length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        if not body.get("stream"):
            out = json.dumps({
                "id": "r1", "object": "response", "created_at": 0, "model": body.get("model"), "status": "completed",
                "output": [{"type": "message", "id": "m1", "role": "assistant", "status": "completed",
                            "content": [{"type": "output_text", "text": ESTRUTURA, "annotations": []}]}],
                "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
            }).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
            return
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("transfer-encoding", "chunked")
        self.end_headers()

        def send(event):
            data = f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode()
            self.wfile.write(f"{len(data):x}\r\n".encode() + data + b"\r\n")
            self.wfile.flush()

        time.sleep(1.6)  # "pensando"
        seq = 0
        for i in range(0, len(ESTRUTURA), 40):
            seq += 1
            send({"type": "response.output_text.delta", "delta": ESTRUTURA[i:i + 40], "item_id": "m1",
                  "output_index": 0, "content_index": 0, "sequence_number": seq, "logprobs": []})
            time.sleep(0.05)
        send({"type": "response.completed", "sequence_number": seq + 1,
              "response": {"id": "r1", "object": "response", "created_at": 0, "model": body.get("model"),
                           "status": "completed", "output": [],
                           "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}}})
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()


ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
