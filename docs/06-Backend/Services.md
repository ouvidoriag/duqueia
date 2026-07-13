# Services do Backend — Duque IA

A principal classe e responsabilidade do `server.js` é gerenciar a inicialização e comunicação IPC (Inter-Process Communication) com o agente Python.

## Spawner do Subprocesso
Para cada nova sessão (`sessionId`), o Node cria um processo isolado rodando o script `agent/main.py`:
```javascript
const pyProcess = spawn('python', ['-u', 'agent/main.py'], { ... });
```
A flag `-u` obriga o interpretador Python a rodar em modo não-bufferizado, garantindo que as respostas sejam enviadas imediatamente ao stdout ao término de cada execução.

---
[Avançar: Middlewares](Middlewares.md) | [Voltar: Controllers](Controllers.md)
