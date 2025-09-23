#!/usr/bin/env python3

import socket
import struct
import hashlib
import os
import time
import threading
from typing import Dict, List, Tuple, Optional
import logging
import sys

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
        
        self.current_file = None
        self.expected_segments = 0
        self.received_segments = {}
        self.missing_segments = set()
        self.file_info = {}
        
        self.simulate_loss = False
        self.loss_probability = 0.1
        
    def connect(self):
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
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info("Cliente desconectado")
    
    def request_file(self, filename: str, output_dir: str = "."):
        try:
            logger.info(f"Solicitando arquivo: {filename}")
            
            request = f"GET {filename}"
            self.socket.sendto(request.encode('utf-8'), self.server_address)
            
            file_info = self.receive_file_info()
            if not file_info:
                logger.error("Não foi possível obter informações do arquivo - servidor pode não estar rodando")
                return False
            
            self.current_file = filename
            self.expected_segments = file_info['num_segments']
            self.received_segments = {}
            self.missing_segments = set()
            self.file_info = file_info
            
            logger.info(f"Arquivo: {filename}")
            logger.info(f"Tamanho: {file_info['file_size']} bytes")
            logger.info(f"Segmentos esperados: {file_info['num_segments']}")
            
            receive_thread = threading.Thread(target=self.receive_file_segments)
            receive_thread.daemon = True
            receive_thread.start()
            
            receive_thread.join()
            
            if len(self.received_segments) == self.expected_segments:
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
        try:
            original_timeout = self.socket.gettimeout()
            self.socket.settimeout(3.0)
            
            data, _ = self.socket.recvfrom(4096)
            message = data.decode('utf-8')
            
            self.socket.settimeout(original_timeout)
            
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
            logger.error("Timeout ao aguardar informações do arquivo - servidor não está respondendo")
        except Exception as e:
            logger.error(f"Erro ao receber informações do arquivo: {e}")
        
        try:
            self.socket.settimeout(original_timeout)
        except:
            pass
            
        return None
    
    def receive_file_segments(self):
        try:
            while len(self.received_segments) < self.expected_segments:
                try:
                    data, _ = self.socket.recvfrom(4096)
                    
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
                            self.process_segment(data)
                            
                    except UnicodeDecodeError:
                        self.process_segment(data)
                        
                except socket.timeout:
                    logger.warning("Timeout ao aguardar segmentos")
                    break
                except Exception as e:
                    logger.error(f"Erro ao receber segmento: {e}")
                    break
            
            if len(self.received_segments) == self.expected_segments:
                logger.info(f"Todos os {self.expected_segments} segmentos recebidos com sucesso")
                return True
            else:
                missing_segments = set(range(self.expected_segments)) - set(self.received_segments.keys())
                logger.warning(f"Segmentos perdidos: {sorted(missing_segments)}")
                
                self.request_missing_segments(missing_segments)
                
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
        try:
            if len(data) < 24:
                logger.warning("Segmento muito pequeno, ignorando")
                return
            
            header = data[:24]
            segment_number, checksum, filename_length, data_length = struct.unpack('!I16sHH', header)
            
            filename_start = 24
            filename_end = filename_start + filename_length
            data_start = filename_end
            
            if len(data) < data_start + data_length:
                logger.warning("Segmento incompleto, ignorando")
                return
            
            filename = data[filename_start:filename_end].decode('utf-8')
            segment_data = data[data_start:data_start + data_length]
            
            if self.simulate_loss and self.should_discard_segment():
                logger.info(f"Simulando perda do segmento {segment_number}")
                return
            
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
        calculated_checksum = hashlib.md5(data).digest()
        return calculated_checksum == expected_checksum
    
    def should_discard_segment(self) -> bool:
        import random
        return random.random() < self.loss_probability
    
    def check_missing_segments(self):
        self.missing_segments = set(range(self.expected_segments)) - set(self.received_segments.keys())
        
        if self.missing_segments:
            logger.warning(f"Segmentos perdidos: {sorted(self.missing_segments)}")
            self.request_missing_segments()
    
    def request_missing_segments(self, missing_segments: set):
        for segment_number in missing_segments:
            try:
                request = f"RETRANSMIT {self.current_file} {segment_number}"
                self.socket.sendto(request.encode('utf-8'), self.server_address)
                logger.info(f"Solicitando retransmissão do segmento {segment_number}")
                
                try:
                    self.socket.settimeout(5.0)
                    retransmitted_data, _ = self.socket.recvfrom(4096)
                    
                    self.process_segment(retransmitted_data)
                    logger.info(f"Segmento {segment_number} retransmitido com sucesso")
                    
                except socket.timeout:
                    logger.error(f"Timeout na retransmissão do segmento {segment_number}")
                    
            except Exception as e:
                logger.error(f"Erro ao solicitar retransmissão do segmento {segment_number}: {e}")
        
        self.socket.settimeout(self.timeout)
    
    def save_file(self, output_filename: str = None) -> bool:
        try:
            if not output_filename:
                output_filename = self.current_file
            
            if len(self.received_segments) != self.expected_segments:
                logger.error(f"Arquivo incompleto: {len(self.received_segments)}/{self.expected_segments} segmentos")
                return False
            
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
        self.simulate_loss = True
        self.loss_probability = probability
        logger.info(f"Simulação de perda habilitada com probabilidade {probability}")

def main():
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
    
    if args.server_port <= 1024:
        print("Erro: Porta deve ser maior que 1024")
        sys.exit(1)
    
    client = UDPClient(args.server_host, args.server_port, args.timeout)
    
    try:
        if not client.connect():
            print("Erro: Falha ao conectar ao servidor")
            sys.exit(1)
        
        if args.simulate_loss:
            client.enable_loss_simulation(args.loss_probability)
        
        success = client.request_file(args.filename, args.output_dir)
        
        if success:
            print(f"Arquivo {args.filename} recebido com sucesso!")
            sys.exit(0)
        else:
            print(f"Falha ao receber arquivo {args.filename}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado: {e}")
        sys.exit(1)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
