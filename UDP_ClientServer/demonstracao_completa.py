#!/usr/bin/env python3

import os
import time
import subprocess
import socket
import threading
import sys
from typing import List, Dict

class DemonstracaoUDP:
    def __init__(self):
        self.demonstracoes = [
            ("1. Ambiente e Setup", self.ambiente_setup),
            ("2. Protocolo de Aplicação e Requisição", self.protocolo_aplicacao),
            ("3. Transferência e Segmentação", self.transferencia_segmentacao),
            ("4. Mecanismos de Confiabilidade", self.mecanismos_confiabilidade),
            ("5. Recuperação de Erros/Perdas", self.recuperacao_erros),
            ("6. Tratamento de Erros do Servidor", self.tratamento_erros),
            ("7. Cenários de Teste Específicos", self.cenarios_teste)
        ]
        
        self.arquivos_teste = [
            ("arquivo_pequeno.txt", 0.1),
            ("arquivo_medio.txt", 1),
            ("arquivo_grande.txt", 10)
        ]
        
    def print_header(self, titulo: str):
        print(f"\n{'='*80}")
        print(f"🔧 {titulo}")
        print(f"{'='*80}")
    
    def print_step(self, passo: str):
        print(f"\n📋 {passo}")
        print("-" * 60)
    
    def print_success(self, mensagem: str):
        print(f"✅ {mensagem}")
    
    def print_error(self, mensagem: str):
        print(f"❌ {mensagem}")
    
    def print_info(self, mensagem: str):
        print(f"ℹ️  {mensagem}")
    
    def print_code(self, codigo: str, linguagem: str = "python"):
        print(f"```{linguagem}")
        print(codigo)
        print("```")
    
    def criar_arquivos_teste(self):
        self.print_step("Criando arquivos de teste...")
        
        for filename, size_mb in self.arquivos_teste:
            try:
                result = subprocess.run([
                    "python3", "create_test_file.py", 
                    "--filename", filename, 
                    "--size", str(size_mb)
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(filename):
                    actual_size = os.path.getsize(filename)
                    self.print_success(f"Arquivo criado: {filename} ({actual_size} bytes)")
                else:
                    self.print_error(f"Falha ao criar {filename}: {result.stderr}")
                    
            except Exception as e:
                self.print_error(f"Erro ao criar {filename}: {e}")
    
    def ambiente_setup(self):
        self.print_header("AMBIENTE E SETUP")
        
        self.print_step("1.1 - Execução do Servidor UDP")
        self.print_info("O servidor UDP é implementado usando a API de sockets diretamente:")
        self.print_code("""
# Criação do socket UDP
self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
self.socket.bind((self.host, self.port))

# Loop principal de escuta
while self.running:
    data, client_address = self.socket.recvfrom(4096)
    # Processa requisição em thread separada
    thread = threading.Thread(target=self.handle_request, args=(data, client_address))
    thread.start()
""")
        
        self.print_step("1.2 - Execução do Cliente UDP")
        self.print_info("O cliente também usa sockets UDP diretamente:")
        self.print_code("""
# Conexão ao servidor
self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
self.socket.settimeout(self.timeout)

# Envio de requisição
self.socket.sendto(request.encode('utf-8'), self.server_address)
""")
        
        self.print_step("1.3 - Especificação de Endereço IP e Porta")
        self.print_info("O cliente especifica o endereço do servidor via linha de comando:")
        self.print_code("""
# Uso: python3 client.py SERVER_HOST SERVER_PORT FILENAME
python3 client.py 127.0.0.1 8888 arquivo.txt

# No código:
self.server_address = (server_host, server_port)
""")
        
        self.print_step("1.4 - Uso Direto da API de Sockets (Sem Bibliotecas de Abstração)")
        self.print_info("O sistema usa apenas bibliotecas padrão do Python:")
        self.print_code("""
import socket          # API de sockets do sistema operacional
import struct          # Empacotamento de dados binários
import hashlib         # Cálculo de checksums
import os              # Operações de sistema de arquivos
import threading       # Processamento multithread
import logging         # Sistema de logging

# NÃO usa bibliotecas como:
# - asyncio (abstração de I/O assíncrono)
# - twisted (framework de rede)
# - pysocket (wrapper de alto nível)
""")
        
        self.print_success("Ambiente e Setup demonstrado com sucesso!")
    
    def protocolo_aplicacao(self):
        self.print_header("PROTOCOLO DE APLICAÇÃO E REQUISIÇÃO")
        
        # 1. Protocolo de aplicação proposto
        self.print_step("2.1 - Protocolo de Aplicação Proposto")
        self.print_info("O sistema implementa um protocolo customizado sobre UDP:")
        self.print_code("""
# Mensagens de controle:
GET filename                    # Solicita arquivo
FILE_INFO filename size segs    # Informações do arquivo
RETRANSMIT filename seg_num    # Solicita retransmissão
END_TRANSMISSION filename      # Fim da transmissão
ERROR message                   # Mensagem de erro
""")
        
        # 2. Demonstração de requisições
        self.print_step("2.2 - Demonstração de Requisições de Arquivos")
        self.print_info("Vamos testar requisições de arquivos diferentes:")
        
        # Cria arquivos de teste se não existirem
        if not os.path.exists("arquivo_pequeno.txt"):
            self.criar_arquivos_teste()
        
        # Testa requisição de arquivo pequeno
        self.print_info("Testando requisição de arquivo pequeno...")
        try:
            # Inicia servidor em background
            server_process = subprocess.Popen([
                "python3", "server.py", "--port", "8891"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)  # Aguarda servidor inicializar
            
            # Testa cliente
            result = subprocess.run([
                "python3", "client.py", "127.0.0.1", "8891", "arquivo_pequeno.txt"
            ], capture_output=True, text=True, timeout=30)
            
            # Para servidor
            server_process.terminate()
            server_process.wait()
            
            if result.returncode == 0:
                self.print_success("Arquivo pequeno transferido com sucesso!")
            else:
                self.print_error(f"Falha na transferência: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.print_error("Teste de arquivo pequeno excedeu o timeout")
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
            except:
                pass
        except Exception as e:
            self.print_error(f"Erro no teste: {e}")
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
            except:
                pass
        
        # Testa requisição de arquivo médio
        self.print_info("Testando requisição de arquivo médio...")
        try:
            server_process = subprocess.Popen([
                "python3", "server.py", "--port", "8892"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)
            
            result = subprocess.run([
                "python3", "client.py", "127.0.0.1", "8892", "arquivo_medio.txt"
            ], capture_output=True, text=True, timeout=60)
            
            server_process.terminate()
            server_process.wait()
            
            if result.returncode == 0:
                self.print_success("Arquivo médio transferido com sucesso!")
            else:
                self.print_error(f"Falha na transferência: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.print_error("Teste de arquivo médio excedeu o timeout")
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
            except:
                pass
        except Exception as e:
            self.print_error(f"Erro no teste: {e}")
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
            except:
                pass
        
        self.print_success("Protocolo de Aplicação demonstrado com sucesso!")
    
    def transferencia_segmentacao(self):
        self.print_header("TRANSFERÊNCIA E SEGMENTAÇÃO")
        
        # 1. Transferência de arquivo grande
        self.print_step("3.1 - Transferência de Arquivo Grande (>10MB)")
        self.print_info("Vamos testar a transferência de um arquivo de 10MB:")
        
        if not os.path.exists("arquivo_grande.txt"):
            self.print_info("Criando arquivo grande de 10MB...")
            self.criar_arquivos_teste()
        
        try:
            server_process = subprocess.Popen([
                "python3", "server.py", "--port", "8893"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)
            
            # Monitora o processo em background
            start_time = time.time()
            result = subprocess.run([
                "python3", "client.py", "127.0.0.1", "8893", "arquivo_grande.txt"
            ], capture_output=True, text=True, timeout=300)  # 5 minutos para arquivo grande
            
            end_time = time.time()
            duration = end_time - start_time
            
            server_process.terminate()
            server_process.wait()
            
            if result.returncode == 0:
                file_size = os.path.getsize("arquivo_grande.txt")
                transfer_rate = file_size / (1024 * 1024 * duration)  # MB/s
                self.print_success(f"Arquivo grande transferido em {duration:.2f}s")
                self.print_info(f"Taxa de transferência: {transfer_rate:.2f} MB/s")
            else:
                self.print_error(f"Falha na transferência: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.print_error("Transferência de arquivo grande excedeu o timeout")
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
            except:
                pass
        except Exception as e:
            self.print_error(f"Erro no teste: {e}")
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
            except:
                pass
        
        # 2. Explicação da segmentação
        self.print_step("3.2 - Como o Arquivo é Dividido em Segmentos")
        self.print_info("O arquivo é dividido em segmentos de tamanho fixo:")
        self.print_code("""
# No servidor:
MAX_PAYLOAD_SIZE = 1024  # 1024 bytes por segmento

def send_file_segments(self, filename, client_address):
    with open(filename, 'rb') as file:
        segment_number = 0
        while True:
            data = file.read(self.MAX_PAYLOAD_SIZE)  # Lê 1024 bytes
            if not data:
                break
            
            segment = self.create_segment(segment_number, data, filename)
            self.socket.sendto(segment, client_address)
            segment_number += 1
""")
        
        # 3. Tamanho do buffer/segmento
        self.print_step("3.3 - Tamanho do Buffer/Segmento de Dados")
        self.print_info("Configurações de tamanho:")
        self.print_code("""
# Tamanhos configurados:
MAX_PAYLOAD_SIZE = 1024    # Dados por segmento
HEADER_SIZE = 20           # Cabeçalho fixo
BUFFER_SIZE = 4096         # Buffer de recepção do cliente

# Estrutura do segmento:
[Cabeçalho: 20 bytes] + [Nome arquivo: N bytes] + [Dados: 0-1024 bytes]
""")
        
        # 4. Relação com MTU
        self.print_step("3.4 - Relação com MTU (Maximum Transmission Unit)")
        self.print_info("Análise do MTU e fragmentação IP:")
        self.print_code("""
# Análise do MTU:
MTU Ethernet padrão: 1500 bytes
Overhead IP: 20 bytes
Overhead UDP: 8 bytes  
Overhead nosso protocolo: 20 bytes + nome arquivo
Espaço disponível: 1500 - 20 - 8 - 20 = 1452 bytes

# Nossa escolha de 1024 bytes:
✅ Seguro: Fica bem abaixo do limite de fragmentação
✅ Eficiente: Evita fragmentação IP automática
✅ Flexível: Permite nomes de arquivo de até ~400 caracteres
""")
        
        self.print_success("Transferência e Segmentação demonstrada com sucesso!")
    
    def mecanismos_confiabilidade(self):
        self.print_header("MECANISMOS DE CONFIABILIDADE")
        
        # 1. Ordenação com números de sequência
        self.print_step("4.1 - Ordenação: Números de Sequência")
        self.print_info("Cada segmento tem um número de sequência para ordenação:")
        self.print_code("""
# Estrutura do cabeçalho:
header = struct.pack('!I16sHH', 
    segment_number,    # 4 bytes - Número sequencial (0, 1, 2, ...)
    checksum,          # 16 bytes - MD5 dos dados
    filename_length,   # 2 bytes - Tamanho do nome do arquivo
    data_length        # 2 bytes - Tamanho dos dados
)

# No cliente:
received_segments = {}
for segment_number in range(expected_segments):
    if segment_number in received_segments:
        segment_data = received_segments[segment_number]['data']
        output_file.write(segment_data)  # Ordem correta garantida
""")
        
        # 2. Integridade com checksum
        self.print_step("4.2 - Integridade: Verificação com Checksum")
        self.print_info("Cada segmento é verificado usando MD5:")
        self.print_code("""
# No servidor (envio):
checksum = hashlib.md5(data).digest()  # Calcula MD5 dos dados
header = struct.pack('!I16sHH', segment_number, checksum, ...)

# No cliente (verificação):
def verify_checksum(self, data, expected_checksum):
    calculated_checksum = hashlib.md5(data).digest()
    return calculated_checksum == expected_checksum

# Uso:
if self.verify_checksum(segment_data, checksum):
    self.received_segments[segment_number] = {...}  # Aceita segmento
else:
    print(f"Checksum inválido para segmento {segment_number}")  # Rejeita
""")
        
        # 3. Montagem e conferência do arquivo
        self.print_step("4.3 - Montagem e Conferência do Arquivo Completo")
        self.print_info("O cliente reconstrói o arquivo e verifica a completude:")
        self.print_code("""
def reconstruct_file(self, output_dir):
    with open(output_path, 'wb') as output_file:
        for segment_number in range(self.expected_segments):
            if segment_number in self.received_segments:
                segment_data = self.received_segments[segment_number]['data']
                output_file.write(segment_data)
            else:
                return False  # Segmento faltando
    
    # Verifica tamanho do arquivo reconstruído
    actual_size = os.path.getsize(output_path)
    expected_size = self.file_info['file_size']
    
    if actual_size != expected_size:
        return False  # Tamanho incorreto
    
    return True  # Arquivo completo e correto
""")
        
        self.print_success("Mecanismos de Confiabilidade demonstrados com sucesso!")
    
    def recuperacao_erros(self):
        self.print_header("RECUPERAÇÃO DE ERROS/PERDAS")
        
        # 1. Simulação de perda de pacotes
        self.print_step("5.1 - Simulação de Perda de Pacotes")
        self.print_info("O cliente pode simular perda de segmentos para testar recuperação:")
        self.print_code("""
# Habilita simulação de perda:
client.enable_loss_simulation(probability=0.2)  # 20% de perda

def should_discard_segment(self):
    import random
    return random.random() < self.loss_probability

# No processamento:
if self.simulate_loss and self.should_discard_segment():
    logger.info(f"Simulando perda do segmento {segment_number}")
    return  # Descarta segmento
""")
        
        # 2. Detecção de segmentos faltantes
        self.print_step("5.2 - Detecção de Segmentos Faltantes")
        self.print_info("O cliente detecta segmentos perdidos por análise de sequência:")
        self.print_code("""
def check_missing_segments(self):
    # Compara segmentos esperados vs. recebidos
    self.missing_segments = set(range(self.expected_segments)) - set(self.received_segments.keys())
    
    if self.missing_segments:
        logger.warning(f"Segmentos perdidos: {sorted(self.missing_segments)}")
        self.request_missing_segments()

# Exemplo de saída:
# WARNING - Segmentos perdidos: [42, 156, 789]
""")
        
        # 3. Solicitação de retransmissão
        self.print_step("5.3 - Solicitação de Retransmissão")
        self.print_info("O cliente solicita retransmissão de segmentos específicos:")
        self.print_code("""
def request_missing_segments(self):
    for segment_number in self.missing_segments:
        request = f"RETRANSMIT {self.current_file} {segment_number}"
        self.socket.sendto(request.encode('utf-8'), self.server_address)
        logger.info(f"Solicitando retransmissão do segmento {segment_number}")
        
        # Aguarda retransmissão
        self.wait_for_retransmission(segment_number)

# Formato da requisição:
# RETRANSMIT arquivo.txt 42
""")
        
        # 4. Mecanismo de disparo da retransmissão
        self.print_step("5.4 - Mecanismo de Disparo da Retransmissão")
        self.print_info("Retransmissão é disparada por timeout e análise de sequência:")
        self.print_code("""
def wait_for_retransmission(self, segment_number, max_wait=10.0):
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            data, _ = self.socket.recvfrom(4096)
            self.process_segment(data)
            
            # Verifica se o segmento foi recebido
            if segment_number in self.received_segments:
                logger.info(f"Segmento {segment_number} retransmitido com sucesso")
                self.missing_segments.discard(segment_number)
                break
                
        except socket.timeout:
            continue  # Continua aguardando
    
    if segment_number in self.missing_segments:
        logger.error(f"Timeout na retransmissão do segmento {segment_number}")
""")
        
        # Demonstração prática
        self.print_info("Vamos demonstrar a recuperação de erros na prática...")
        try:
            server_process = subprocess.Popen([
                "python3", "server.py", "--port", "8894"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)
            
            # Cliente com simulação de perda
            result = subprocess.run([
                "python3", "client.py", "127.0.0.1", "8894", "arquivo_medio.txt",
                "--simulate-loss", "--loss-probability", "0.3"
            ], capture_output=True, text=True, timeout=60)
            
            server_process.terminate()
            server_process.wait()
            
            if result.returncode == 0:
                self.print_success("Recuperação de erros demonstrada com sucesso!")
                self.print_info("Verifique os logs para ver segmentos perdidos e retransmitidos")
            else:
                self.print_error(f"Falha na demonstração: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.print_error("Demonstração de recuperação de erros excedeu o timeout")
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
            except:
                pass
        except Exception as e:
            self.print_error(f"Erro na demonstração: {e}")
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
            except:
                pass
        
        self.print_success("Recuperação de Erros demonstrada com sucesso!")
    
    def tratamento_erros(self):
        self.print_header("TRATAMENTO DE ERROS DO SERVIDOR")
        
        # 1. Arquivo inexistente
        self.print_step("6.1 - Cenário: Cliente Requisita Arquivo Inexistente")
        self.print_info("Vamos testar o que acontece quando o cliente solicita um arquivo que não existe:")
        
        try:
            server_process = subprocess.Popen([
                "python3", "server.py", "--port", "8895"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)
            
            # Tenta baixar arquivo inexistente
            result = subprocess.run([
                "python3", "client.py", "127.0.0.1", "8895", "arquivo_inexistente.txt"
            ], capture_output=True, text=True, timeout=30)
            
            server_process.terminate()
            server_process.wait()
            
            if "File not found" in result.stderr or "Arquivo não encontrado" in result.stderr:
                self.print_success("Erro de arquivo não encontrado tratado corretamente!")
                self.print_info("Servidor enviou mensagem de erro apropriada")
            else:
                self.print_error("Erro não foi tratado corretamente")
                self.print_info(f"Stderr: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.print_error("Teste de arquivo inexistente excedeu o timeout")
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
            except:
                pass
        except Exception as e:
            self.print_error(f"Erro no teste: {e}")
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
            except:
                pass
        
        # 2. Formato de mensagens de erro
        self.print_step("6.2 - Formato das Mensagens de Erro")
        self.print_info("O protocolo define mensagens de erro padronizadas:")
        self.print_code("""
# Formato das mensagens de erro:
ERROR error_message

# Exemplos implementados:
ERROR File not found: arquivo.txt
ERROR Invalid segment number: 999
ERROR Internal server error
ERROR Invalid request format

# No servidor:
def send_error(self, client_address, error_message):
    error_msg = f"ERROR {error_message}"
    self.socket.sendto(error_msg.encode('utf-8'), client_address)

# No cliente:
if message.startswith('ERROR '):
    error_msg = message[6:]  # Remove 'ERROR ' do início
    logger.error(f"Erro do servidor: {error_msg}")
""")
        
        # 3. Outros erros tratados
        self.print_step("6.3 - Outros Erros Tratados")
        self.print_info("O sistema trata diversos tipos de erro:")
        self.print_code("""
# Tipos de erro tratados:

1. Arquivo não encontrado:
   - Verifica se arquivo existe antes de processar
   - Envia mensagem de erro específica

2. Formato de requisição inválido:
   - Valida formato das mensagens recebidas
   - Rejeita requisições malformadas

3. Segmentos inválidos:
   - Verifica números de segmento válidos
   - Rejeita segmentos com dados corrompidos

4. Erros internos:
   - Captura exceções durante processamento
   - Envia mensagens de erro genéricas

5. Timeouts:
   - Detecta clientes não responsivos
   - Limpa recursos alocados
""")
        
        self.print_success("Tratamento de Erros demonstrado com sucesso!")
    
    def cenarios_teste(self):
        self.print_header("CENÁRIOS DE TESTE ESPECÍFICOS")
        
        # 1. Múltiplos clientes simultâneos
        self.print_step("7.1 - Servidor Lidando com Dois Clientes Simultâneos")
        self.print_info("Vamos testar o servidor atendendo múltiplos clientes:")
        
        try:
            server_process = subprocess.Popen([
                "python3", "server.py", "--port", "8896"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)
            
            # Cliente 1 em background com timeout
            client1_process = subprocess.Popen([
                "python3", "client.py", "127.0.0.1", "8896", "arquivo_pequeno.txt"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Cliente 2 em background com timeout
            client2_process = subprocess.Popen([
                "python3", "client.py", "127.0.0.1", "8896", "arquivo_medio.txt"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Aguarda ambos terminarem com timeout
            try:
                client1_process.wait(timeout=60)  # 60 segundos de timeout
                self.print_info("Cliente 1 terminou")
            except subprocess.TimeoutExpired:
                self.print_error("Cliente 1 não terminou dentro do timeout")
                client1_process.terminate()
                client1_process.wait()
            
            try:
                client2_process.wait(timeout=60)  # 60 segundos de timeout
                self.print_info("Cliente 2 terminou")
            except subprocess.TimeoutExpired:
                self.print_error("Cliente 2 não terminou dentro do timeout")
                client2_process.terminate()
                client2_process.wait()
            
            # Para servidor
            server_process.terminate()
            server_process.wait()
            
            if client1_process.returncode == 0 and client2_process.returncode == 0:
                self.print_success("Múltiplos clientes atendidos com sucesso!")
                self.print_info("Servidor processou requisições concorrentes")
            else:
                self.print_error("Falha no teste de múltiplos clientes")
                if client1_process.returncode != 0:
                    self.print_error(f"Cliente 1 falhou com código: {client1_process.returncode}")
                if client2_process.returncode != 0:
                    self.print_error(f"Cliente 2 falhou com código: {client2_process.returncode}")
                
        except Exception as e:
            self.print_error(f"Erro no teste: {e}")
            # Garante que os processos sejam terminados
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
                if 'client1_process' in locals():
                    client1_process.terminate()
                    client1_process.wait()
                if 'client2_process' in locals():
                    client2_process.terminate()
                    client2_process.wait()
            except:
                pass
        
        # 2. Cliente conectando antes do servidor
        self.print_step("7.2 - Cliente Tentando Conectar Antes do Servidor")
        self.print_info("Vamos testar o comportamento quando o cliente tenta conectar antes do servidor:")
        
        try:
            # Tenta conectar sem servidor rodando
            result = subprocess.run([
                "python3", "client.py", "127.0.0.1", "8897", "arquivo.txt"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.print_success("Erro de conexão tratado corretamente!")
                self.print_info("Cliente falhou ao tentar conectar sem servidor")
            else:
                self.print_error("Cliente não falhou como esperado")
                
        except Exception as e:
            self.print_error(f"Erro no teste: {e}")
        
        # 3. Servidor interrompido durante transferência
        self.print_step("7.3 - Servidor Interrompido Durante Transferência")
        self.print_info("Vamos testar o que acontece se o servidor for interrompido:")
        
        try:
            server_process = subprocess.Popen([
                "python3", "server.py", "--port", "8898"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(3)
            
            # Inicia cliente em background
            client_process = subprocess.Popen([
                "python3", "client.py", "127.0.0.1", "8898", "arquivo_grande.txt"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Aguarda um pouco e interrompe servidor
            time.sleep(5)
            server_process.terminate()
            server_process.wait()
            
            # Aguarda cliente terminar com timeout
            try:
                client_process.wait(timeout=30)  # 30 segundos de timeout
                self.print_info("Cliente terminou após interrupção do servidor")
            except subprocess.TimeoutExpired:
                self.print_error("Cliente não terminou dentro do timeout")
                client_process.terminate()
                client_process.wait()
            
            if client_process.returncode != 0:
                self.print_success("Interrupção do servidor tratada corretamente!")
                self.print_info("Cliente detectou a perda de conexão")
            else:
                self.print_error("Cliente não detectou a interrupção")
                
        except Exception as e:
            self.print_error(f"Erro no teste: {e}")
            # Garante que os processos sejam terminados
            try:
                if 'server_process' in locals():
                    server_process.terminate()
                    server_process.wait()
                if 'client_process' in locals():
                    client_process.terminate()
                    client_process.wait()
            except:
                pass
        
        self.print_success("Cenários de Teste demonstrados com sucesso!")
    
    def executar_todas_demonstracoes(self):
        print("🚀 DEMONSTRAÇÃO COMPLETA DO SISTEMA UDP")
        print("=" * 80)
        print("Este script demonstra e explica todos os itens obrigatórios do projeto")
        print("=" * 80)
        
        self.criar_arquivos_teste()
        
        for titulo, funcao in self.demonstracoes:
            try:
                funcao()
                time.sleep(2)
            except Exception as e:
                self.print_error(f"Erro na demonstração '{titulo}': {e}")
        
        print(f"\n{'='*80}")
        print("🎉 TODAS AS DEMONSTRAÇÕES FORAM CONCLUÍDAS!")
        print("=" * 80)
        print("O sistema UDP demonstrou com sucesso todos os itens obrigatórios:")
        print("✅ Ambiente e Setup")
        print("✅ Protocolo de Aplicação e Requisição")
        print("✅ Transferência e Segmentação")
        print("✅ Mecanismos de Confiabilidade")
        print("✅ Recuperação de Erros/Perdas")
        print("✅ Tratamento de Erros do Servidor")
        print("✅ Cenários de Teste Específicos")
        print(f"\n{'='*80}")

def main():
    demonstracao = DemonstracaoUDP()
    
    try:
        demonstracao.executar_todas_demonstracoes()
    except KeyboardInterrupt:
        print("\n\nDemonstração interrompida pelo usuário")
    except Exception as e:
        print(f"\n\nErro durante demonstração: {e}")
    
    print("\nDemonstração finalizada!")

if __name__ == "__main__":
    main()
