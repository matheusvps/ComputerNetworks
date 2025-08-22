#!/usr/bin/env python3
"""
Servidor UDP Multi-Porta para Transferência de Arquivos Confiável
Cada cliente usa uma porta diferente para evitar mistura de mensagens
"""

import socket
import struct
import hashlib
import os
import time
import threading
from typing import Dict, List, Tuple
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiPortUDPServer:
    def __init__(self, host: str = '0.0.0.0', base_port: int = 8888):
        self.host = host
        self.base_port = base_port
        self.servers = {}  # {port: UDPServer}
        self.running = False
        self.port_lock = threading.Lock()
        
    def start(self):
        """Inicia o servidor multi-porta"""
        self.running = True
        logger.info(f"Servidor Multi-Porta iniciado em {self.host} a partir da porta {self.base_port}")
        logger.info("Aguardando conexões de clientes...")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Para o servidor multi-porta"""
        self.running = False
        logger.info("Parando servidor multi-porta...")
        
        # Para todos os servidores
        with self.port_lock:
            for port, server in self.servers.items():
                try:
                    server.stop()
                except:
                    pass
            self.servers.clear()
        
        logger.info("Servidor multi-porta parado")
    
    def get_available_port(self) -> int:
        """Obtém uma porta disponível"""
        with self.port_lock:
            port = self.base_port
            while port in self.servers:
                port += 1
            return port
    
    def create_server_for_client(self, client_address: Tuple[str, int]) -> int:
        """Cria um servidor dedicado para um cliente"""
        port = self.get_available_port()
        
        try:
            server = UDPServer(self.host, port)
            server_thread = threading.Thread(target=server.start)
            server_thread.daemon = True
            server_thread.start()
            
            with self.port_lock:
                self.servers[port] = server
            
            logger.info(f"Servidor criado na porta {port} para cliente {client_address}")
            return port
            
        except Exception as e:
            logger.error(f"Erro ao criar servidor na porta {port}: {e}")
            return None
    
    def remove_server(self, port: int):
        """Remove um servidor da porta especificada"""
        with self.port_lock:
            if port in self.servers:
                try:
                    self.servers[port].stop()
                    del self.servers[port]
                    logger.info(f"Servidor removido da porta {port}")
                except Exception as e:
                    logger.error(f"Erro ao remover servidor da porta {port}: {e}")

class UDPServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8888, buffer_size: int = 1024):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket = None
        self.running = False
        self.file_cache = {}  # Cache para arquivos já lidos
        self.segment_cache = {}  # Cache para segmentos de arquivos
        
        # Constantes do protocolo
        self.MAX_PAYLOAD_SIZE = 1024  # Tamanho máximo do payload por segmento
        self.HEADER_SIZE = 20  # Tamanho do cabeçalho em bytes
        
    def start(self):
        """Inicia o servidor UDP"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.running = True
            
            logger.info(f"Servidor UDP iniciado em {self.host}:{self.port}")
            logger.info(f"Tamanho máximo do payload: {self.MAX_PAYLOAD_SIZE} bytes")
            logger.info(f"Tamanho do cabeçalho: {self.HEADER_SIZE} bytes")
            
            self.listen()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor: {e}")
            self.stop()
    
    def stop(self):
        """Para o servidor"""
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info(f"Servidor na porta {self.port} parado")
    
    def listen(self):
        """Loop principal de escuta do servidor"""
        while self.running:
            try:
                data, client_address = self.socket.recvfrom(4096)
                logger.info(f"Requisição recebida de {client_address} na porta {self.port}")
                
                # Processa requisição em thread separada
                thread = threading.Thread(
                    target=self.handle_request,
                    args=(data, client_address)
                )
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                if self.running:
                    logger.error(f"Erro ao receber dados: {e}")
    
    def handle_request(self, data: bytes, client_address: Tuple[str, int]):
        """Processa uma requisição do cliente"""
        try:
            # Decodifica a requisição
            request = data.decode('utf-8').strip()
            logger.info(f"Requisição de {client_address} na porta {self.port}: {request}")
            
            if request.startswith('GET '):
                filename = request[4:]  # Remove 'GET ' do início
                self.handle_file_request(filename, client_address)
            elif request.startswith('RETRANSMIT '):
                # Formato: RETRANSMIT filename segment_number
                parts = request.split(' ')
                if len(parts) >= 3:
                    filename = parts[1]
                    segment_number = int(parts[2])
                    self.handle_retransmit_request(filename, segment_number, client_address)
            else:
                self.send_error(client_address, "Formato de requisição inválido")
                
        except Exception as e:
            logger.error(f"Erro ao processar requisição: {e}")
            self.send_error(client_address, f"Erro interno: {str(e)}")
    
    def handle_file_request(self, filename: str, client_address: Tuple[str, int]):
        """Processa requisição de arquivo"""
        try:
            # Verifica se arquivo existe
            if not os.path.exists(filename):
                self.send_error(client_address, f"Arquivo não encontrado: {filename}")
                return
            
            # Obtém informações do arquivo
            file_size = os.path.getsize(filename)
            logger.info(f"Arquivo solicitado na porta {self.port}: {filename} ({file_size} bytes)")
            
            # Calcula número de segmentos
            num_segments = (file_size + self.MAX_PAYLOAD_SIZE - 1) // self.MAX_PAYLOAD_SIZE
            
            # Envia informações do arquivo
            file_info = f"FILE_INFO {filename} {file_size} {num_segments}"
            self.socket.sendto(file_info.encode('utf-8'), client_address)
            
            # Aguarda confirmação
            time.sleep(0.1)
            
            # Envia segmentos do arquivo
            self.send_file_segments(filename, client_address)
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {filename}: {e}")
            self.send_error(client_address, f"Erro ao processar arquivo: {str(e)}")
    
    def send_file_segments(self, filename: str, client_address: Tuple[str, int]):
        """Envia todos os segmentos do arquivo"""
        try:
            with open(filename, 'rb') as file:
                segment_number = 0
                
                while True:
                    # Lê dados do arquivo
                    data = file.read(self.MAX_PAYLOAD_SIZE)
                    if not data:
                        break
                    
                    # Cria segmento com cabeçalho
                    segment = self.create_segment(segment_number, data, filename)
                    
                    # Envia segmento
                    self.socket.sendto(segment, client_address)
                    logger.debug(f"Segmento {segment_number} enviado para {client_address} na porta {self.port}")
                    
                    segment_number += 1
                    time.sleep(0.01)  # Pequena pausa para não sobrecarregar
                
                # Envia sinal de fim de transmissão
                end_message = f"END_TRANSMISSION {filename}"
                self.socket.sendto(end_message.encode('utf-8'), client_address)
                logger.info(f"Transmissão do arquivo {filename} concluída na porta {self.port}")
                
        except Exception as e:
            logger.error(f"Erro ao enviar segmentos do arquivo {filename}: {e}")
    
    def create_segment(self, segment_number: int, data: bytes, filename: str) -> bytes:
        """Cria um segmento com cabeçalho customizado"""
        # Cabeçalho: [segment_number(4)][checksum(16)][filename_length(2)][data_length(2)]
        filename_bytes = filename.encode('utf-8')
        filename_length = len(filename_bytes)
        data_length = len(data)
        
        # Calcula checksum MD5 dos dados
        checksum = hashlib.md5(data).digest()
        
        # Monta cabeçalho
        header = struct.pack('!I16sHH', segment_number, checksum, filename_length, data_length)
        
        # Monta segmento completo
        segment = header + filename_bytes + data
        
        return segment
    
    def handle_retransmit_request(self, filename: str, segment_number: int, client_address: Tuple[str, int]):
        """Processa requisição de retransmissão de segmento"""
        try:
            if not os.path.exists(filename):
                self.send_error(client_address, f"Arquivo não encontrado: {filename}")
                return
            
            # Lê o segmento específico
            with open(filename, 'rb') as file:
                file.seek(segment_number * self.MAX_PAYLOAD_SIZE)
                data = file.read(self.MAX_PAYLOAD_SIZE)
                
                if data:
                    # Cria e envia segmento
                    segment = self.create_segment(segment_number, data, filename)
                    self.socket.sendto(segment, client_address)
                    logger.info(f"Segmento {segment_number} retransmitido para {client_address} na porta {self.port}")
                else:
                    self.send_error(client_address, f"Segmento {segment_number} inválido")
                    
        except Exception as e:
            logger.error(f"Erro ao retransmitir segmento {segment_number}: {e}")
            self.send_error(client_address, f"Erro ao retransmitir: {str(e)}")
    
    def send_error(self, client_address: Tuple[str, int], error_message: str):
        """Envia mensagem de erro para o cliente"""
        try:
            error_msg = f"ERROR {error_message}"
            self.socket.sendto(error_msg.encode('utf-8'), client_address)
            logger.warning(f"Erro enviado para {client_address} na porta {self.port}: {error_message}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de erro: {e}")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Servidor UDP Multi-Porta para Transferência de Arquivos')
    parser.add_argument('--host', default='0.0.0.0', help='Host para escutar (padrão: 0.0.0.0)')
    parser.add_argument('--base-port', type=int, default=8888, help='Porta base para iniciar (padrão: 8888)')
    
    args = parser.parse_args()
    
    # Verifica se a porta é válida
    if args.base_port <= 1024:
        print("Erro: Porta deve ser maior que 1024")
        return
    
    server = MultiPortUDPServer(args.host, args.base_port)
    
    try:
        print(f"Servidor UDP Multi-Porta iniciando em {args.host} a partir da porta {args.base_port}")
        print("Pressione Ctrl+C para parar")
        server.start()
    except KeyboardInterrupt:
        print("\nParando servidor...")
        server.stop()

if __name__ == "__main__":
    main()
