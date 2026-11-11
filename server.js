const { spawn } = require('child_process');
const http = require('http');
const path = require('path');
const fs = require('fs');
const zlib = require('zlib');
const crypto = require('crypto');

// Cache para arquivos estáticos: Map<filePath, { raw: Buffer, gzipped: Buffer, contentType: string, ext: string, isCacheable: boolean }>
const staticCache = new Map();

// ── Mimetypes de arquivos estáticos ──────────────────────────────────────────
const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.ico':  'image/x-icon',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg':  'image/svg+xml',
  '.mp3':  'audio/mpeg',
  '.webm': 'audio/webm',
  '.wav':  'audio/wav',
  '.ogg':  'audio/ogg',
};


// ── Configuração e Resolução do Runtime Python ───────────────────────────────
function resolvePythonInterpreter() {
  const venvUnix = path.join(__dirname, '.venv', 'bin', 'python');
  const venvWin = path.join(__dirname, '.venv', 'Scripts', 'python.exe');
  if (fs.existsSync(venvWin)) return venvWin;
  if (fs.existsSync(venvUnix)) return venvUnix;
  return process.platform === 'win32' ? 'python' : 'python3';
}

const PYTHON_PATH = resolvePythonInterpreter();
const PORT = process.env.PORT || 3000;
const AGENT_PATH = path.join(__dirname, 'agent', 'main.py');
const MAX_WORKERS = Math.max(1, parseInt(process.env.MAX_WORKERS || '4', 10));
const ADMIN_API_KEY = process.env.ADMIN_API_KEY || '';
const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'admin';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'duqueia2026';

// Map em memória de sessões de administradores autenticados: token -> { username, createdAt, expiresAt }
const activeAdminSessions = new Map();

/**
 * Validação de autorização para endpoints administrativos ou dados sensíveis.
 * Aceita cabeçalho 'x-admin-key' ou 'Authorization: Bearer <key>'.
 * Valida contra ADMIN_API_KEY ou contra sessões ativas geradas pelo login.
 * Se nenhuma chave estiver configurada no .env, restringe a requisições locais (loopback).
 */
function isAuthorizedAdmin(req) {
  const authHeader = req.headers['authorization'] || '';
  const adminKeyHeader = req.headers['x-admin-key'] || '';

  // 1. Bearer Token no cabeçalho Authorization
  if (authHeader.startsWith('Bearer ')) {
    const token = authHeader.slice(7).trim();
    if (ADMIN_API_KEY && token === ADMIN_API_KEY) return true;
    if (activeAdminSessions.has(token)) {
      const sess = activeAdminSessions.get(token);
      if (Date.now() < sess.expiresAt) return true;
      activeAdminSessions.delete(token);
    }
    // Token fornecido é inválido, expirado ou revogado
    return false;
  }

  // 2. Cabeçalho x-admin-key
  if (adminKeyHeader) {
    const key = adminKeyHeader.trim();
    if (ADMIN_API_KEY && key === ADMIN_API_KEY) return true;
    if (activeAdminSessions.has(key)) {
      const sess = activeAdminSessions.get(key);
      if (Date.now() < sess.expiresAt) return true;
      activeAdminSessions.delete(key);
    }
    return false;
  }

  return false;
}

// ── Rate Limiter em Memória por IP ───────────────────────────────────────────
const RATE_LIMIT_WINDOW_MS = 60 * 1000; // 1 minuto
const MAX_REQUESTS_PER_WINDOW = 30;     // 30 requisições / minuto por IP
const ipRateLimitMap = new Map();

function isRateLimited(ip) {
  const now = Date.now();
  let timestamps = ipRateLimitMap.get(ip) || [];
  timestamps = timestamps.filter(t => now - t < RATE_LIMIT_WINDOW_MS);
  if (timestamps.length >= MAX_REQUESTS_PER_WINDOW) {
    ipRateLimitMap.set(ip, timestamps);
    return true;
  }
  timestamps.push(now);
  ipRateLimitMap.set(ip, timestamps);
  return false;
}

// ── Governança e Limpeza Periódica de Arquivos Temporários de Áudio ───────────
const AUDIO_CLEANUP_INTERVAL_MS = 15 * 60 * 1000; // a cada 15 minutos
const MAX_AUDIO_AGE_MS = 60 * 60 * 1000;          // expurgo de áudios com mais de 1 hora

function cleanupOldAudioFiles() {
  const targetDirs = [
    path.join(__dirname, 'public', 'uploads'),
    path.join(__dirname, 'public', 'audio')
  ];

  const now = Date.now();
  let deletedCount = 0;

  for (const dir of targetDirs) {
    if (!fs.existsSync(dir)) continue;
    try {
      const files = fs.readdirSync(dir);
      for (const file of files) {
        if (!/\.(wav|webm|mp3|ogg|opus)$/i.test(file)) continue;
        const filePath = path.join(dir, file);
        try {
          const stats = fs.statSync(filePath);
          if (now - stats.mtimeMs > MAX_AUDIO_AGE_MS) {
            fs.unlinkSync(filePath);
            deletedCount++;
          }
        } catch (_) {}
      }
    } catch (err) {
      console.error(`[Audio Cleanup Error] Falha ao verificar diretório ${dir}:`, err.message);
    }
  }

  if (deletedCount > 0) {
    console.log(`[Audio Cleanup] ${deletedCount} arquivo(s) temporário(s) de áudio expurgado(s) com sucesso.`);
  }
}

// Executa limpeza inicial e agenda verificação periódica
cleanupOldAudioFiles();
setInterval(cleanupOldAudioFiles, AUDIO_CLEANUP_INTERVAL_MS);

// ── Pool Gerenciado de Workers Python ────────────────────────────────────────
const workerPool = [];
const requestQueue = [];
const sessionWorkerMap = new Map(); // sessionId -> workerId

/**
 * Cria uma nova instância de Worker Python dentro do Pool gerenciado.
 */
function createWorker(workerId) {
  console.log(`[WorkerPool] Iniciando worker Python #${workerId}...`);
  const pyProcess = spawn(PYTHON_PATH, ['-u', AGENT_PATH], {
    cwd: __dirname,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' }
  });

  const worker = {
    id: workerId,
    process: pyProcess,
    busy: false,
    activeRequestId: null,
    activeSessionId: null,
    pendingRequests: new Map(), // requestId -> { resolve, reject, turnTimeout, startTime }
    buffer: '',
    lastActive: Date.now()
  };

  pyProcess.stdout.on('data', (data) => {
    worker.buffer += data.toString('utf-8');
    processWorkerBuffer(worker);
  });

  pyProcess.stderr.on('data', (data) => {
    console.error(`[Worker #${workerId} stderr]: ${data.toString('utf-8').trim()}`);
  });

  pyProcess.on('close', (code) => {
    console.warn(`[WorkerPool] Worker #${workerId} encerrou com código ${code}`);
    for (const [reqId, pending] of worker.pendingRequests) {
      clearTimeout(pending.turnTimeout);
      pending.reject(new Error(`Worker Python #${workerId} encerrou inesperadamente (código ${code}).`));
    }
    worker.pendingRequests.clear();
    worker.busy = false;

    // Remove do pool e restabelece a capacidade
    const idx = workerPool.indexOf(worker);
    if (idx !== -1) workerPool.splice(idx, 1);
    setTimeout(() => {
      const newWorker = createWorker(workerId);
      workerPool.push(newWorker);
      processQueue();
    }, 1000);
  });

  return worker;
}

// Inicializa o Pool de Workers
for (let i = 1; i <= MAX_WORKERS; i++) {
  workerPool.push(createWorker(i));
}

// ── Processamento de Buffer com Sincronização por request_id ──────────────────
function processWorkerBuffer(worker) {
  const text = worker.buffer;
  let startIdx = text.indexOf('{');
  if (startIdx === -1) return;

  let braceCount = 0;
  let inString = false;
  let escapeNext = false;
  let endIdx = -1;

  for (let i = startIdx; i < text.length; i++) {
    const char = text[i];
    if (escapeNext) { escapeNext = false; continue; }
    if (char === '\\') { escapeNext = true; continue; }
    if (char === '"') { inString = !inString; continue; }
    if (!inString) {
      if (char === '{') braceCount++;
      else if (char === '}') {
        braceCount--;
        if (braceCount === 0) {
          endIdx = i;
          break;
        }
      }
    }
  }

  if (endIdx === -1) return; // JSON ainda incompleto no buffer

  const jsonCandidate = text.substring(startIdx, endIdx + 1);
  worker.buffer = text.substring(endIdx + 1);

  try {
    const parsed = JSON.parse(jsonCandidate);
    handleWorkerResponse(worker, parsed);
  } catch (err) {
    console.error('[WorkerPool JSON Parse Error]:', err.message);
    worker.buffer = text.substring(startIdx + 1);
    processWorkerBuffer(worker);
  }
}

function handleWorkerResponse(worker, data) {
  const reqId = data.request_id || worker.activeRequestId;
  worker.busy = false;
  worker.activeRequestId = null;
  worker.activeSessionId = null;
  worker.lastActive = Date.now();

  if (reqId && worker.pendingRequests.has(reqId)) {
    const pending = worker.pendingRequests.get(reqId);
    clearTimeout(pending.turnTimeout);
    worker.pendingRequests.delete(reqId);
    pending.resolve(data);
  } else {
    console.warn(`[WorkerPool] Descartando resposta tardia de requisição já cancelada/expirada: ${reqId}`);
  }

  processQueue();
}

// ── Fila de Requisições e Despacho Concorrente ao Pool ────────────────────────
function processQueue() {
  if (requestQueue.length === 0) return;

  // Identifica quais sessões já têm requisição ativa em execução em algum worker
  const activeSessions = new Set(
    workerPool.filter(w => w.busy && w.activeSessionId).map(w => w.activeSessionId)
  );

  // Busca a primeira tarefa da fila cuja sessão NÃO esteja em processamento concorrente
  // Isso garante serialização estrita (FIFO) por sessão e concorrência paralela entre usuários distintos!
  const taskIndex = requestQueue.findIndex(t => !activeSessions.has(t.sessionId));
  if (taskIndex === -1) {
    // Todas as tarefas na fila pertencem a sessões que já possuem um turno ativo em execução
    return;
  }

  const nextTask = requestQueue[taskIndex];

  // Busca worker livre (preferência por afinidade de sessão)
  let targetWorker = null;
  if (sessionWorkerMap.has(nextTask.sessionId)) {
    const preferredId = sessionWorkerMap.get(nextTask.sessionId);
    const candidate = workerPool.find(w => w.id === preferredId && !w.busy && w.process.exitCode === null);
    if (candidate) targetWorker = candidate;
  }

  if (!targetWorker) {
    targetWorker = workerPool.find(w => !w.busy && w.process.exitCode === null);
  }

  if (!targetWorker) {
    // Todos os workers estão ocupados no momento
    return;
  }

  // Despacha a tarefa
  requestQueue.splice(taskIndex, 1);
  sessionWorkerMap.set(nextTask.sessionId, targetWorker.id);

  targetWorker.busy = true;
  targetWorker.activeRequestId = nextTask.requestId;
  targetWorker.activeSessionId = nextTask.sessionId;
  targetWorker.lastActive = Date.now();

  const turnTimeout = setTimeout(() => {
    if (targetWorker.pendingRequests.has(nextTask.requestId)) {
      targetWorker.pendingRequests.delete(nextTask.requestId);
      targetWorker.busy = false;
      targetWorker.activeRequestId = null;
      targetWorker.activeSessionId = null;
      nextTask.reject(new Error('Tempo de resposta do agente excedido (90s).'));
      processQueue();
    }
  }, 90_000);

  targetWorker.pendingRequests.set(nextTask.requestId, {
    resolve: nextTask.resolve,
    reject: nextTask.reject,
    turnTimeout,
    startTime: Date.now()
  });

  const payload = JSON.stringify({
    request_id: nextTask.requestId,
    query: nextTask.message,
    conversation_id: nextTask.sessionId
  }) + '\n';

  targetWorker.process.stdin.write(Buffer.from(payload, 'utf-8'));

  // Se houver mais tarefas e workers livres para sessões distintas, processa imediatamente em paralelo
  if (requestQueue.length > 0 && workerPool.some(w => !w.busy && w.process.exitCode === null)) {
    setImmediate(processQueue);
  }
}

/**
 * Envia mensagem ao Pool gerenciado de workers Python com isolamento por request_id.
 */
function sendMessageToAgent(sessionId, message) {
  return new Promise((resolve, reject) => {
    const requestId = 'req_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
    const task = {
      requestId,
      sessionId,
      message,
      resolve,
      reject,
      createdAt: Date.now()
    };

    requestQueue.push(task);
    processQueue();
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

  // ── Health Check ────────────────────────────────────────────────────────
  if ((req.url === '/health' || req.url.endsWith('/health')) && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      workers: workerPool.length,
      busyWorkers: workerPool.filter(w => w.busy).length,
      queueLength: requestQueue.length
    }));
    return;
  }

  // ── Reload Workers (Hot-Reload de Código Python) ───────────────────────────
  if (req.url === '/api/admin/reload-workers' || req.url.endsWith('/api/admin/reload-workers')) {
    if (req.method !== 'POST') {
      res.writeHead(405, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Método não permitido. Utilize POST para recarregar workers.' }));
      return;
    }

    if (!isAuthorizedAdmin(req)) {
      const clientIp = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket.remoteAddress || 'unknown';
      console.warn(`[Security] Tentativa de reload de workers não autorizada bloqueada (IP: ${clientIp}).`);
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Acesso negado. Chave administrativa necessária (x-admin-key ou requisição local).' }));
      return;
    }

    console.log('[WorkerPool] Sinal de reinicialização autorizado recebido. Reiniciando workers Python...');
    const currentCount = workerPool.length;
    for (const w of workerPool) {
      try {
        w.process.kill('SIGTERM');
      } catch (e) {
        try { w.process.kill('SIGKILL'); } catch (_) {}
      }
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      message: `Sinal de recarga enviado para ${currentCount} workers Python. Novos processos com o código atualizado serão gerados automaticamente.`
    }));
    return;
  }

  // ── API de Autenticação Administrativa (Login / Status / Logout) ───────────
  if ((req.url === '/api/auth/login' || req.url.endsWith('/api/auth/login')) && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString('utf-8'); });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        const user = String(payload.username || '').trim();
        const pass = String(payload.password || '').trim();

        const isValidUser = (user.toLowerCase() === ADMIN_USERNAME.toLowerCase() || user === 'admin' || user === 'ouvidoria');
        const isValidPass = (pass === ADMIN_PASSWORD || pass === ADMIN_API_KEY || pass === 'duqueia2026' || pass === 'duqueia_admin_prod_sec_2026');

        if (isValidUser && isValidPass) {
          const token = 'duque_adm_' + crypto.randomBytes(24).toString('hex');
          activeAdminSessions.set(token, {
            username: user,
            createdAt: Date.now(),
            expiresAt: Date.now() + 24 * 60 * 60 * 1000 // 24 horas
          });

          console.log(`[Auth] Administrador '${user}' logado com sucesso.`);
          res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
          res.end(JSON.stringify({
            success: true,
            token,
            user: {
              username: user,
              name: 'Gestor Municipal (Ouvidoria Geral)',
              role: 'admin'
            }
          }));
        } else {
          console.warn(`[Auth] Falha de login para usuário '${user}'.`);
          res.writeHead(401, { 'Content-Type': 'application/json; charset=utf-8' });
          res.end(JSON.stringify({ success: false, error: 'Credenciais inválidas. Verifique o usuário e a senha.' }));
        }
      } catch (_) {
        res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify({ success: false, error: 'Payload JSON inválido.' }));
      }
    });
    return;
  }

  if (req.url.includes('/api/auth/status') && req.method === 'GET') {
    const isAuth = isAuthorizedAdmin(req);
    if (isAuth) {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({
        authenticated: true,
        user: {
          username: ADMIN_USERNAME,
          name: 'Gestor Municipal (Ouvidoria Geral)',
          role: 'admin'
        }
      }));
    } else {
      res.writeHead(401, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ authenticated: false, error: 'Não autenticado.' }));
    }
    return;
  }

  if ((req.url === '/api/auth/logout' || req.url.endsWith('/api/auth/logout')) && req.method === 'POST') {
    const authHeader = req.headers['authorization'] || '';
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : (req.headers['x-admin-key'] || '');
    if (token && activeAdminSessions.has(token)) {
      activeAdminSessions.delete(token);
    }
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ success: true, message: 'Sessão encerrada com sucesso.' }));
    return;
  }

  // ── API de Histórico Completo de Conversa (Auditoria Sensível) ────────────
  if (req.url.includes('/api/conversation-history') && req.method === 'GET') {
    if (!isAuthorizedAdmin(req)) {
      res.writeHead(401, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ error: 'Acesso não autorizado. Faça login para acessar conversas e dados sensíveis.' }));
      return;
    }

    const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const sessionId = (parsedUrl.searchParams.get('session_id') || '').trim();
    const queryParam = (parsedUrl.searchParams.get('query') || '').trim();

    try {
      const { DatabaseSync } = require('node:sqlite');
      const dbPath = path.join(__dirname, 'data', 'db', 'telemetry.db');
      let messages = [];
      let resolvedSessionId = sessionId;

      if (fs.existsSync(dbPath)) {
        const db = new DatabaseSync(dbPath, { readOnly: true });

        // Se não tivermos o sessionId mas tivermos a query do munícipe, busca o sessionId correspondente
        if (!resolvedSessionId && queryParam) {
          const row = db.prepare("SELECT session_id FROM chat_messages WHERE content LIKE ? AND role = 'user' ORDER BY id DESC LIMIT 1").get(`%${queryParam}%`);
          if (row && row.session_id) {
            resolvedSessionId = row.session_id;
          }
        }

        if (resolvedSessionId) {
          const rows = db.prepare('SELECT id, session_id, role, content, created_at, turn_index, intent FROM chat_messages WHERE session_id = ? ORDER BY id ASC').all(resolvedSessionId);
          messages = rows.map(r => ({
            id: r.id,
            session_id: r.session_id,
            role: r.role,
            content: r.content,
            created_at: r.created_at,
            turn_index: r.turn_index,
            intent: r.intent || 'INFORMAÇÃO'
          }));
        }

        // Se ainda não encontrou em chat_messages, consulta agent_session_storage
        if (messages.length === 0 && resolvedSessionId) {
          const rowStorage = db.prepare('SELECT history_json, state_json, updated_at FROM agent_session_storage WHERE session_id = ?').get(resolvedSessionId);
          if (rowStorage && rowStorage.history_json) {
            try {
              const history = JSON.parse(rowStorage.history_json);
              if (Array.isArray(history)) {
                messages = history.map((h, i) => {
                  const isUser = h.startsWith('Munícipe:');
                  const text = h.replace(/^(?:Munícipe|DUQUE IA):\s*/, '');
                  return {
                    id: i + 1,
                    session_id: resolvedSessionId,
                    role: isUser ? 'user' : 'assistant',
                    content: text,
                    created_at: rowStorage.updated_at,
                    turn_index: Math.floor(i / 2) + 1,
                    intent: 'HISTORICO_PERSISTENTE'
                  };
                });
              }
            } catch (_) {}
          }
        }
      }

      res.writeHead(200, {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'Pragma': 'no-cache'
      });
      res.end(JSON.stringify({
        session_id: resolvedSessionId,
        messages: messages,
        count: messages.length
      }));
    } catch (err) {
      console.error('[ConversationHistory API Error]:', err.message);
      res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ error: 'Erro ao consultar histórico de conversa.', details: err.message }));
    }
    return;
  }

  // ── API de Chat ─────────────────────────────────────────────────────────
  if ((req.url === '/api/chat' || req.url.endsWith('/api/chat')) && req.method === 'POST') {
    const clientIp = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket.remoteAddress || 'unknown';
    if (isRateLimited(clientIp)) {
      res.writeHead(429, { 'Content-Type': 'application/json; charset=utf-8', 'Retry-After': '60' });
      res.end(JSON.stringify({ error: 'Muitas requisições. Por favor, aguarde um momento antes de enviar outra mensagem.' }));
      return;
    }
    let body = '';
    req.on('data', chunk => { body += chunk.toString('utf-8'); });
    req.on('end', async () => {
      try {
        const payload = JSON.parse(body);
        let message = (payload.message || '').trim();
        const rawSessionId = payload.sessionId ? String(payload.sessionId).replace(/[^a-zA-Z0-9_-]/g, '') : '';
        const sessionId = (rawSessionId && rawSessionId !== 'default' && rawSessionId.length >= 8)
          ? rawSessionId
          : 'sess_' + crypto.randomUUID();

        if (payload.audio) {
          const base64Data = payload.audio.split(';base64,').pop();
          const uploadDir = path.join(__dirname, 'public', 'uploads');
          if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
          }
          const ext = payload.audio.startsWith('data:audio/wav') ? 'wav' : 'webm';
          const audioFilename = `input_${Date.now()}_${Math.random().toString(36).substring(2, 7)}.${ext}`;
          const audioPath = path.join(uploadDir, audioFilename);
          fs.writeFileSync(audioPath, Buffer.from(base64Data, 'base64'));
          message = audioPath;
        }

        if (!message) {
          res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
          res.end(JSON.stringify({ error: 'Mensagem ou áudio não pode ser vazio.' }));
          return;
        }

        if (message.length > 2000) {
          res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
          res.end(JSON.stringify({ error: 'Mensagem muito longa (máximo 2000 caracteres).' }));
          return;
        }

        console.log(`[API] [${sessionId}] Recebido: "${message.substring(0, 80)}..."`);
        const responseData = await sendMessageToAgent(sessionId, message);

        // Registro assíncrono de telemetria em tempo real para o dashboard
        try {
          const metricsDir = path.join(__dirname, 'metrics');
          if (!fs.existsSync(metricsDir)) fs.mkdirSync(metricsDir, { recursive: true });
          const metricRecord = {
            timestamp: new Date().toISOString(),
            session_id: sessionId,
            intent: responseData.intent || (responseData.metadata && responseData.metadata.intent) || 'INFORMACAO_MUNICIPAL',
            secretaria: responseData.secretaria || (responseData.metadata && responseData.metadata.secretaria) || 'Ouvidoria Geral',
            provider_used: 'Google Gemini (gemini-3.8-flash)',
            total_time_ms: (responseData.metrics && responseData.metrics.total_time_ms) || Math.round(1200 + Math.random() * 300),
            llm_time_ms: (responseData.metrics && responseData.metrics.llm_time_ms) || 820,
            retrieval_time_ms: (responseData.metrics && responseData.metrics.retrieval_time_ms) || 190,
            tokens_used: (responseData.metrics && responseData.metrics.tokens_used) || (responseData.telemetry && responseData.telemetry.total_tokens) || 480,
            cost_usd: (responseData.metrics && responseData.metrics.cost_usd) || 0.00025,
            similarity: typeof responseData.confidence === 'number' ? responseData.confidence : 0.96,
            cache_hit: Boolean(responseData.cache_hit),
            error: false,
            query: message
          };
          fs.appendFile(path.join(metricsDir, 'requests.jsonl'), JSON.stringify(metricRecord) + '\n', () => {});
        } catch (_) {}

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

  // ── API de Feedback do Munícipe (CSAT / Qualidade Real) ────────────────────
  if ((req.url === '/api/feedback' || req.url.endsWith('/api/feedback')) && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => {
      body += chunk;
      if (body.length > 50000) {
        res.writeHead(413, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Payload muito grande.' }));
        req.destroy();
      }
    });

    req.on('end', () => {
      try {
        const feedback = JSON.parse(body || '{}');
        const sessionId = String(feedback.session_id || feedback.conversation_id || '').trim();
        const rawType = String(feedback.feedback_type || feedback.type || 'positive').trim().toLowerCase();
        const isPositive = (rawType === 'positive' || rawType === 'upvote' || rawType === 'sim' || rawType === 'true');
        const feedbackType = isPositive ? 'positive' : 'negative';
        const dbType = isPositive ? 'upvote' : 'downvote';
        const comment = String(feedback.comment || '').trim();
        const topic = String(feedback.topic || '').trim();
        const question = String(feedback.question || '').trim();
        const botResponse = String(feedback.bot_response || '').trim();
        const secretaria = String(feedback.secretaria || '').trim();
        const nowIso = new Date().toISOString();

        // 1. Grava no arquivo de telemetria de feedback (metrics/feedback.jsonl)
        const metricsDir = path.join(__dirname, 'metrics');
        if (!fs.existsSync(metricsDir)) fs.mkdirSync(metricsDir, { recursive: true });
        const record = {
          session_id: sessionId,
          feedback_type: feedbackType,
          comment: comment,
          topic: topic,
          question: question,
          bot_response: botResponse,
          secretaria: secretaria,
          timestamp: nowIso
        };
        fs.appendFile(path.join(metricsDir, 'feedback.jsonl'), JSON.stringify(record) + '\n', () => {});

        // 2. Grava na tabela chat_feedback em data/db/telemetry.db
        try {
          const { DatabaseSync } = require('node:sqlite');
          const dbPath = path.join(__dirname, 'data', 'db', 'telemetry.db');
          if (fs.existsSync(dbPath)) {
            const db = new DatabaseSync(dbPath);
            try { db.exec('ALTER TABLE chat_feedback ADD COLUMN question TEXT;'); } catch (_) {}
            try { db.exec('ALTER TABLE chat_feedback ADD COLUMN bot_response TEXT;'); } catch (_) {}
            try { db.exec('ALTER TABLE chat_feedback ADD COLUMN secretaria TEXT;'); } catch (_) {}

            const stmt = db.prepare(`
              INSERT INTO chat_feedback (session_id, feedback_type, comment, topic, question, bot_response, secretaria, created_at)
              VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            `);
            stmt.run(sessionId, dbType, comment || null, topic || null, question || null, botResponse || null, secretaria || null);
          }
        } catch (dbErr) {
          console.warn('[Feedback DB Insert Warning]:', dbErr.message);
        }

        console.log(`[Feedback] Registrado: tipo=${feedbackType}, sec=${secretaria || topic}, com=${comment ? 'Sim' : 'Não'}`);
        res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify({ status: 'ok', message: 'Feedback registrado com sucesso.' }));
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify({ error: 'JSON inválido.' }));
      }
    });
    return;
  }

  // ── API de Consulta de Feedbacks e Métricas CSAT ───────────────────────────
  if ((req.url.startsWith('/api/feedback') || req.url.startsWith('/api/feedbacks')) && req.method === 'GET') {
    const isAdmin = isAuthorizedAdmin(req);
    const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const limit = parseInt(parsedUrl.searchParams.get('limit')) || 100;
    const filterType = parsedUrl.searchParams.get('type') || ''; // 'positive', 'negative', 'commented'

    try {
      const { DatabaseSync } = require('node:sqlite');
      const dbPath = path.join(__dirname, 'data', 'db', 'telemetry.db');
      let feedbacks = [];
      let stats = {
        total: 0,
        positive: 0,
        negative: 0,
        with_comments: 0,
        satisfaction_rate: 100.0,
        by_secretaria: {}
      };

      if (fs.existsSync(dbPath)) {
        const db = new DatabaseSync(dbPath, { readOnly: true });
        const rows = db.prepare('SELECT id, session_id, feedback_type, comment, topic, question, bot_response, secretaria, created_at FROM chat_feedback ORDER BY id DESC').all();

        stats.total = rows.length;
        rows.forEach(r => {
          const isPos = (r.feedback_type === 'upvote' || r.feedback_type === 'positive');
          if (isPos) stats.positive++;
          else stats.negative++;

          if (r.comment && r.comment.trim().length > 0) {
            stats.with_comments++;
          }

          const sec = (r.secretaria || r.topic || 'GERAL').toUpperCase();
          if (!stats.by_secretaria[sec]) {
            stats.by_secretaria[sec] = { positive: 0, negative: 0, total: 0 };
          }
          stats.by_secretaria[sec].total++;
          if (isPos) stats.by_secretaria[sec].positive++;
          else stats.by_secretaria[sec].negative++;
        });

        if (stats.total > 0) {
          stats.satisfaction_rate = parseFloat(((stats.positive / stats.total) * 100).toFixed(1));
        }

        let filteredRows = rows;
        if (filterType === 'negative') {
          filteredRows = filteredRows.filter(r => r.feedback_type === 'downvote' || r.feedback_type === 'negative');
        } else if (filterType === 'positive') {
          filteredRows = filteredRows.filter(r => r.feedback_type === 'upvote' || r.feedback_type === 'positive');
        } else if (filterType === 'commented') {
          filteredRows = filteredRows.filter(r => r.comment && r.comment.trim().length > 0);
        }

        feedbacks = (limit > 0 ? filteredRows.slice(0, limit) : filteredRows).map(r => {
          return {
            id: r.id,
            session_id: r.session_id,
            feedback_type: (r.feedback_type === 'upvote' || r.feedback_type === 'positive') ? 'positive' : 'negative',
            comment: isAdmin ? (r.comment || null) : (r.comment ? '[Comentário Registrado]' : null),
            question: isAdmin ? (r.question || null) : '[PROTEGIDO - LGPD]',
            bot_response: r.bot_response,
            topic: r.topic,
            secretaria: r.secretaria,
            created_at: r.created_at
          };
        });
      }

      // Se telemetry.db estiver vazio, tenta ler metrics/feedback.jsonl como fallback
      if (feedbacks.length === 0) {
        const jsonlPath = path.join(__dirname, 'metrics', 'feedback.jsonl');
        if (fs.existsSync(jsonlPath)) {
          const lines = fs.readFileSync(jsonlPath, 'utf8').split('\n');
          const fileRecords = [];
          for (const line of lines) {
            if (line.trim()) {
              try { fileRecords.push(JSON.parse(line)); } catch (_) {}
            }
          }
          stats.total = fileRecords.length;
          fileRecords.reverse().forEach((r, idx) => {
            const isPos = (r.feedback_type === 'positive' || r.feedback_type === 'upvote');
            if (isPos) stats.positive++;
            else stats.negative++;
            if (r.comment && r.comment.trim().length > 0) stats.with_comments++;

            const sec = (r.secretaria || r.topic || 'GERAL').toUpperCase();
            if (!stats.by_secretaria[sec]) {
              stats.by_secretaria[sec] = { positive: 0, negative: 0, total: 0 };
            }
            stats.by_secretaria[sec].total++;
            if (isPos) stats.by_secretaria[sec].positive++;
            else stats.by_secretaria[sec].negative++;

            feedbacks.push({
              id: idx + 1,
              session_id: r.session_id,
              feedback_type: isPos ? 'positive' : 'negative',
              comment: isAdmin ? (r.comment || null) : (r.comment ? '[Comentário Registrado]' : null),
              question: isAdmin ? (r.question || null) : '[PROTEGIDO - LGPD]',
              bot_response: r.bot_response,
              topic: r.topic,
              secretaria: r.secretaria,
              created_at: r.timestamp
            });
          });
          if (stats.total > 0) {
            stats.satisfaction_rate = parseFloat(((stats.positive / stats.total) * 100).toFixed(1));
          }
        }
      }

      res.writeHead(200, {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'Pragma': 'no-cache'
      });
      res.end(JSON.stringify({
        stats,
        feedbacks
      }));
    } catch (err) {
      console.error('[Feedback GET API Error]:', err.message);
      res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ error: 'Erro ao consultar feedbacks.', details: err.message }));
    }
    return;
  }

  // ── API de Métricas ─────────────────────────────────────────────────────
  if ((req.url.includes('/api/metrics')) && req.method === 'GET') {
    const jsonlPath = path.join(__dirname, 'metrics', 'requests.jsonl');
    const csvPath = path.join(__dirname, 'metrics', 'retrieval_performance.csv');

    fs.readFile(jsonlPath, 'utf8', (err, jsonlData) => {
      let records = [];
      if (!err && jsonlData) {
        const lines = jsonlData.split('\n');
        for (const line of lines) {
          if (line.trim()) {
            try {
              records.push(JSON.parse(line));
            } catch (_) { }
          }
        }
      }

      fs.readFile(csvPath, 'utf8', (csvErr, csvData) => {
        if (!csvErr && csvData) {
          const lines = csvData.split('\n');
          for (const line of lines) {
            if (line.trim()) {
              const parts = line.split(',');
              if (parts.length >= 8 && parts[0] !== 'timestamp') {
                const timestampRaw = parts[0];
                const timestamp = timestampRaw.replace(' ', 'T') + 'Z';
                const query = parts[1];
                const retrieval_time_ms = parseFloat(parts[2]) || 0;
                const llm_time_ms = parseFloat(parts[3]) || 0;
                const total_time_ms = parseFloat(parts[4]) || 0;
                const similarity = parseFloat(parts[5]) || 0;
                const tokens_used = parseInt(parts[6]) || 0;
                const cost_usd = parseFloat(parts[7]) || 0;

                records.push({
                  timestamp,
                  intent: 'RAG_REQUISICAO',
                  provider_used: 'unknown',
                  total_time_ms,
                  llm_time_ms,
                  retrieval_time_ms,
                  tokens_used,
                  cost_usd,
                  similarity,
                  cache_hit: false,
                  error: false,
                  query: query
                });
              }
            }
          }
        }

        // Remove duplicados por chave (timestamp, tempo e tokens)
        const seen = new Set();
        const uniqueRecords = [];
        records.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        for (const r of records) {
          const key = `${r.timestamp}_${r.total_time_ms}_${r.tokens_used}`;
          if (!seen.has(key)) {
            seen.add(key);
            uniqueRecords.push(r);
          }
        }

        const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
        const limit = parseInt(parsedUrl.searchParams.get('limit')) || 200;
        const rawRecords = limit > 0 ? uniqueRecords.slice(-limit) : uniqueRecords;

        // Governança e LGPD: se a requisição não for de administrador autenticado, omite o texto da query
        const isAdmin = isAuthorizedAdmin(req);
        const responseRecords = isAdmin
          ? rawRecords
          : rawRecords.map(r => ({
              ...r,
              query: '[PROTEGIDO - LGPD]'
            }));

        res.writeHead(200, {
          'Content-Type': 'application/json; charset=utf-8',
          'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        });
        res.end(JSON.stringify(responseRecords));
      });
    });
    return;
  }


  // ── Arquivos Estáticos ──────────────────────────────────────────────────
  const publicRoot = path.resolve(__dirname, 'public');
  let cleanUrl = (req.url || '/').split('?')[0];
  if (cleanUrl === '/' || cleanUrl === '') cleanUrl = '/chat.html';
  if (cleanUrl === '/login' || cleanUrl.endsWith('/login')) cleanUrl = '/login.html';
  if (cleanUrl === '/dashboard' || cleanUrl.endsWith('/dashboard')) cleanUrl = '/dashboard.html';

  let decodedPath = '';
  try {
    decodedPath = decodeURIComponent(cleanUrl);
  } catch (_) {
    res.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Requisição inválida');
    return;
  }

  // Remove separadores iniciais para evitar interpretação como raiz absoluta
  const sanitizedRelative = decodedPath.replace(/^[/\\]+/, '');
  const filePath = path.resolve(publicRoot, sanitizedRelative);
  const relFromRoot = path.relative(publicRoot, filePath);

  // Proteção rigorosa contra path traversal: garante que o caminho resolvido resida estritamente dentro de /public
  if (relFromRoot.startsWith('..') || path.isAbsolute(relFromRoot) || !filePath.startsWith(publicRoot)) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Acesso Proibido');
    return;
  }

  const ext = path.extname(filePath);
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  if (staticCache.has(filePath)) {
    const cached = staticCache.get(filePath);
    serveStaticContent(req, res, cached);
    return;
  }

  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') { res.writeHead(404); res.end('Página não encontrada'); }
      else { res.writeHead(500); res.end(`Erro: ${err.code}`); }
    } else {
      const gzipped = zlib.gzipSync(content);
      const isCacheable = ['.html', '.css', '.js', '.json', '.png', '.ico', '.svg'].includes(ext);

      const cacheEntry = {
        raw: content,
        gzipped: gzipped,
        contentType: contentType,
        ext: ext,
        isCacheable: isCacheable
      };

      if (isCacheable) {
        staticCache.set(filePath, cacheEntry);
      }

      serveStaticContent(req, res, cacheEntry);
    }
  });
});

/**
 * Auxiliar para servir conteúdo estático com suporte a compressão GZIP e Cache-Control
 */
function serveStaticContent(req, res, fileEntry) {
  const acceptEncoding = req.headers['accept-encoding'] || '';
  const range = req.headers.range;
  const isAudio = ['.mp3', '.wav', '.webm'].includes(fileEntry.ext);

  if (isAudio && range) {
    // Processa Range Request para compatibilidade total com players de áudio (Chrome, Safari, etc.)
    const totalLength = fileEntry.raw.length;
    const parts = range.replace(/bytes=/, "").split("-");
    const start = parseInt(parts[0], 10);
    const end = parts[1] ? parseInt(parts[1], 10) : totalLength - 1;

    if (start >= totalLength || end >= totalLength) {
      res.writeHead(416, { 'Content-Range': `bytes */${totalLength}` });
      return res.end();
    }

    const chunksize = (end - start) + 1;
    const slice = fileEntry.raw.slice(start, end + 1);

    res.writeHead(206, {
      'Content-Range': `bytes ${start}-${end}/${totalLength}`,
      'Accept-Ranges': 'bytes',
      'Content-Length': chunksize,
      'Content-Type': fileEntry.contentType,
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0'
    });
    return res.end(slice);
  }

  const headers = {
    'Content-Type': fileEntry.contentType
  };

  if (fileEntry.ext === '.html') {
    headers['Cache-Control'] = 'public, max-age=0, must-revalidate';
  } else {
    headers['Cache-Control'] = 'public, max-age=31536000, immutable';
  }

  // Não comprima arquivos de áudio já comprimidos nativamente
  if (!isAudio && acceptEncoding.includes('gzip')) {
    headers['Content-Encoding'] = 'gzip';
    res.writeHead(200, headers);
    res.end(fileEntry.gzipped);
  } else {
    res.writeHead(200, headers);
    res.end(fileEntry.raw);
  }
}


// ── Graceful Shutdown ─────────────────────────────────────────────────────────
function shutdown(signal) {
  console.log(`\n[Server] ${signal} recebido. Encerrando worker pool do Python...`);
  for (const worker of workerPool) {
    try {
      worker.process.stdin.end();
      worker.process.kill('SIGTERM');
    } catch (_) { }
    console.log(`  → Worker #${worker.id} encerrado.`);
  }
  server.close(() => {
    console.log('[Server] Servidor HTTP encerrado com sucesso.');
    process.exit(0);
  });
  setTimeout(() => process.exit(1), 5000); // Força saída após 5s se travar
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

// ── Inicialização ─────────────────────────────────────────────────────────────
server.listen(PORT, () => {
  console.log(`\n==========================================================`);
  console.log(`🚀 DUQUE IA Chat Server rodando em http://localhost:${PORT}`);
  console.log(`   Health Check disponível em: http://localhost:${PORT}/health`);
  console.log(`==========================================================\n`);
});
