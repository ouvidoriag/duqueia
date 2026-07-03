const { spawn } = require('child_process');
const http = require('http');
const path = require('path');
const fs = require('fs');

// ── Configuração ─────────────────────────────────────────────────────────────
const PYTHON_PATH = process.platform === 'win32' ? 'python' : 'python3';
const PORT = process.env.PORT || 3000;
const AGENT_PATH = path.join(__dirname, 'agent', 'main.py');
const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutos de inatividade

// Cache de agentes instanciados por sessão: Map<sessionId, sessionObj>
const activeSessions = new Map();

// ── Mimetypes de arquivos estáticos ──────────────────────────────────────────
const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.ico':  'image/x-icon',
  '.png':  'image/png',
  '.svg':  'image/svg+xml',
};

// ── Gerenciamento de sessões ──────────────────────────────────────────────────

/**
 * Cria ou retorna uma instância persistente do processo Python para a sessão.
 */
function getOrCreateAgentInstance(sessionId) {
  if (activeSessions.has(sessionId)) {
    const existing = activeSessions.get(sessionId);
    // Reinicia sessão se o processo morreu
    if (existing.process.exitCode !== null) {
      console.warn(`[Server] Processo da sessão ${sessionId} havia morrido. Reiniciando...`);
      activeSessions.delete(sessionId);
    } else {
      // Renova o timer de timeout ao receber nova mensagem
      clearTimeout(existing.timeoutId);
      existing.timeoutId = setTimeout(() => destroySession(sessionId), SESSION_TIMEOUT_MS);
      return existing;
    }
  }

  console.log(`[Server] Criando nova instância do agente para a sessão: ${sessionId}`);

  const pyProcess = spawn(PYTHON_PATH, ['-u', AGENT_PATH], {
    cwd: __dirname,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' }
  });

  const sessionObj = {
    process: pyProcess,
    currentResolve: null,
    currentReject: null,
    buffer: '',
    initialized: false,
    timeoutId: null,
  };

  // ── Stdout: bufferiza e extrai respostas JSON ───────────────────────────
  pyProcess.stdout.on('data', (data) => {
    const chunk = data.toString('utf-8');
    sessionObj.buffer += chunk;
    processBuffer(sessionObj);
  });

  // ── Stderr: apenas log (não afeta o fluxo) ─────────────────────────────
  pyProcess.stderr.on('data', (data) => {
    console.error(`[Python stderr - ${sessionId}]: ${data.toString('utf-8').trim()}`);
  });

  // ── Close: limpa sessão e rejeita qualquer promise pendente ───────────
  pyProcess.on('close', (code) => {
    console.log(`[Server] Processo da sessão ${sessionId} encerrou com código ${code}`);
    if (sessionObj.currentReject) {
      sessionObj.currentReject(new Error(`Processo do agente encerrou inesperadamente (código ${code}).`));
      sessionObj.currentResolve = null;
      sessionObj.currentReject = null;
    }
    clearTimeout(sessionObj.timeoutId);
    activeSessions.delete(sessionId);
  });

  // ── Timeout de inatividade ──────────────────────────────────────────────
  sessionObj.timeoutId = setTimeout(() => destroySession(sessionId), SESSION_TIMEOUT_MS);

  activeSessions.set(sessionId, sessionObj);
  return sessionObj;
}

/**
 * Destrói graciosamente uma sessão após inatividade.
 */
function destroySession(sessionId) {
  const session = activeSessions.get(sessionId);
  if (!session) return;
  console.log(`[Server] Encerrando sessão inativa: ${sessionId}`);
  try { session.process.kill('SIGTERM'); } catch (_) {}
  activeSessions.delete(sessionId);
}

// ── Processamento de Buffer ───────────────────────────────────────────────────

/**
 * Extrai e resolve blocos de JSON completos do stream de saída do Python.
 */
function processBuffer(session) {
  const text = session.buffer;
  let startIdx = text.indexOf('{');
  if (startIdx === -1) return;

  let braceCount = 0;
  let endIdx = -1;
  for (let i = startIdx; i < text.length; i++) {
    if (text[i] === '{') braceCount++;
    else if (text[i] === '}') {
      braceCount--;
      if (braceCount === 0) { endIdx = i; break; }
    }
  }

  if (endIdx === -1) return; // JSON ainda incompleto no buffer

  const jsonCandidate = text.substring(startIdx, endIdx + 1);
  session.buffer = text.substring(endIdx + 1);

  try {
    const parsed = JSON.parse(jsonCandidate);
    if (session.currentResolve) {
      session.currentResolve(parsed);
      session.currentResolve = null;
      session.currentReject = null;
    }
  } catch (_) {
    // Bloco JSON mal formado — descarta e tenta extrair o próximo
    session.buffer = text.substring(startIdx + 1);
    processBuffer(session);
  }
}

// ── Comunicação com o Agente ──────────────────────────────────────────────────

/**
 * Envia mensagem ao processo Python e retorna uma Promise com a resposta JSON.
 */
function sendMessageToAgent(sessionId, message) {
  return new Promise((resolve, reject) => {
    // Timeout de 90s por turno para evitar travamentos
    const turnTimeout = setTimeout(() => {
      reject(new Error('Tempo de resposta do agente excedido (90s).'));
      const session = activeSessions.get(sessionId);
      if (session) { session.currentResolve = null; session.currentReject = null; }
    }, 90_000);

    const session = getOrCreateAgentInstance(sessionId);

    if (session.currentResolve) {
      clearTimeout(turnTimeout);
      return reject(new Error('Requisição pendente para esta sessão. Aguarde.'));
    }

    session.currentResolve = (data) => { clearTimeout(turnTimeout); resolve(data); };
    session.currentReject  = (err)  => { clearTimeout(turnTimeout); reject(err); };

    const line = `${message}\n`;
    session.process.stdin.write(Buffer.from(line, 'utf-8'));
  });
}

// ── Servidor HTTP ─────────────────────────────────────────────────────────────

const server = http.createServer((req, res) => {
  // ── CORS ────────────────────────────────────────────────────────────────
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // ── Health Check (Render usa isso para verificar se o serviço está vivo) ─
  if (req.url === '/health' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', sessions: activeSessions.size }));
    return;
  }

  // ── API de Chat ─────────────────────────────────────────────────────────
  if (req.url === '/api/chat' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString('utf-8'); });
    req.on('end', async () => {
      try {
        const payload = JSON.parse(body);
        const message = (payload.message || '').trim();
        const sessionId = (payload.sessionId || 'default').replace(/[^a-zA-Z0-9_-]/g, '');

        if (!message) {
          res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
          res.end(JSON.stringify({ error: 'Mensagem não pode ser vazia.' }));
          return;
        }

        if (message.length > 2000) {
          res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
          res.end(JSON.stringify({ error: 'Mensagem muito longa (máximo 2000 caracteres).' }));
          return;
        }

        console.log(`[API] [${sessionId}] Recebido: "${message.substring(0, 80)}..."`);
        const responseData = await sendMessageToAgent(sessionId, message);

        res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify(responseData));
      } catch (err) {
        console.error('[API Error]:', err.message);
        res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify({ error: err.message || 'Erro interno do servidor.' }));
      }
    });
    return;
  }

  // ── Arquivos Estáticos ──────────────────────────────────────────────────
  const urlPath = req.url === '/' ? '/chat.html' : req.url;
  const filePath = path.join(__dirname, 'public', urlPath);

  // Proteção contra path traversal: impede acesso a arquivos fora de /public
  if (!filePath.startsWith(path.join(__dirname, 'public'))) {
    res.writeHead(403);
    res.end('Acesso Proibido');
    return;
  }

  const ext = path.extname(filePath);
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') { res.writeHead(404); res.end('Página não encontrada'); }
      else { res.writeHead(500); res.end(`Erro: ${err.code}`); }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    }
  });
});

// ── Graceful Shutdown ─────────────────────────────────────────────────────────
function shutdown(signal) {
  console.log(`\n[Server] ${signal} recebido. Encerrando sessões ativas...`);
  for (const [id, session] of activeSessions) {
    try { session.process.kill('SIGTERM'); } catch (_) {}
    clearTimeout(session.timeoutId);
    console.log(`  → Sessão encerrada: ${id}`);
  }
  server.close(() => {
    console.log('[Server] Servidor encerrado com sucesso.');
    process.exit(0);
  });
  setTimeout(() => process.exit(1), 5000); // Força saída após 5s se travar
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT',  () => shutdown('SIGINT'));

// ── Inicialização ─────────────────────────────────────────────────────────────
server.listen(PORT, () => {
  console.log(`\n==========================================================`);
  console.log(`🚀 DUQUE IA Chat Server rodando em http://localhost:${PORT}`);
  console.log(`   Health Check disponível em: http://localhost:${PORT}/health`);
  console.log(`==========================================================\n`);
});
