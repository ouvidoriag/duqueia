# Chat Widget Embutível — Duque IA

> **Versão:** 1.0.0 · **Atualizado em:** Novembro 2026

Este guia documenta como integrar o assistente virtual **Duque IA** em qualquer portal da Prefeitura de Duque de Caxias usando uma única linha de HTML.

---

## Sumário

1. [Visão Geral](#visão-geral)
2. [Instalação Rápida](#instalação-rápida)
3. [Opções de Configuração](#opções-de-configuração)
4. [Temas](#temas)
5. [Personagens (Mascotes)](#personagens-mascotes)
6. [API JavaScript](#api-javascript)
7. [Protocolo postMessage](#protocolo-postmessage)
8. [Segurança e CORS](#segurança-e-cors)
9. [Configuração do Nginx](#configuração-do-nginx)
10. [Variáveis de Ambiente](#variáveis-de-ambiente)
11. [Teste Local](#teste-local)
12. [Solução de Problemas](#solução-de-problemas)

---

## Visão Geral

```
Sites da Prefeitura                VPS Duque IA
─────────────────────              ──────────────────────────────────
portal.duquedecaxias.rj.gov.br ──► Nginx /duqueia/widget.js
                                        │
                           widget.js injeta botão mascote + iframe
                                        │
                           iframe src = /duqueia/embed/chat
                                        │
                           embed-chat.html ──► Node.js ──► Python Workers
                                                                  │
                                                           RAG / Gemini
```

**Características:**
- ✅ Zero dependências — JS puro, sem frameworks
- ✅ < 15 KB minificado
- ✅ Funciona sob subpath Nginx `/duqueia/`
- ✅ Responsivo: bottom sheet em mobile (< 480 px)
- ✅ Lazy load do iframe (carrega só no primeiro clique)
- ✅ postMessage com validação de origem
- ✅ LGPD: nenhum dado pessoal persistido no cliente além de `sessionStorage` (ID de sessão efêmero)

---

## Instalação Rápida

Adicione **uma linha** antes do `</body>` de qualquer página:

```html
<script
  src="https://ogm.duquedecaxias.rj.gov.br/duqueia/widget.js"
  data-title="Duque IA"
  defer>
</script>
```

> [!NOTE]
> O widget carrega de forma assíncrona (`defer`) e não bloqueia o carregamento da página hospedeira.

---

## Opções de Configuração

Todos os parâmetros são atributos `data-*` na tag `<script>`.

| Atributo | Padrão | Valores aceitos | Descrição |
|---|---|---|---|
| `data-position` | `bottom-right` | `bottom-right` · `bottom-left` | Posição do botão flutuante |
| `data-theme` | `prefeitura` | `prefeitura` · `verde` · `escuro` | Tema de cores do chat |
| `data-title` | `Duque IA` | qualquer texto | Título exibido no cabeçalho do chat |
| `data-char` | `boas_vindas` | ver tabela abaixo | Personagem inicial do mascote |
| `data-src` | *(automático)* | URL completa | URL do iframe embed (substitui o padrão) |
| `data-mascot-src` | *(automático)* | URL do PNG | Sobrescreve a imagem do botão flutuante |
| `data-allowed-origins` | *(origem do script)* | lista separada por vírgula | Origens autorizadas no postMessage |
| `data-z-index` | `99999` | número inteiro | Z-index do botão e do painel |

**Exemplo completo:**

```html
<script
  src="https://ogm.duquedecaxias.rj.gov.br/duqueia/widget.js"
  data-position="bottom-right"
  data-theme="prefeitura"
  data-title="Atendimento Virtual"
  data-char="atendimento"
  data-allowed-origins="https://www.duquedecaxias.rj.gov.br,https://portal.duquedecaxias.rj.gov.br"
  defer>
</script>
```

---

## Temas

| Valor | Aparência |
|---|---|
| `prefeitura` | Azul institucional (#1a56a0) — padrão |
| `verde` | Verde (#1a7a40) — para portais de meio ambiente |
| `escuro` | Fundo escuro (#0d1b2a) — para painéis noturnos |

---

## Personagens (Mascotes)

| Valor (`data-char`) | Arquivo PNG | Uso recomendado |
|---|---|---|
| `boas_vindas` | `duque_boas_vindas_bracos_abertos.png` | Saudação inicial (padrão) |
| `atendimento` | `duque_atendimento_telefone.png` | Atendimento e ouvidoria |
| `joinha` | `duque_joinha_aprovado.png` | Confirmação e aprovação |
| `saude` | `duque_saude_jaleco.png` | Portais de saúde |
| `tablet` | `duque_consultando_tablet.png` | Consulta e pesquisa |
| `executivo` | `duque_executivo_analisando.png` | Dashboard executivo |
| `gestao` | `duque_gestao_foco_caneca.png` | Gestão e administração |
| `polo` | `duque_polo_apresenta.png` | Apresentações |
| `notebook` | `duque_desenvolvedor_notebook.png` | Portais técnicos |
| `confiante` | `duque_confiante_bracos_cruzados.png` | Segurança institucional |

---

## API JavaScript

Após o widget carregar, o objeto `window.DuqueWidget` fica disponível:

```javascript
// Abrir o painel de chat
DuqueWidget.open();

// Fechar o painel
DuqueWidget.close();

// Alternar aberto/fechado
DuqueWidget.toggle();

// Enviar uma mensagem programaticamente
DuqueWidget.send('Quero abrir uma manifestação na Ouvidoria.');

// Versão do widget
console.log(DuqueWidget.version); // "1.0.0"
```

**Exemplo de uso em botão de chamada à ação:**

```html
<button onclick="DuqueWidget.open()">
  💬 Fale com a Duque IA
</button>
```

---

## Protocolo postMessage

O widget e o iframe se comunicam via `window.postMessage`. Você pode ouvir os eventos e enviar comandos manualmente se necessário.

### Eventos emitidos pelo iframe → página hospedeira

| `type` | Quando ocorre | `payload` |
|---|---|---|
| `duque:ready` | iframe carregado e pronto | `{ version }` |
| `duque:close` | Usuário clicou em fechar no chat | — |
| `duque:toggle_expand` | Usuário clicou em expandir/minimizar | — |
| `duque:message_received` | IA respondeu (painel pode estar fechado) | `{ text }` |

**Escutar eventos:**

```javascript
window.addEventListener('message', function (event) {
  // IMPORTANTE: sempre valide a origem!
  if (event.origin !== 'https://ogm.duquedecaxias.rj.gov.br') return;
  if (!event.data || event.data.source !== 'duque-widget') return;

  if (event.data.type === 'duque:message_received') {
    console.log('Nova mensagem da IA:', event.data.payload);
  }
});
```

### Comandos enviados pela página → iframe

| `type` | Efeito |
|---|---|
| `duque:focus` | Foca o campo de texto do chat |
| `duque:send_message` | Envia uma mensagem (`payload.text`) |
| `duque:set_character` | Troca o personagem (`payload.char`) |
| `duque:set_title` | Atualiza o título do cabeçalho (`payload.title`) |

```javascript
// Envio manual via postMessage (alternativa a DuqueWidget.send)
var iframe = document.querySelector('#duque-widget-iframe');
iframe.contentWindow.postMessage(
  { source: 'duque-host', type: 'duque:send_message', payload: { text: 'Olá!' } },
  'https://ogm.duquedecaxias.rj.gov.br'
);
```

---

## Segurança e CORS

### No servidor (variável de ambiente)

```env
# .env
# Lista de origens autorizadas a incorporar o widget via iframe (separadas por vírgula)
# Use * para ambiente de desenvolvimento ou liste os domínios reais em produção
EMBED_ALLOWED_ORIGINS=https://www.duquedecaxias.rj.gov.br,https://portal.duquedecaxias.rj.gov.br
```

O servidor envia `Content-Security-Policy: frame-ancestors` com as origens configuradas.

### No widget (atributo data-allowed-origins)

```html
<script
  src=".../widget.js"
  data-allowed-origins="https://www.duquedecaxias.rj.gov.br,https://portal.duquedecaxias.rj.gov.br"
  defer>
</script>
```

O widget valida `event.origin` antes de processar qualquer `postMessage` recebido.

> [!CAUTION]
> Em produção, **nunca** deixe `EMBED_ALLOWED_ORIGINS=*` nem `data-allowed-origins` vazio ou com `*`. Isso permitiria que qualquer site incorporasse o chat e enviasse comandos via postMessage.

> [!IMPORTANT]
> O widget **não expõe** chaves de API, tokens ou credenciais. Toda a lógica de IA permanece no servidor. O navegador só recebe a resposta final em texto.

---

## Configuração do Nginx

Veja o arquivo [`docs/nginx-widget.conf`](nginx-widget.conf) para o trecho completo.

Pontos essenciais:

```nginx
# widget.js — cache curto (5 min) para propagação rápida de atualizações
location = /duqueia/widget.js {
    proxy_pass http://duque_ia_backend/widget.js;
    add_header Cache-Control "public, max-age=300, must-revalidate" always;
    add_header Access-Control-Allow-Origin "*" always;
}

# /embed/chat — remove X-Frame-Options global; CSP do Node.js prevalece
location /duqueia/embed {
    proxy_pass http://duque_ia_backend/embed;
    proxy_hide_header X-Frame-Options;
    add_header X-Frame-Options "" always;
}
```

---

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `EMBED_ALLOWED_ORIGINS` | `*` | Origens autorizadas a incorporar o widget via iframe |
| `PORT` | `3000` | Porta do servidor Node.js |

---

## Teste Local

1. Inicie o servidor: `node server.js`
2. Abra: [`http://localhost:3000/tests/test_widget_embed.html`](http://localhost:3000/tests/test_widget_embed.html)
3. Clique no mascote (canto inferior direito) e verifique o chat

> [!TIP]
> Ative o painel de debug "🐛 Debug postMessage" na página de teste para visualizar todos os eventos de comunicação em tempo real.

---

## Solução de Problemas

### Widget não aparece

- Verifique se o script carregou sem erros no console do navegador
- Confirme que a URL do `src` está correta (sem barra dupla sob `/duqueia/`)
- Teste direto: `curl http://localhost:3000/widget.js` deve retornar o JS

### Iframe não carrega (tela em branco)

- Verifique se `/embed/chat` retorna 200: `curl http://localhost:3000/embed/chat`
- Confirme que `embed-chat.html` existe em `public/`
- Verifique o console do iframe (F12 → aba Console, selecionar contexto do iframe)

### "Refused to display in frame" no console

- O header `X-Frame-Options` ou `Content-Security-Policy: frame-ancestors` está bloqueando
- Confirme que `EMBED_ALLOWED_ORIGINS` inclui o domínio que tenta incorporar o widget
- No Nginx, verifique se `proxy_hide_header X-Frame-Options` está configurado em `/duqueia/embed`

### postMessage não chega ao widget

- Confirme que `data-allowed-origins` inclui a origem da página hospedeira
- A origem deve incluir protocolo e porta: `http://localhost:3000`, não apenas `localhost`
- Abra o console e verifique: `window.__duqueWidgetLoaded === true`

### Badge de nova mensagem não aparece

- O badge só aparece quando o painel está **fechado** e chega um evento `duque:message_received`
- Verifique se o iframe está emitindo o evento (painel de debug)
- Confirme que a origem do iframe está em `data-allowed-origins`
