const { spawn } = require('child_process');
const http = require('http');
const path = require('path');
const fs = require('fs');
const zlib = require('zlib');

// Cache para arquivos estáticos: Map<filePath, { raw: Buffer, gzipped: Buffer, contentType: string, ext: string, isCacheable: boolean }>
const staticCache = new Map();


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
  '.mp3':  'audio/mpeg',
  '.webm': 'audio/webm',
  '.wav':  'audio/wav',
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
        let message = (payload.message || '').trim();
        const sessionId = (payload.sessionId || 'default').replace(/[^a-zA-Z0-9_-]/g, '');

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

  // ── API de Métricas ─────────────────────────────────────────────────────
  if (req.url.startsWith('/api/metrics') && req.method === 'GET') {
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
            } catch (_) {}
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
        const responseRecords = limit > 0 ? uniqueRecords.slice(-limit) : uniqueRecords;
        
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
