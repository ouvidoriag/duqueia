# ==============================================================================
#                      DUQUE IA - RAG FRAMEWORK MAKEFILE
# ==============================================================================
# Este Makefile automatiza o fluxo de processamento de documentos, geração
# de embeddings, testes de recuperação e execução de guardrails.
#
# Fontes de Ingestão Suportadas:
#   - PDFs (data/raw/raw_pdf_files/) e Markdown (data/knowledge/)
#   - Tabelas CSV (data/raw/raw_csv_files/)
#   - Planilhas Excel (data/raw/raw_excel_files/)
#   - Links da Web / Sites (data/raw/raw_web_urls/)
# ==============================================================================

.PHONY: help setup parse_pdfs parse_csv parse_excel parse_web parse_carta_servico parse_oficios parse_all embed test_retrieval run_agent clean test_suite test_30

# Exibe o menu de ajuda com os comandos disponíveis e descrições dos scripts
help:
	@echo "=============================================================================="
	@echo "                      Comandos Disponíveis no DUQUE IA"
	@echo "make setup              - Executa bootstrap de inicialização do banco SQLite local"
	@echo "make parse_pdfs         - Extrai textos de PDFs reais e importa para JSON"
	@echo "make parse_assuntos     - Ingere mapeamento de assuntos por secretaria (Colab)"
	@echo "make parse_carta_servico- Ingere Carta de Serviços Municipal em Excel"
	@echo "make sync_excel         - Sincroniza planilha Excel atualizada para serviços estruturados"
	@echo "make parse_web          - Executa raspagem de sites a partir de data/raw/raw_web_urls/urls.txt"
	@echo "make parse_oficios      - Ingere PDFs de ofícios municipais via OCR"
	@echo "make parse_all          - Executa todos os parsers listados acima sequencialmente"
	@echo "make embed              - Roda o pipeline de chunking e gravacao no banco SQLite"
	@echo "make test_retrieval     - Roda os testes de metricas de recuperacao (Precision/Recall)"
	@echo "make test_suite         - Executa todos os testes de integração e unitários do projeto"
	@echo "make test_30            - Roda o benchmark de 30 perguntas simulando munícipes"
	@echo "make test_ask           - Modo interativo de perguntas ao agente"
	@echo "make run_agent          - Inicializa o agente interativo de Duque de Caxias"
	@echo "make clean              - Limpa arquivos JSON estruturados temporarios"
	@echo "=============================================================================="

# Cria as tabelas e índices no banco de dados local SQLite
setup:
	python -c "from bootstrap.database_init import setup_database; setup_database()"

# Ingestão de PDFs e Markdown
parse_pdfs:
	python ingestion/parser/parse_pdfs.py

# Ingestão de mapeamento de Assuntos por Secretaria (Colab)
parse_assuntos:
	python ingestion/parser/parse_assuntos.py

# Ingere a Carta de Servicos Municipal (Excel)
parse_carta_servico:
	python ingestion/parser/parse_carta_servico.py

# Sincroniza planilha Excel atualizada para JSONs estruturados
sync_excel:
	python ingestion/parser/sync_updated_excel.py

# Ingestão de URLs da internet
parse_web:
	python ingestion/parser/parse_web.py

# Ingere os PDFs de Oficios (OCR via Gemini Vision)
parse_oficios:
	python ingestion/parser/parse_oficios_ocr.py

# Executa todas as ingestoes e gera a base consolidada de JSONs
parse_all: parse_pdfs parse_assuntos parse_carta_servico sync_excel parse_web parse_oficios
	@echo "[Pipeline] Todos os parsers foram executados com sucesso!"

# Modo interativo de testes rapidos
test_ask:
	python scripts/tests/test_ask.py

# Divide os textos processados de acordo com as estratégias e envia para o Vector DB
embed:
	python ingestion/embed/main.py --config ingestion/embed/embed_config.yml

# Executa testes de relevância de recuperação com base nas métricas
test_retrieval:
	python scripts/tests/test_retrieval_relevance.py

# Inicia a execução principal do Agente para atendimento aos munícipes
run_agent:
	python agent/main.py

# Inicializa o ambiente, banco de dados e roda o servidor em 1 clique
run:
	python setup_and_run.py

# Remove os arquivos JSON gerados no processo de parsing de PDFs e outros formatos
clean:
	python -c "import os, shutil; p_dir = os.path.join('data', 'processed'); [shutil.rmtree(os.path.join(p_dir, d)) for d in os.listdir(p_dir) if os.path.isdir(os.path.join(p_dir, d)) and d != 'CRIADO']; [os.remove(os.path.join(p_dir, f)) for f in os.listdir(p_dir) if os.path.isfile(os.path.join(p_dir, f))]"

# Executa toda a suite de testes integrados do projeto
test_suite:
	python scripts/run_all_tests.py

# Executa o benchmark com as 30 perguntas
test_30:
	python scripts/test_30_perguntas.py

