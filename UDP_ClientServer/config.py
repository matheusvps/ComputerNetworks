#!/usr/bin/env python3
"""
Arquivo de Configuração Centralizada para o Sistema UDP
Define constantes e configurações utilizadas por todos os componentes
"""

# Configurações de Rede
DEFAULT_HOST = '0.0.0.0'  # Host padrão para o servidor
DEFAULT_PORT = 8888        # Porta padrão para o servidor
DEFAULT_TIMEOUT = 5.0      # Timeout padrão em segundos

# Configurações do Protocolo
MAX_PAYLOAD_SIZE = 1024    # Tamanho máximo do payload por segmento (bytes)
HEADER_SIZE = 20           # Tamanho do cabeçalho em bytes
MAX_FILENAME_LENGTH = 255  # Tamanho máximo do nome do arquivo

# Configurações de Performance
SEGMENT_DELAY = 0.01      # Delay entre segmentos (segundos)
MAX_RETRANSMISSION_WAIT = 10.0  # Tempo máximo para aguardar retransmissão
BUFFER_SIZE = 4096         # Tamanho do buffer de recepção

# Configurações de Simulação de Perda
DEFAULT_LOSS_PROBABILITY = 0.1  # Probabilidade padrão de perda (10%)

# Configurações de Logging
LOG_LEVEL = 'INFO'         # Nível de logging padrão
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Configurações de Arquivo
DEFAULT_OUTPUT_DIR = '.'   # Diretório de saída padrão
MAX_FILE_SIZE = 1024 * 1024 * 100  # Tamanho máximo de arquivo (100MB)

# Configurações de Segurança
ENABLE_CHECKSUM = True     # Habilita verificação de checksum
CHECKSUM_ALGORITHM = 'md5' # Algoritmo de checksum a ser usado

# Configurações de Debug
DEBUG_MODE = False         # Modo debug (mais logs detalhados)
VERBOSE_OUTPUT = False     # Saída verbosa para demonstrações

# Validações
def validate_config():
    """Valida as configurações do sistema"""
    errors = []
    
    if DEFAULT_PORT <= 1024:
        errors.append("Porta padrão deve ser maior que 1024")
    
    if MAX_PAYLOAD_SIZE <= 0:
        errors.append("Tamanho do payload deve ser positivo")
    
    if HEADER_SIZE <= 0:
        errors.append("Tamanho do cabeçalho deve ser positivo")
    
    if DEFAULT_TIMEOUT <= 0:
        errors.append("Timeout deve ser positivo")
    
    if DEFAULT_LOSS_PROBABILITY < 0 or DEFAULT_LOSS_PROBABILITY > 1:
        errors.append("Probabilidade de perda deve estar entre 0 e 1")
    
    if MAX_FILE_SIZE <= 0:
        errors.append("Tamanho máximo de arquivo deve ser positivo")
    
    return errors

def get_config_summary():
    """Retorna um resumo das configurações"""
    return {
        'network': {
            'default_host': DEFAULT_HOST,
            'default_port': DEFAULT_PORT,
            'default_timeout': DEFAULT_TIMEOUT
        },
        'protocol': {
            'max_payload_size': MAX_PAYLOAD_SIZE,
            'header_size': HEADER_SIZE,
            'max_filename_length': MAX_FILENAME_LENGTH
        },
        'performance': {
            'segment_delay': SEGMENT_DELAY,
            'max_retransmission_wait': MAX_RETRANSMISSION_WAIT,
            'buffer_size': BUFFER_SIZE
        },
        'simulation': {
            'default_loss_probability': DEFAULT_LOSS_PROBABILITY
        },
        'security': {
            'enable_checksum': ENABLE_CHECKSUM,
            'checksum_algorithm': CHECKSUM_ALGORITHM
        }
    }

if __name__ == "__main__":
    # Valida configurações
    errors = validate_config()
    
    if errors:
        print("Erros de configuração encontrados:")
        for error in errors:
            print(f"  - {error}")
        exit(1)
    
    # Mostra resumo das configurações
    print("Configurações do Sistema UDP:")
    print("="*40)
    
    config = get_config_summary()
    for category, settings in config.items():
        print(f"\n{category.upper()}:")
        for key, value in settings.items():
            print(f"  {key}: {value}")
    
    print("\n✓ Todas as configurações são válidas!")
