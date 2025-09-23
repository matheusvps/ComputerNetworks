#!/usr/bin/env python3

import socket
import struct
import hashlib
import os
import time
import threading
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiPortUDPServer:
    def __init__(self, host: str = '0.0.0.0', base_port: int = 8888):
        self.host = host
        self.base_port = base_port
        self.servers = {}
        self.running = False
        self.port_lock = threading.Lock()
        
    def start(self):
        self.running = True
        logger.info(f"Servidor Multi-Porta iniciado em {self.host} a partir da porta {self.base_port}")
        logger.info("Aguardando conexões de clientes...")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        self.running = False
        logger.info("Parando servidor multi-porta...")
        
        with self.port_lock:
            for port, server in self.servers.items():
                try:
                    server.stop()
                except:
                    pass
            self.servers.clear()
        
        logger.info("Servidor multi-porta parado")
    
    def get_available_port(self) -> int:
        with self.port_lock:
            port = self.base_port
            while port in self.servers:
                port += 1
            return port
    
    def create_server_for_client(self, client_address: Tuple[str, int]) -> int:
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
        self.file_cache = {}
        self.segment_cache = {}
        
        self.MAX_PAYLOAD_SIZE = 1024
        self.HEADER_SIZE = 20
        
    def start(self):
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
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info(f"Servidor na porta {self.port} parado")
    
    def listen(self):
        while self.running:
            try:
                data, client_address = self.socket.recvfrom(4096)
                logger.info(f"Requisição recebida de {client_address} na porta {self.port}")
                
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
        try:
            request = data.decode('utf-8').strip()
            logger.info(f"Requisição de {client_address} na porta {self.port}: {request}")
            
            if request.startswith('GET '):
                filename = request[4:]
                self.handle_file_request(filename, client_address)
            elif request.startswith('RETRANSMIT '):
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
        try:
            if not os.path.exists(filename):
                self.send_error(client_address, f"Arquivo não encontrado: {filename}")
                return
            
            file_size = os.path.getsize(filename)
            logger.info(f"Arquivo solicitado na porta {self.port}: {filename} ({file_size} bytes)")
            
            num_segments = (file_size + self.MAX_PAYLOAD_SIZE - 1) // self.MAX_PAYLOAD_SIZE
            
            file_info = f"FILE_INFO {filename} {file_size} {num_segments}"
            self.socket.sendto(file_info.encode('utf-8'), client_address)
            
            time.sleep(0.1)
            
            self.send_file_segments(filename, client_address)
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {filename}: {e}")
            self.send_error(client_address, f"Erro ao processar arquivo: {str(e)}")
    
    def send_file_segments(self, filename: str, client_address: Tuple[str, int]):
        try:
            with open(filename, 'rb') as file:
                segment_number = 0
                
                while True:
                    data = file.read(self.MAX_PAYLOAD_SIZE)
                    if not data:
                        break
                    
                    segment = self.create_segment(segment_number, data, filename)
                    
                    self.socket.sendto(segment, client_address)
                    logger.debug(f"Segmento {segment_number} enviado para {client_address} na porta {self.port}")
                    
                    segment_number += 1
                    time.sleep(0.01)
                
                end_message = f"END_TRANSMISSION {filename}"
                self.socket.sendto(end_message.encode('utf-8'), client_address)
                logger.info(f"Transmissão do arquivo {filename} concluída na porta {self.port}")
                
        except Exception as e:
            logger.error(f"Erro ao enviar segmentos do arquivo {filename}: {e}")
    
    def create_segment(self, segment_number: int, data: bytes, filename: str) -> bytes:
        filename_bytes = filename.encode('utf-8')
        filename_length = len(filename_bytes)
        data_length = len(data)
        
        checksum = hashlib.md5(data).digest()
        
        header = struct.pack('!I16sHH', segment_number, checksum, filename_length, data_length)
        
        segment = header + filename_bytes + data
        
        return segment
    
    def handle_retransmit_request(self, filename: str, segment_number: int, client_address: Tuple[str, int]):
        try:
            if not os.path.exists(filename):
                self.send_error(client_address, f"Arquivo não encontrado: {filename}")
                return
            
            with open(filename, 'rb') as file:
                file.seek(segment_number * self.MAX_PAYLOAD_SIZE)
                data = file.read(self.MAX_PAYLOAD_SIZE)
                
                if data:
                    segment = self.create_segment(segment_number, data, filename)
                    self.socket.sendto(segment, client_address)
                    logger.info(f"Segmento {segment_number} retransmitido para {client_address} na porta {self.port}")
                else:
                    self.send_error(client_address, f"Segmento {segment_number} inválido")
                    
        except Exception as e:
            logger.error(f"Erro ao retransmitir segmento {segment_number}: {e}")
            self.send_error(client_address, f"Erro ao retransmitir: {str(e)}")
    
    def send_error(self, client_address: Tuple[str, int], error_message: str):
        try:
            error_msg = f"ERROR {error_message}"
            self.socket.sendto(error_msg.encode('utf-8'), client_address)
            logger.warning(f"Erro enviado para {client_address} na porta {self.port}: {error_message}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de erro: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Servidor UDP Multi-Porta para Transferência de Arquivos')
    parser.add_argument('--host', default='0.0.0.0', help='Host para escutar (padrão: 0.0.0.0)')
    parser.add_argument('--base-port', type=int, default=8888, help='Porta base para iniciar (padrão: 8888)')
    
    args = parser.parse_args()
    
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
