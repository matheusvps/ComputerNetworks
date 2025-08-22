#!/usr/bin/env python3
"""
Cliente UDP para Transferência de Arquivos Confiável
Implementa recepção de arquivos com verificação de integridade e retransmissão
"""

import socket
import struct
import hashlib
import os
import time
import threading
from typing import Dict, List, Tuple, Optional
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UDPClient:
    def __init__(self, server_host: str, server_port: int, timeout: float = 5.0):
        self.server_host = server_host
        self.server_port = server_port
        self.server_address = (server_host, server_port)
        self.timeout = timeout
        self.socket = None
        self.running = False
        
        # Estado da transferência
        self.current_file = None
        self.expected_segments = 0
        self.received_segments = {}
        self.missing_segments = set()
        self.file_info = {}
        
        # Configurações de simulação de perda
        self.simulate_loss = False
        self.loss_probability = 0.1  # 10% de chance de perda
        
    def connect(self):
        """Conecta ao servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
            self.running = True
            
            logger.info(f"Cliente conectado ao servidor {self.server_host}:{self.server_port}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do servidor"""
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info("Cliente desconectado")
    
    def request_file(self, filename: str, output_dir: str = "."):
        """Solicita um arquivo do servidor"""
        try:
            logger.info(f"Solicitando arquivo: {filename}")
            
            # Envia requisição GET
            request = f"GET {filename}"
            self.socket.sendto(request.encode('utf-8'), self.server_address)
            
            # Aguarda informações do arquivo
            file_info = self.receive_file_info()
            if not file_info:
                logger.error("Não foi possível obter informações do arquivo")
                return False
            
            # Inicializa estado da transferência
            self.current_file = filename
            self.expected_segments = file_info['num_segments']
            self.received_segments = {}
            self.missing_segments = set()
            self.file_info = file_info
            
            logger.info(f"Arquivo: {filename}")
            logger.info(f"Tamanho: {file_info['file_size']} bytes")
            logger.info(f"Segmentos esperados: {file_info['num_segments']}")
            
            # Inicia thread de recepção
            receive_thread = threading.Thread(target=self.receive_file_segments)
            receive_thread.daemon = True
            receive_thread.start()
            
            # Aguarda conclusão da transferência
            receive_thread.join()
            
            # Salva o arquivo
            if len(self.received_segments) == self.expected_segments:
                # Reconstrói e salva o arquivo
                if self.save_file(os.path.join(output_dir, filename)):
                    logger.info(f"Arquivo {filename} recebido com sucesso!")
                    return True
                else:
                    logger.error("Falha ao salvar arquivo")
                    return False
            else:
                logger.error("Arquivo incompleto")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao solicitar arquivo: {e}")
            return False
    
    def receive_file_info(self) -> Optional[Dict]:
        """Recebe informações do arquivo do servidor"""
        try:
            data, _ = self.socket.recvfrom(4096)
            message = data.decode('utf-8')
            
            if message.startswith('FILE_INFO '):
                parts = message.split(' ')
                if len(parts) >= 4:
                    return {
                        'filename': parts[1],
                        'file_size': int(parts[2]),
                        'num_segments': int(parts[3])
                    }
            elif message.startswith('ERROR '):
                error_msg = message[6:]
                logger.error(f"Erro do servidor: {error_msg}")
                return None
                
        except socket.timeout:
            logger.error("Timeout ao aguardar informações do arquivo")
        except Exception as e:
            logger.error(f"Erro ao receber informações do arquivo: {e}")
        
        return None
    
    def receive_file_segments(self):
        """Recebe todos os segmentos do arquivo"""
        try:
            while len(self.received_segments) < self.expected_segments:
                try:
                    data, _ = self.socket.recvfrom(4096)
                    
                    # Verifica se é uma mensagem de controle (texto) ou segmento de dados (binário)
                    try:
                        message = data.decode('utf-8')
                        
                        if message.startswith('END_TRANSMISSION'):
                            logger.info("Recebido sinal de fim de transmissão")
                            break
                        elif message.startswith('ERROR '):
                            error_msg = message[6:]
                            logger.error(f"Erro do servidor: {error_msg}")
                            break
                        else:
                            # Se não for mensagem de controle, deve ser um segmento de dados
                            # Processa como segmento binário
                            self.process_segment(data)
                            
                    except UnicodeDecodeError:
                        # Dados binários - processa como segmento
                        self.process_segment(data)
                        
                except socket.timeout:
                    logger.warning("Timeout ao aguardar segmentos")
                    break
                except Exception as e:
                    logger.error(f"Erro ao receber segmento: {e}")
                    break
            
            # Verifica se recebeu todos os segmentos
            if len(self.received_segments) == self.expected_segments:
                logger.info(f"Todos os {self.expected_segments} segmentos recebidos com sucesso")
                return True
            else:
                missing_segments = set(range(self.expected_segments)) - set(self.received_segments.keys())
                logger.warning(f"Segmentos perdidos: {sorted(missing_segments)}")
                
                # Tenta solicitar retransmissão dos segmentos perdidos
                self.request_missing_segments(missing_segments)
                
                # Verifica novamente após retransmissão
                if len(self.received_segments) == self.expected_segments:
                    logger.info("Todos os segmentos recebidos após retransmissão")
                    return True
                else:
                    logger.error("Arquivo incompleto")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao receber segmentos: {e}")
            return False
    
    def process_segment(self, data: bytes):
        """Processa um segmento recebido"""
        try:
            # Extrai cabeçalho - deve ser 24 bytes como definido no servidor
            if len(data) < 24:  # Tamanho mínimo do cabeçalho (24 bytes)
                logger.warning("Segmento muito pequeno, ignorando")
                return
            
            header = data[:24]
            segment_number, checksum, filename_length, data_length = struct.unpack('!I16sHH', header)
            
            # Extrai nome do arquivo e dados
            filename_start = 24
            filename_end = filename_start + filename_length
            data_start = filename_end
            
            if len(data) < data_start + data_length:
                logger.warning("Segmento incompleto, ignorando")
                return
            
            filename = data[filename_start:filename_end].decode('utf-8')
            segment_data = data[data_start:data_start + data_length]
            
            # Verifica se deve simular perda
            if self.simulate_loss and self.should_discard_segment():
                logger.info(f"Simulando perda do segmento {segment_number}")
                return
            
            # Verifica checksum
            if self.verify_checksum(segment_data, checksum):
                self.received_segments[segment_number] = {
                    'data': segment_data,
                    'checksum': checksum,
                    'filename': filename
                }
                logger.debug(f"Segmento {segment_number} recebido e verificado")
            else:
                logger.warning(f"Checksum inválido para segmento {segment_number}")
                
        except Exception as e:
            logger.error(f"Erro ao processar segmento: {e}")
    
    def verify_checksum(self, data: bytes, expected_checksum: bytes) -> bool:
        """Verifica o checksum dos dados"""
        calculated_checksum = hashlib.md5(data).digest()
        return calculated_checksum == expected_checksum
    
    def should_discard_segment(self) -> bool:
        """Decide se deve descartar um segmento (simulação de perda)"""
        import random
        return random.random() < self.loss_probability
    
    def check_missing_segments(self):
        """Verifica quais segmentos estão faltando"""
        self.missing_segments = set(range(self.expected_segments)) - set(self.received_segments.keys())
        
        if self.missing_segments:
            logger.warning(f"Segmentos perdidos: {sorted(self.missing_segments)}")
            self.request_missing_segments()
    
    def request_missing_segments(self, missing_segments: set):
        """Solicita retransmissão dos segmentos perdidos"""
        for segment_number in missing_segments:
            try:
                request = f"RETRANSMIT {self.current_file} {segment_number}"
                self.socket.sendto(request.encode('utf-8'), self.server_address)
                logger.info(f"Solicitando retransmissão do segmento {segment_number}")
                
                # Aguarda retransmissão com timeout
                try:
                    self.socket.settimeout(5.0)  # 5 segundos de timeout
                    retransmitted_data, _ = self.socket.recvfrom(4096)
                    
                    # Processa segmento retransmitido
                    self.process_segment(retransmitted_data)
                    logger.info(f"Segmento {segment_number} retransmitido com sucesso")
                    
                except socket.timeout:
                    logger.error(f"Timeout na retransmissão do segmento {segment_number}")
                    
            except Exception as e:
                logger.error(f"Erro ao solicitar retransmissão do segmento {segment_number}: {e}")
        
        # Restaura timeout original
        self.socket.settimeout(self.timeout)
    
    def save_file(self, output_filename: str = None) -> bool:
        """Reconstrói o arquivo a partir dos segmentos recebidos"""
        try:
            if not output_filename:
                output_filename = self.current_file
            
            # Verifica se todos os segmentos foram recebidos
            if len(self.received_segments) != self.expected_segments:
                logger.error(f"Arquivo incompleto: {len(self.received_segments)}/{self.expected_segments} segmentos")
                return False
            
            # Reconstrói arquivo na ordem correta
            with open(output_filename, 'wb') as output_file:
                for segment_number in range(self.expected_segments):
                    if segment_number in self.received_segments:
                        segment_data = self.received_segments[segment_number]['data']
                        output_file.write(segment_data)
                    else:
                        logger.error(f"Segmento {segment_number} não encontrado")
                        return False
            
            logger.info(f"Arquivo salvo com sucesso: {output_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo: {e}")
            return False
    
    def enable_loss_simulation(self, probability: float = 0.1):
        """Habilita simulação de perda de segmentos"""
        self.simulate_loss = True
        self.loss_probability = probability
        logger.info(f"Simulação de perda habilitada com probabilidade {probability}")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cliente UDP para Transferência de Arquivos')
    parser.add_argument('server_host', help='Endereço IP do servidor')
    parser.add_argument('server_port', type=int, help='Porta do servidor')
    parser.add_argument('filename', help='Nome do arquivo a solicitar')
    parser.add_argument('--output-dir', default='.', help='Diretório de saída (padrão: .)')
    parser.add_argument('--timeout', type=float, default=5.0, help='Timeout em segundos (padrão: 5.0)')
    parser.add_argument('--simulate-loss', action='store_true', help='Habilita simulação de perda')
    parser.add_argument('--loss-probability', type=float, default=0.1, help='Probabilidade de perda (padrão: 0.1)')
    
    args = parser.parse_args()
    
    # Verifica se a porta é válida
    if args.server_port <= 1024:
        print("Erro: Porta deve ser maior que 1024")
        return
    
    client = UDPClient(args.server_host, args.server_port, args.timeout)
    
    try:
        if not client.connect():
            return
        
        if args.simulate_loss:
            client.enable_loss_simulation(args.loss_probability)
        
        success = client.request_file(args.filename, args.output_dir)
        
        if success:
            print(f"Arquivo {args.filename} recebido com sucesso!")
        else:
            print(f"Falha ao receber arquivo {args.filename}")
            
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
