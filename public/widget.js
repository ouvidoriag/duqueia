/**
 * duque-widget.js — Chat Widget Embutível da Duque IA
 * Versão: 1.0.0
 * Sem dependências externas. Compatível com ES2017+.
 * Uso: <script src="/widget.js" data-title="Duque IA" defer></script>
 */
(function (global) {
  'use strict';

  // ── Localiza a própria tag <script> ─────────────────────────────────────────
  // IMPORTANTE: document.currentScript é null em scripts com `defer` ou `async`.
  // Estratégia: busca pelo src que contém "widget.js", depois pelo data-title,
  // depois pelo último <script> como último recurso.
  var currentScript = (function () {
    if (document.currentScript) return document.currentScript;
    var scripts = document.getElementsByTagName('script');
    // 1ª tentativa: script cujo src contém "widget.js"
    for (var i = scripts.length - 1; i >= 0; i--) {
      if (scripts[i].src && scripts[i].src.indexOf('widget.js') !== -1) {
        return scripts[i];
      }
    }
    // 2ª tentativa: script com data-title (atributo único do widget)
    for (var j = scripts.length - 1; j >= 0; j--) {
      if (scripts[j].hasAttribute('data-title') || scripts[j].hasAttribute('data-position')) {
        return scripts[j];
      }
    }
    // 3ª tentativa: último script da página
    return scripts[scripts.length - 1];
  })();

  // ── Lê atributos de configuração da tag <script> ────────────────────────────
  function attr(name, fallback) {
    if (!currentScript) return fallback;
    var val = currentScript.getAttribute('data-' + name);
    return (val !== null && val !== undefined && val !== '') ? val : fallback;
  }

  // Resolve a origem (origin) a partir da URL do script
  function resolveScriptOrigin() {
    try {
      var src = (currentScript && currentScript.src) ? currentScript.src : '';
      if (!src) return global.location.origin;
      var url = new URL(src, global.location.href);
      return url.origin;
    } catch (e) {
      return global.location.origin;
    }
  }

  // Resolve base path do widget (remove /widget.js do final)
  function resolveBasePath() {
    try {
      var src = (currentScript && currentScript.src) ? currentScript.src : '';
      if (!src) return '';
      return src.replace(/\/widget\.js(\?.*)?$/, '');
    } catch (e) {
      return '';
    }
  }

  var BASE_PATH     = resolveBasePath();
  var SCRIPT_ORIGIN = resolveScriptOrigin();

  var CFG = {
    position : attr('position', 'bottom-right'),          // 'bottom-right' | 'bottom-left'
    theme    : attr('theme',    'prefeitura'),             // 'prefeitura' | 'verde' | 'escuro'
    title    : attr('title',    'Duque IA'),
    char     : attr('char',     'boas_vindas'),
    src      : attr('src',      BASE_PATH + '/embed/chat'),
    mascot   : attr('mascot-src', BASE_PATH + '/assets/personagens/duque_boas_vindas_bracos_abertos.png'),
    // Origens permitidas para postMessage (separadas por vírgula)
    allowedOrigins: (attr('allowed-origins', '') || SCRIPT_ORIGIN)
                      .split(',').map(function(s){ return s.trim(); }).filter(Boolean),
    zIndex: parseInt(attr('z-index', '99999'), 10) || 99999,
  };

  // ── Previne dupla inicialização ──────────────────────────────────────────────
  if (global.__duqueWidgetLoaded) return;
  global.__duqueWidgetLoaded = true;

  // ── Helpers ──────────────────────────────────────────────────────────────────
  var isBottomLeft = CFG.position === 'bottom-left';

  function px(n) { return n + 'px'; }

  function isMobile() { return global.innerWidth < 480; }

  function isAllowedOrigin(origin) {
    return CFG.allowedOrigins.indexOf(origin) !== -1 ||
           CFG.allowedOrigins.indexOf('*') !== -1;
  }

  // ── Injeção de estilos (escopo do botão flutuante) ───────────────────────────
  var CSS = [
    '#duque-widget-btn{',
      'position:fixed;',
      (isBottomLeft ? 'left:16px;' : 'right:16px;'),
      'bottom:16px;',
      'width:68px;height:68px;',
      'border-radius:50%;',
      'background:linear-gradient(135deg,#1a56a0 0%,#0d3b7a 100%);',
      'box-shadow:0 4px 20px rgba(0,0,0,0.30);',
      'cursor:pointer;',
      'border:none;padding:0;margin:0;',
      'z-index:', CFG.zIndex, ';',
      'transition:transform 0.18s ease,box-shadow 0.18s ease;',
      'display:flex;align-items:center;justify-content:center;',
      'overflow:visible;',
    '}',
    '#duque-widget-btn:hover{transform:scale(1.08);box-shadow:0 6px 28px rgba(0,0,0,0.38);}',
    '#duque-widget-btn.duque-open{transform:rotate(10deg) scale(1.04);}',
    '#duque-widget-btn img{width:52px;height:52px;object-fit:contain;border-radius:50%;pointer-events:none;transition:transform 0.18s;}',

    /* Badge de não lida */
    '#duque-widget-badge{',
      'position:absolute;top:4px;',
      (isBottomLeft ? 'right:4px;' : 'right:4px;'),
      'width:14px;height:14px;',
      'background:#ff4d00;border-radius:50%;',
      'border:2px solid #fff;',
      'display:none;',
      'animation:duque-pulse 1.4s ease-in-out infinite;',
    '}',
    '@keyframes duque-pulse{0%,100%{transform:scale(1);}50%{transform:scale(1.25);}}',

    /* Tooltip */
    '#duque-widget-tooltip{',
      'position:absolute;bottom:76px;',
      (isBottomLeft ? 'left:0;' : 'right:0;'),
      'white-space:nowrap;',
      'background:rgba(10,30,70,0.92);color:#fff;',
      'font-size:13px;font-family:system-ui,sans-serif;',
      'padding:6px 12px;border-radius:8px;',
      'pointer-events:none;',
      'opacity:0;transition:opacity 0.2s;',
      'z-index:', CFG.zIndex + 1, ';',
    '}',
    '#duque-widget-btn:hover #duque-widget-tooltip{opacity:1;}',

    /* Container do iframe */
    '#duque-widget-panel{',
      'position:fixed;',
      (isBottomLeft ? 'left:16px;' : 'right:16px;'),
      'bottom:96px;',
      'width:380px;height:580px;',
      'border-radius:20px;',
      'overflow:hidden;',
      'box-shadow:0 8px 40px rgba(0,0,0,0.30);',
      'z-index:', CFG.zIndex - 1, ';',
      'opacity:0;',
      'transform:translateY(24px) scale(0.97);',
      'pointer-events:none;',
      'transition:opacity 0.22s ease,transform 0.22s ease;',
      'background:#fff;',
    '}',
    '#duque-widget-panel.duque-panel-open{opacity:1;transform:translateY(0) scale(1);pointer-events:auto;}',
    '#duque-widget-panel.duque-panel-expanded{width:95vw !important;height:90vh !important;bottom:4vh !important;right:2.5vw !important;left:auto !important;border-radius:16px;}',
    '#duque-widget-iframe{width:100%;height:100%;border:none;display:block;}',

    /* Responsivo mobile */
    '@media(max-width:479px){',
      '#duque-widget-panel{width:100% !important;height:85vh !important;bottom:0 !important;right:0 !important;left:0 !important;border-radius:16px 16px 0 0 !important;}',
    '}',
  ].join('');

  var styleEl = document.createElement('style');
  styleEl.id = 'duque-widget-styles';
  styleEl.textContent = CSS;
  document.head.appendChild(styleEl);

  // ── Botão flutuante ──────────────────────────────────────────────────────────
  var btn = document.createElement('button');
  btn.id = 'duque-widget-btn';
  btn.setAttribute('aria-label', 'Falar com a Duque IA');
  btn.setAttribute('title', 'Falar com a Duque IA');
  btn.setAttribute('type', 'button');

  var mascotImg = document.createElement('img');
  mascotImg.src = CFG.mascot;
  mascotImg.alt = 'Duque IA';
  btn.appendChild(mascotImg);

  var badge = document.createElement('span');
  badge.id = 'duque-widget-badge';
  badge.setAttribute('aria-label', 'Nova mensagem');
  btn.appendChild(badge);

  var tooltip = document.createElement('span');
  tooltip.id = 'duque-widget-tooltip';
  tooltip.textContent = 'Falar com a Duque IA';
  btn.appendChild(tooltip);

  document.body.appendChild(btn);

  // ── Painel (container do iframe) ─────────────────────────────────────────────
  var panel = document.createElement('div');
  panel.id = 'duque-widget-panel';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-label', CFG.title);
  panel.setAttribute('aria-modal', 'true');

  // Monta a URL do iframe com parâmetros de configuração
  var iframeSrc = (function () {
    try {
      var u = new URL(CFG.src, global.location.href);
      u.searchParams.set('title', CFG.title);
      u.searchParams.set('theme', CFG.theme);
      u.searchParams.set('char',  CFG.char);
      return u.toString();
    } catch (e) {
      return CFG.src + '?title=' + encodeURIComponent(CFG.title) +
             '&theme=' + encodeURIComponent(CFG.theme) +
             '&char=' + encodeURIComponent(CFG.char);
    }
  })();

  var iframe = document.createElement('iframe');
  iframe.id = 'duque-widget-iframe';
  iframe.setAttribute('title', CFG.title);
  iframe.setAttribute('allow', 'microphone');
  iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-popups allow-modals');
  // O iframe é carregado de forma lazy (src só é definido quando o widget abre pela 1ª vez)
  iframe.setAttribute('data-src', iframeSrc);
  iframe.setAttribute('loading', 'lazy');
  panel.appendChild(iframe);

  document.body.appendChild(panel);

  // ── Estado interno ───────────────────────────────────────────────────────────
  var state = {
    open: false,
    expanded: false,
    iframeLoaded: false,
    hasUnread: false,
  };

  // ── Funções de abertura/fechamento ───────────────────────────────────────────
  function openPanel() {
    state.open = true;
    btn.classList.add('duque-open');
    btn.setAttribute('aria-expanded', 'true');
    panel.classList.add('duque-panel-open');
    clearBadge();

    // Carrega o iframe de forma lazy na primeira abertura
    if (!state.iframeLoaded) {
      state.iframeLoaded = true;
      iframe.src = iframe.getAttribute('data-src');
    }

    // Foca o iframe após abrir
    setTimeout(function () {
      sendToIframe({ type: 'duque:focus' });
      try { iframe.focus(); } catch (e) {}
    }, 280);
  }

  function closePanel() {
    state.open = false;
    state.expanded = false;
    btn.classList.remove('duque-open');
    btn.setAttribute('aria-expanded', 'false');
    panel.classList.remove('duque-panel-open');
    panel.classList.remove('duque-panel-expanded');
  }

  function togglePanel() {
    if (state.open) closePanel(); else openPanel();
  }

  function expandPanel() {
    state.expanded = !state.expanded;
    if (state.expanded) {
      panel.classList.add('duque-panel-expanded');
    } else {
      panel.classList.remove('duque-panel-expanded');
    }
  }

  function showBadge() {
    if (!state.open) {
      state.hasUnread = true;
      badge.style.display = 'block';
    }
  }

  function clearBadge() {
    state.hasUnread = false;
    badge.style.display = 'none';
  }

  // ── Click handler no botão ───────────────────────────────────────────────────
  btn.addEventListener('click', function (e) {
    e.stopPropagation();
    togglePanel();
  });

  // ── Fechar ao pressionar ESC ─────────────────────────────────────────────────
  document.addEventListener('keydown', function (e) {
    if ((e.key === 'Escape' || e.keyCode === 27) && state.open) {
      closePanel();
      btn.focus();
    }
  });

  // ── Fechar ao clicar fora do painel (somente desktop) ────────────────────────
  document.addEventListener('click', function (e) {
    if (!state.open) return;
    if (!panel.contains(e.target) && e.target !== btn) {
      closePanel();
    }
  });

  // ── postMessage: envia comandos ao iframe ────────────────────────────────────
  function sendToIframe(payload) {
    if (!iframe.contentWindow) return;
    var origin = SCRIPT_ORIGIN;
    try {
      iframe.contentWindow.postMessage(
        Object.assign({ source: 'duque-host' }, payload),
        origin
      );
    } catch (e) {
      // Cross-origin post pode falhar em alguns contextos — silencioso
    }
  }

  // ── postMessage: recebe eventos do iframe ────────────────────────────────────
  global.addEventListener('message', function (event) {
    // Valida origem: só aceita mensagens do iframe configurado
    if (!isAllowedOrigin(event.origin)) return;

    var data = event.data;
    if (!data || typeof data !== 'object') return;
    if (data.source !== 'duque-widget') return;

    switch (data.type) {
      case 'duque:ready':
        // Iframe carregado e pronto
        if (!state.open) showBadge();
        break;

      case 'duque:close':
        closePanel();
        btn.focus();
        break;

      case 'duque:toggle_expand':
        expandPanel();
        break;

      case 'duque:message_received':
        // Nova mensagem da IA enquanto o painel está fechado → pulsa badge
        if (!state.open) showBadge();
        break;

      default:
        break;
    }
  });

  // ── API pública mínima (uso avançado via JS) ─────────────────────────────────
  global.DuqueWidget = {
    open    : openPanel,
    close   : closePanel,
    toggle  : togglePanel,
    send    : function (text) { sendToIframe({ type: 'duque:send_message', payload: { text: text } }); },
    version : '1.0.0',
  };

})(window);

