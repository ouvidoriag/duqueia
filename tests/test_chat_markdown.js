// Teste de regressão do renderizador Markdown do chat (public/chat.html -> formatMarkdown).
// Execução: node tests/test_chat_markdown.js
const fs = require('fs');
const path = require('path');
const assert = require('assert');

const html = fs.readFileSync(process.env.CHAT_HTML || path.join(__dirname, '..', 'public', 'chat.html'), 'utf8');
const start = html.indexOf('function formatMarkdown(text) {');
const end = html.indexOf('function nowTime() {');
assert(start > 0 && end > start, 'formatMarkdown não encontrada em chat.html');
const formatMarkdown = new Function(html.slice(start, end) + '\nreturn formatMarkdown;')();

const cases = [];
const t = (name, fn) => cases.push([name, fn]);

t('link markdown vira <a> clicável', () => {
  const out = formatMarkdown('[Abrir solicitação no Colab](https://duquedecaxias.colab.re)');
  assert(out.includes('<a href="https://duquedecaxias.colab.re"'), out);
  assert(!out.includes(']('), 'sintaxe markdown vazou: ' + out);
});

t('URL solta vira link e não engole pontuação final', () => {
  const out = formatMarkdown('Acesse https://duquedecaxias.colab.re.');
  assert(out.includes('href="https://duquedecaxias.colab.re"'), out);
});

t('javascript: nunca vira link', () => {
  const out = formatMarkdown('[x](javascript:alert(1))');
  assert(!out.includes('<a '), out);
});

t('HTML do usuário/IA é escapado', () => {
  const out = formatMarkdown('<img src=x onerror=alert(1)> **ok**');
  assert(!out.includes('<img'), out);
  assert(out.includes('<strong>ok</strong>'), out);
});

t('lista ordenada vira <ol>', () => {
  const out = formatMarkdown('Passos:\n1. Acesse o app\n2. Escolha o tema\n3. Envie');
  assert(out.includes('<ol>') && (out.match(/<li>/g) || []).length === 3, out);
});

t('lista com marcador * e negrito não gera <em> quebrado', () => {
  const out = formatMarkdown('* **Órgão Responsável:** SMTSP\n* **Prazo:** 30 dias\n\n*Atenção:* confirme no canal oficial.');
  assert((out.match(/<li>/g) || []).length === 2, out);
  assert(out.includes('<em>Atenção:</em>'), out);
  assert(!/<li>\s*<em>/.test(out), 'marcador de lista virou itálico: ' + out);
});

t('lista aninhada dentro de item', () => {
  const out = formatMarkdown('* **Como Solicitar:**\n  1. Abra o Colab\n  2. Selecione Zeladoria\n* **Prazo:** 30 dias');
  assert(out.includes('<ul>') && out.includes('<ol>'), out);
  assert((out.match(/<ol>/g) || []).length === 1 && (out.match(/<\/ol>/g) || []).length === 1, out);
  assert((out.match(/<ul>/g) || []).length === (out.match(/<\/ul>/g) || []).length, 'tags ul desbalanceadas: ' + out);
});

t('nota final em itálico com negrito interno e telefone', () => {
  const out = formatMarkdown('*(A **Ouvidoria Geral** — telefone **(21) 2652-3835** — deve ser acionada.)*');
  assert(out.includes('<strong>Ouvidoria Geral</strong>'), out);
  assert(out.includes('tel:2126523835'), out);
});

t('lista após parágrafo sem linha em branco', () => {
  const out = formatMarkdown('Você precisa de:\n- RG\n- CPF');
  assert(out.includes('<p>Você precisa de:</p>') && out.includes('<ul>'), out);
});

let failed = 0;
for (const [name, fn] of cases) {
  try { fn(); console.log('  ok  -', name); }
  catch (e) { failed++; console.log('FALHA -', name, '\n      ', String(e.message).slice(0, 300)); }
}
console.log(failed ? `\n${failed} falha(s) de ${cases.length}` : `\nTodos os ${cases.length} testes do renderizador passaram`);
process.exit(failed ? 1 : 0);
