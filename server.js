const { spawn } = require('child_process');
const http = require('http');
const path = require('path');
const fs = require('fs');

const PORT = 3000;
const PYTHON_PATH = 'python'; // Usa o executável python padrão do sistema
const AGENT_PATH = path.join(__dirname, 'agent', 'main.py');

// Cache de agentes instanciados por sessão
const activeSessions = new Map();

/**
 * Cria ou retorna uma instância persistente do script Python para uma sessão do usuário
 */
function getOrCreateAgentInstance(sessionId) {
  if (activeSessions.has(sessionId)) {
    return activeSessions.get(sessionId);
  }

  console.log(`[Server] Criando nova instância do agente para a sessão: ${sessionId}`);

  // Inicia o processo Python com a flag -u (unbuffered output) para evitar atrasos de buffer
  const pyProcess = spawn(PYTHON_PATH, ['-u', AGENT_PATH], {
    cwd: __dirname,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
  });

  const sessionObj = {
    process: pyProcess,
    queue: [],
    currentResolve: null,
    currentReject: null,
    buffer: ''
  };

  // Trata saída do stdout do agente Python
  pyProcess.stdout.on('data', (data) => {
    const chunk = data.toString('utf-8');
    sessionObj.buffer += chunk;
    
    console.log(`[Python Debug stdout]: ${chunk}`);

    // Tentamos processar as linhas do buffer
    processBuffer(sessionObj);
  });

  // Trata erros vindos do stderr do agente Python
  pyProcess.stderr.on('data', (data) => {
    console.error(`[Python stderr - ${sessionId}]:`, data.toString('utf-8'));
  });

  // Trata encerramento do processo
  pyProcess.on('close', (code) => {
    console.log(`[Server] Processo do agente para a sessão ${sessionId} encerrou com código ${code}`);
    activeSessions.delete(sessionId);
    if (sessionObj.currentReject) {
      sessionObj.currentReject(new Error('Processo do agente encerrou inesperadamente.'));
    }
  });

  activeSessions.set(sessionId, sessionObj);
  return sessionObj;
}

/**
 * Tenta processar o buffer da sessão procurando por respostas JSON completas
 */
function processBuffer(session) {
  // O agente principal do Duque IA retorna a saída em formato JSON
  // Procuremos por chaves fechadas contendo campos conhecidos de resposta
  // Como estamos rodando no CLI interativo do main.py modificado, o JSON é impresso
  // diretamente quando rodamos. No entanto, o main.py interativo lê do stdin linha por linha
  // e imprime a resposta humanizada por padrão, ou JSON se habilitado.
  // Para tornar a comunicação 100% robusta via API sem mexer no main.py interativo,
  // vamos extrair o bloco de JSON que o agente imprime a cada turno de conversação.
  
  // Vamos buscar por padrões de JSON impressos
  // Como o main.py imprime o JSON quando usamos respond() ou se tiver habilitado,
  // vamos habilitar o modo JSON no start enviando o comando 'json\n' no primeiro turno.
  // Outra forma é ler a saída humanizada. Mas ler o JSON estruturado é excelente porque traz
  // inclusive metadados (intenção, confiança, fontes).
  
  const text = session.buffer;
  
  // Vamos buscar por padrões estruturados de JSON: { ... }
  // Procuramos o primeiro '{' e tentamos casar com o seu correspondente '}'
  let startIdx = text.indexOf('{');
  if (startIdx !== -1) {
    let braceCount = 0;
    let endIdx = -1;
    for (let i = startIdx; i < text.length; i++) {
      if (text[i] === '{') braceCount++;
      else if (text[i] === '}') {
        braceCount--;
        if (braceCount === 0) {
          endIdx = i;
          break;
        }
      }
    }

    if (endIdx !== -1) {
      const jsonCandidate = text.substring(startIdx, endIdx + 1);
      session.buffer = text.substring(endIdx + 1); // Limpa o buffer até onde lemos

      try {
        const parsed = JSON.parse(jsonCandidate);
        if (session.currentResolve) {
          session.currentResolve(parsed);
          session.currentResolve = null;
          session.currentReject = null;
        }
      } catch (err) {
        // Se falhou ao parsear (JSON incompleto ou inválido), removemos o '{' inicial e tentamos novamente no próximo chunk
        session.buffer = text.substring(startIdx + 1);
        processBuffer(session);
      }
    }
  }
}

/**
 * Envia uma mensagem para o agente Python associado à sessão e espera pela resposta
 */
function sendMessageToAgent(sessionId, message) {
  return new Promise((resolve, reject) => {
    const session = getOrCreateAgentInstance(sessionId);

    // Se já existe uma requisição ativa esperando resposta, rejeita para evitar conflitos
    if (session.currentResolve) {
      return reject(new Error('Já existe uma requisição pendente para esta sessão. Aguarde.'));
    }

    session.currentResolve = resolve;
    session.currentReject = reject;

    // O main.py detecta automaticamente modo pipe via sys.stdin.isatty()
    // e já inicia em modo JSON por padrão — não é necessário enviar 'json\n'.
    if (!session.initialized) {
      session.initialized = true;
      session.process.stdin.write(`${message}\n`);
    } else {
      session.process.stdin.write(`${message}\n`);
    }
  });
}

// Servidor HTTP simples
const server = http.createServer((req, res) => {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Rota API para envio de mensagens
  if (req.url === '/api/chat' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });

    req.on('end', async () => {
      try {
        const { message, sessionId = 'default' } = JSON.parse(body);

        if (!message) {
          res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
          res.end(JSON.stringify({ error: 'Mensagem vazia' }));
          return;
        }

        console.log(`[API] Recebido: "${message}" para sessão ${sessionId}`);
        const responseData = await sendMessageToAgent(sessionId, message);

        res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify(responseData));
      } catch (err) {
        console.error('[API Error]:', err);
        res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify({ error: err.message || 'Erro interno do servidor' }));
      }
    });
    return;
  }

  // Roteia arquivos estáticos da página de chat
  let filePath = path.join(__dirname, 'public', req.url === '/' ? 'chat.html' : req.url);
  
  // Garante que não acessem arquivos fora da pasta pública por segurança
  if (!filePath.startsWith(path.join(__dirname, 'public'))) {
    res.writeHead(403);
    res.end('Acesso Proibido');
    return;
  }

  const extname = path.extname(filePath);
  let contentType = 'text/html';
  if (extname === '.css') contentType = 'text/css';
  if (extname === '.js') contentType = 'application/javascript';
  if (extname === '.json') contentType = 'application/json';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        res.writeHead(404);
        res.end('Página não encontrada');
      } else {
        res.writeHead(500);
        res.end(`Erro no servidor: ${err.code}`);
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
    }
  });
});

server.listen(PORT, () => {
  console.log(`\n==========================================================`);
  console.log(`🚀 DUQUE IA Chat Server rodando em http://localhost:${PORT}`);
  console.log(`==========================================================\n`);
});
