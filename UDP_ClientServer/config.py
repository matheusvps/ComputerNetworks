#!/usr/bin/env python3

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8888
DEFAULT_TIMEOUT = 5.0

MAX_PAYLOAD_SIZE = 1024
HEADER_SIZE = 20
MAX_FILENAME_LENGTH = 255

SEGMENT_DELAY = 0.01
MAX_RETRANSMISSION_WAIT = 10.0
BUFFER_SIZE = 4096

DEFAULT_LOSS_PROBABILITY = 0.1

LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

DEFAULT_OUTPUT_DIR = '.'
MAX_FILE_SIZE = 1024 * 1024 * 100

ENABLE_CHECKSUM = True
CHECKSUM_ALGORITHM = 'md5'

DEBUG_MODE = False
VERBOSE_OUTPUT = False

def validate_config():
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
    errors = validate_config()
    
    if errors:
        print("Erros de configuração encontrados:")
        for error in errors:
            print(f"  - {error}")
        exit(1)
    
    print("Configurações do Sistema UDP:")
    print("="*40)
    
    config = get_config_summary()
    for category, settings in config.items():
        print(f"\n{category.upper()}:")
        for key, value in settings.items():
            print(f"  {key}: {value}")
    
    print("\n✓ Todas as configurações são válidas!")
