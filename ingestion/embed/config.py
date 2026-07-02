import os
import yaml

def load_config(config_path="ingestion/embed/embed_config.yml"):
    """Carrega as configurações do arquivo YAML."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuração não encontrada em {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config
