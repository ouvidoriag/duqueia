"""
graph.py — Duque IA  (LangGraph Lite)
======================================
Grafo de estados interno em Python puro — sem dependências externas.

Arquitetura:
  START
    │
    ▼
  fast_gate ──blocked──► security     ──► END
    │
    │ cleared
    ▼
  triage ──► (roteamento por next_agent)
    │
    ├── SECURITY_HANDLER           ──► END
    ├── CONVERSATION_HANDLER       ──► END
    ├── COLLECTOR_HANDLER          ──► END
    ├── AMBIGUITY_HANDLER          ──► END
    ├── PRIVATE_RESPONSIBILITY     ──► END
    ├── PROGRAMACAO_HANDLER        ──► END
    └── RAG_HANDLER                ──► END

Cada nó recebe e retorna um AgentState, que é imutável entre nós (passado por cópia).
Retry granular: cada nó pode indicar on_error_next para desvio seguro em caso de falha.
"""

from __future__ import annotations

import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@dataclass
class AgentState:
    """Estado compartilhado entre os nós do grafo."""
    # Entrada
    query: str = ""
    conversation_id: str = ""
    history: list = field(default_factory=list)

    # Triagem
    triage_info: dict = field(default_factory=dict)
    next_node: str = "triage"

    # Saída
    response: dict = field(default_factory=dict)

    # Metadados de execução (auditoria)
    nodes_executed: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    def with_update(self, **kwargs) -> "AgentState":
        """Retorna uma cópia do estado com campos atualizados."""
        import copy
        new_state = copy.copy(self)
        for k, v in kwargs.items():
            setattr(new_state, k, v)
        return new_state

    def record_node(self, name: str):
        self.nodes_executed.append({"node": name, "at": round(time.time() - self.start_time, 4)})

    def record_error(self, node: str, exc: Exception):
        self.errors.append({"node": node, "error": str(exc), "at": round(time.time() - self.start_time, 4)})


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

@dataclass
class Node:
    """Nó do grafo: unidade de execução atômica."""
    name: str
    fn: Callable[[AgentState, Any], AgentState]
    on_error_next: Optional[str] = None  # nó de fallback se este falhar

    def run(self, state: AgentState, ctx: Any) -> AgentState:
        t0 = time.time()
        state.record_node(self.name)
        try:
            res = self.fn(state, ctx)
            elapsed = round((time.time() - t0) * 1000, 2)
            if state.nodes_executed:
                state.nodes_executed[-1]["duration_ms"] = elapsed
            return res
        except Exception as exc:
            state.record_error(self.name, exc)
            print(f"[Graph Error] Nó '{self.name}' falhou: {exc}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            if self.on_error_next:
                return state.with_update(next_node=self.on_error_next)
            return state


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class AgentGraph:
    """
    Orquestra os nós de acordo com state.next_node.
    Cada nó deve definir state.next_node = "END" para encerrar o loop.
    """

    def __init__(self):
        self._nodes: dict[str, Node] = {}
        self._entry: Optional[str] = None

    def add_node(self, node: Node):
        self._nodes[node.name] = node

    def set_entry(self, name: str):
        self._entry = name

    def run(self, state: AgentState, ctx: Any = None, max_steps: int = 20) -> AgentState:
        """Executa o grafo a partir do nó de entrada até o estado END."""
        if self._entry:
            state = state.with_update(next_node=self._entry)

        steps = 0
        while state.next_node != "END" and steps < max_steps:
            node_name = state.next_node
            node = self._nodes.get(node_name)
            if not node:
                print(f"[Graph Warning] Nó '{node_name}' não encontrado. Encerrando.", file=sys.stderr)
                break
            state = node.run(state, ctx)
            steps += 1

        return state


# ---------------------------------------------------------------------------
# Context passed to every node
# ---------------------------------------------------------------------------

@dataclass
class GraphContext:
    """Contexto compartilhado entre todos os nós (agente, configurações)."""
    agent: Any          # DuqueIAAgent
    db_path: str = ""


# ---------------------------------------------------------------------------
# Node Implementations
# ---------------------------------------------------------------------------

def node_fast_gate(state: AgentState, ctx: GraphContext) -> AgentState:
    """Camada 0: verifica regras de segurança locais sem LLM."""
    from agent.triage import check_fast_gate, _add_routing_metadata

    result = check_fast_gate(state.query)
    if result:
        triage = _add_routing_metadata(result)
        next_node = triage.get("next_agent", "RAG_HANDLER")
        return state.with_update(
            triage_info=triage,
            next_node=next_node
        )
    # Nenhuma regra disparou — vai para triagem LLM
    return state.with_update(next_node="triage")


def node_triage(state: AgentState, ctx: GraphContext) -> AgentState:
    """Camada 1-2: Cache SQLite ou Classificador LLM."""
    from agent.triage import perform_triage

    triage = perform_triage(
        db_path=ctx.agent.db_cache,
        query=state.query,
        gemini_client=ctx.agent.gemini_client,
        history=state.history
    )
    # Sempre passa pelo tool router após a triagem para enriquecer o contexto
    return state.with_update(
        triage_info=triage,
        next_node="tool_router"
    )

def node_tool_router(state: AgentState, ctx: GraphContext) -> AgentState:
    """Camada 2.5: Roteador de Ferramentas (Tool Router)."""
    try:
        from agent.tool_router import ToolRouter
        intent = state.triage_info.get("intent", "")
        tools = ToolRouter.select_tools(intent, [state.query])
        
        # Enriquecendo o triage_info com as ferramentas selecionadas
        new_triage = dict(state.triage_info)
        new_triage["tools_selected"] = tools
        
        # Agora sim segue para o handler que a triagem originalmente definiu
        next_node = new_triage.get("next_agent", "RAG_HANDLER")
        return state.with_update(triage_info=new_triage, next_node=next_node)
    except Exception as e:
        import sys
        print(f"[Graph ToolRouter Warning] {e}", file=sys.stderr)
        next_node = state.triage_info.get("next_agent", "RAG_HANDLER")
        return state.with_update(next_node=next_node)




def _run_handler(state: AgentState, ctx: GraphContext, handler_key: str) -> AgentState:
    """Utilitário: delega ao handler registrado no agente e encerra o grafo."""
    handler = ctx.agent.handlers.get(handler_key)
    if not handler:
        print(f"[Graph Warning] Handler '{handler_key}' não encontrado, usando RAG_HANDLER.", file=sys.stderr)
        handler = ctx.agent.handlers.get("RAG_HANDLER")

    result = handler.execute(
        query=state.query,
        triage_info=state.triage_info,
        agent=ctx.agent,
        conversation_id=state.conversation_id,
        start_time=state.start_time,
        history=state.history
    )
    # Injeta metadados do grafo na resposta
    result["_graph"] = {
        "nodes_executed": state.nodes_executed,
        "errors": state.errors,
        "steps": len(state.nodes_executed)
    }
    return state.with_update(response=result, next_node="END")


def node_security(state: AgentState, ctx: GraphContext) -> AgentState:
    return _run_handler(state, ctx, "SECURITY_HANDLER")


def node_conversation(state: AgentState, ctx: GraphContext) -> AgentState:
    return _run_handler(state, ctx, "CONVERSATION_HANDLER")


def node_collector(state: AgentState, ctx: GraphContext) -> AgentState:
    return _run_handler(state, ctx, "COLLECTOR_HANDLER")


def node_ambiguity(state: AgentState, ctx: GraphContext) -> AgentState:
    return _run_handler(state, ctx, "AMBIGUITY_HANDLER")


def node_private(state: AgentState, ctx: GraphContext) -> AgentState:
    return _run_handler(state, ctx, "PRIVATE_RESPONSIBILITY_HANDLER")


def node_programacao(state: AgentState, ctx: GraphContext) -> AgentState:
    return _run_handler(state, ctx, "PROGRAMACAO_HANDLER")


def node_rag(state: AgentState, ctx: GraphContext) -> AgentState:
    return _run_handler(state, ctx, "RAG_HANDLER")


def node_authority(state: AgentState, ctx: GraphContext) -> AgentState:
    return _run_handler(state, ctx, "AUTHORITY_HANDLER")


# ---------------------------------------------------------------------------
# Factory: build the default Duque IA graph
# ---------------------------------------------------------------------------

def build_duque_ia_graph() -> AgentGraph:
    """
    Constrói e retorna o grafo completo do Duque IA.
    A ordem dos nós reflete o fluxo declarado na arquitetura.
    """
    graph = AgentGraph()

    # Nós de controle de fluxo
    graph.add_node(Node("fast_gate",    node_fast_gate,    on_error_next="triage"))
    graph.add_node(Node("triage",       node_triage,       on_error_next="tool_router"))
    graph.add_node(Node("tool_router",  node_tool_router,  on_error_next="RAG_HANDLER"))

    # Nós de resposta (terminais — definem next_node="END")
    graph.add_node(Node("SECURITY_HANDLER",              node_security,      on_error_next="END"))
    graph.add_node(Node("CONVERSATION_HANDLER",          node_conversation,  on_error_next="END"))
    graph.add_node(Node("COLLECTOR_HANDLER",             node_collector,     on_error_next="END"))
    graph.add_node(Node("AMBIGUITY_HANDLER",             node_ambiguity,     on_error_next="END"))
    graph.add_node(Node("PRIVATE_RESPONSIBILITY_HANDLER", node_private,      on_error_next="END"))
    graph.add_node(Node("PROGRAMACAO_HANDLER",           node_programacao,   on_error_next="END"))
    graph.add_node(Node("RAG_HANDLER",                   node_rag,           on_error_next="END"))
    graph.add_node(Node("AUTHORITY_HANDLER",             node_authority,     on_error_next="END"))

    graph.set_entry("fast_gate")
    return graph


# ---------------------------------------------------------------------------
# Public API: convenience function
# ---------------------------------------------------------------------------

def run_graph(query: str, conversation_id: str, history: list, agent) -> dict:
    """
    Executa o grafo do Duque IA e retorna a resposta final.

    Args:
        query:           Mensagem do munícipe.
        conversation_id: ID da sessão de conversa.
        history:         Histórico de mensagens anteriores.
        agent:           Instância de DuqueIAAgent.

    Returns:
        dict com campos: answer, sources, confidence, intent_detected, triage_info,
                         metrics, _graph (metadados de auditoria do grafo).
    """
    graph = build_duque_ia_graph()
    ctx = GraphContext(agent=agent, db_path=agent.db_path)
    initial_state = AgentState(
        query=query,
        conversation_id=conversation_id,
        history=history,
        start_time=time.time()
    )
    final_state = graph.run(initial_state, ctx=ctx)
    
    # Grava métricas de observabilidade de forma assíncrona/segura
    try:
        from metrics.collector import MetricsCollector
        MetricsCollector.record(final_state)
    except Exception as e:
        import sys
        print(f"[Graph Metrics Warning] Erro ao gravar métricas: {e}", file=sys.stderr)
        
    return final_state.response
