#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import hashlib
import os
import sys
import time
import signal
from datetime import datetime

class TCPServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}
        self.client_counter = 0
        self.running = False
        self.server_files_dir = "server_files"
        
        if not os.path.exists(self.server_files_dir):
            os.makedirs(self.server_files_dir)
    
    def signal_handler(self, signum, frame):
        """Handler para capturar Ctrl+C e outros sinais"""
        print(f"\n[INFO] Sinal {signum} recebido - encerrando servidor...")
        self.running = False
    
    def calculate_sha256(self, file_path):
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"[ERRO] Erro ao calcular SHA-256: {e}")
            return None
    
    def send_message(self, client_socket, message):
        try:
            message_bytes = message.encode('utf-8')
            message_length = len(message_bytes)
            client_socket.send(message_length.to_bytes(4, byteorder='big'))
            client_socket.send(message_bytes)
        except Exception as e:
            print(f"[ERRO] Erro ao enviar mensagem: {e}")
    
    def receive_message(self, client_socket):
        try:
            length_bytes = client_socket.recv(4)
            if not length_bytes:
                return None
            
            message_length = int.from_bytes(length_bytes, byteorder='big')
            
            message_bytes = b''
            while len(message_bytes) < message_length:
                chunk = client_socket.recv(message_length - len(message_bytes))
                if not chunk:
                    return None
                message_bytes += chunk
            
            return message_bytes.decode('utf-8')
        except Exception as e:
            print(f"[ERRO] Erro ao receber mensagem: {e}")
            return None
    
    def send_file(self, client_socket, file_path):
        try:
            full_path = os.path.join(self.server_files_dir, file_path)
            
            if not os.path.exists(full_path):
                self.send_message(client_socket, "ARQUIVO_NAO_ENCONTRADO")
                return
            
            file_size = os.path.getsize(full_path)
            file_sha256 = self.calculate_sha256(full_path)
            
            if file_sha256 is None:
                self.send_message(client_socket, "ERRO")
                return
            
            metadata = f"OK|{file_path}|{file_size}|{file_sha256}"
            self.send_message(client_socket, metadata)
            
            print(f"[INFO] Metadados enviados. Aguardando confirmação do cliente...")
            
            # Aguardar confirmação do cliente antes de enviar o arquivo
            try:
                client_socket.settimeout(10.0)  # Timeout para confirmação
                confirmation = self.receive_message(client_socket)
                if confirmation != "READY":
                    print(f"[ERRO] Confirmação inválida do cliente: {confirmation}")
                    return
                print(f"[INFO] Cliente confirmou. Enviando arquivo: {file_path} ({file_size} bytes)")
            except Exception as e:
                print(f"[ERRO] Erro ao aguardar confirmação do cliente: {e}")
                return
            
            with open(full_path, 'rb') as f:
                bytes_sent = 0
                last_progress_time = time.time()
                
                while bytes_sent < file_size:
                    # Usar chunks menores para melhor sincronização
                    chunk_size = min(16384, file_size - bytes_sent)  # 16KB chunks (menor)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # Enviar chunk completo
                    total_sent = 0
                    while total_sent < len(chunk):
                        try:
                            sent = client_socket.send(chunk[total_sent:])
                            if sent == 0:
                                print(f"[ERRO] Conexão quebrada durante envio. Enviados: {bytes_sent}/{file_size} bytes")
                                raise RuntimeError("Socket connection broken")
                            total_sent += sent
                        except socket.error as e:
                            print(f"[ERRO] Erro de socket durante envio: {e}")
                            print(f"[DEBUG] Bytes enviados até o erro: {bytes_sent}/{file_size}")
                            raise
                    
                    bytes_sent += len(chunk)
                    
                    # Controle de fluxo: pequena pausa a cada 512KB enviado
                    if bytes_sent % (512 * 1024) == 0 and bytes_sent > 0:
                        time.sleep(0.005)  # 5ms de pausa a cada 512KB
                    
                    # Mostrar progresso para arquivos grandes
                    current_time = time.time()
                    if file_size > 1024 * 1024 and current_time - last_progress_time >= 1.0:
                        progress = (bytes_sent / file_size) * 100
                        print(f"[INFO] Servidor - Progresso: {progress:.1f}% ({bytes_sent}/{file_size} bytes)")
                        last_progress_time = current_time
                
                # Debug: verificar se enviou tudo
                print(f"[DEBUG] Servidor - Envio completo: {bytes_sent}/{file_size} bytes")
            
            print(f"[INFO] Arquivo {file_path} enviado com sucesso!")
            
        except Exception as e:
            print(f"[ERRO] Erro ao enviar arquivo: {e}")
            self.send_message(client_socket, "ERRO")
    
    def broadcast_chat_message(self, sender_id, message):
        if sender_id == 0:
            chat_message = f"CHAT_SERVER|{message}"
        else:
            chat_message = f"CHAT_CLIENT|Cliente {sender_id}: {message}"
        
        disconnected_clients = []
        
        for client_id, client_info in self.clients.items():
            # Para mensagens do servidor (sender_id = 0), enviar para todos os clientes
            # Para mensagens de clientes, enviar para todos exceto o remetente
            if sender_id == 0 or client_id != sender_id:
                try:
                    self.send_message(client_info['socket'], chat_message)
                    print(f"[DEBUG] Mensagem enviada para Cliente {client_id}: {chat_message}")
                except Exception as e:
                    print(f"[ERRO] Falha ao enviar para Cliente {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            if client_id in self.clients:
                del self.clients[client_id]
    
    def handle_client(self, client_socket, client_address):
        self.client_counter += 1
        client_id = self.client_counter
        
        self.clients[client_id] = {
            'socket': client_socket,
            'address': client_address,
            'connected_at': datetime.now()
        }
        
        print(f"[INFO] Cliente {client_id} conectado de {client_address}")
        
        try:
            while self.running:
                request = self.receive_message(client_socket)
                
                if not request:
                    break
                
                print(f"[INFO] Cliente {client_id} enviou: {request}")
                
                if request.upper() == "SAIR":
                    print(f"[INFO] Cliente {client_id} solicitou desconexão")
                    self.send_message(client_socket, "OK")
                    break
                
                elif request.upper().startswith("ARQUIVO:"):
                    file_name = request[8:].strip()
                    print(f"[INFO] Cliente {client_id} solicitou arquivo: {file_name}")
                    self.send_file(client_socket, file_name)
                
                elif request.upper().startswith("CHAT:"):
                    chat_message = request[5:].strip()
                    print(f"[CHAT] Cliente {client_id}: {chat_message}")
                    
                    self.send_message(client_socket, "OK")
                    self.broadcast_chat_message(client_id, chat_message)
                
                else:
                    print(f"[AVISO] Requisição inválida do Cliente {client_id}: {request}")
                    self.send_message(client_socket, "ERRO")
        
        except Exception as e:
            print(f"[ERRO] Erro na comunicação com Cliente {client_id}: {e}")
        
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            
            try:
                client_socket.close()
            except:
                pass
            
            print(f"[INFO] Cliente {client_id} desconectado")
    
    def server_chat_input(self):
        """Thread para processar comandos do servidor de forma não-bloqueante"""
        while self.running:
            try:
                # Implementação simples e compatível com todas as plataformas
                import sys
                
                # Usar uma abordagem mais simples que funciona em Windows e Linux
                if sys.platform == 'win32':
                    # Windows - verificar se há input disponível
                    try:
                        import msvcrt
                        if msvcrt.kbhit():
                            line = input()
                            if line.strip() and self.running:
                                self.process_server_command(line.strip())
                        else:
                            time.sleep(0.1)  # Pequena pausa
                    except ImportError:
                        # Fallback se msvcrt não disponível
                        time.sleep(0.5)
                    except (EOFError, KeyboardInterrupt):
                        self.running = False
                        break
                else:
                    # Linux/Mac - usar select com timeout
                    try:
                        import select
                        ready, _, _ = select.select([sys.stdin], [], [], 0.5)
                        if ready and self.running:
                            line = input()
                            if line.strip():
                                self.process_server_command(line.strip())
                    except (ImportError, OSError):
                        # Fallback se select não funcionar
                        time.sleep(0.5)
                    except (EOFError, KeyboardInterrupt):
                        self.running = False
                        break
                        
            except EOFError:
                break
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f"[DEBUG] Erro na thread de chat (não crítico): {e}")
                # Não quebrar o loop por erros não críticos
                time.sleep(0.5)
    
    def process_server_command(self, command):
        """Processa comandos do servidor"""
        try:
            if command.lower() == '/quit':
                self.running = False
            elif command.lower() == '/status':
                print(f"[STATUS] Clientes conectados: {len(self.clients)}")
                for client_id, info in self.clients.items():
                    print(f"  - Cliente {client_id}: {info['address']} (conectado em {info['connected_at'].strftime('%H:%M:%S')})")
            elif command.lower() == '/help':
                print("[AJUDA] Comandos disponíveis:")
                print("  /quit - Encerra o servidor")
                print("  /status - Mostra clientes conectados")
                print("  /help - Mostra esta ajuda")
                print("  Qualquer outra mensagem será enviada como chat para todos os clientes")
            else:
                print(f"[CHAT] Servidor: {command}")
                self.broadcast_chat_message(0, command)
        except Exception as e:
            print(f"[ERRO] Erro ao processar comando: {e}")
    
    def start_server(self):
        try:
            # Configurar handler para Ctrl+C
            signal.signal(signal.SIGINT, self.signal_handler)
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, self.signal_handler)
            
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            # Configurar timeout para permitir interrupção
            self.server_socket.settimeout(1.0)  # Timeout de 1 segundo
            
            self.running = True
            
            print(f"[INFO] Servidor TCP iniciado em {self.host}:{self.port}")
            print(f"[INFO] Diretório de arquivos: {os.path.abspath(self.server_files_dir)}")
            print("[INFO] Aguardando conexões...")
            print("[INFO] Digite mensagens para enviar chat ou /help para comandos")
            print("[INFO] Pressione Ctrl+C para parar o servidor")
            print("-" * 60)
            
            chat_thread = threading.Thread(target=self.server_chat_input, daemon=True)
            chat_thread.start()
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                
                except socket.timeout:
                    # Timeout é normal - permite verificar self.running
                    continue
                
                except socket.error:
                    if self.running:
                        print("[ERRO] Erro ao aceitar conexão")
                    break
        
        except Exception as e:
            print(f"[ERRO] Erro ao iniciar servidor: {e}")
        
        finally:
            self.stop_server()
    
    def stop_server(self):
        print("\n[INFO] Encerrando servidor...")
        self.running = False
        
        for client_id, client_info in list(self.clients.items()):
            try:
                client_info['socket'].close()
            except:
                pass
        
        self.clients.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("[INFO] Servidor encerrado")

def main():
    print("=== Servidor TCP Multithread ===")
    print("Trabalho 2 - Redes de Computadores")
    print()
    
    host = input("Digite o endereço IP do servidor (Enter para localhost): ").strip()
    if not host:
        host = 'localhost'
    
    try:
        port = input("Digite a porta do servidor (Enter para 8888): ").strip()
        if not port:
            port = 8888
        else:
            port = int(port)
            
        if port <= 1024:
            print("[AVISO] Recomenda-se usar porta > 1024")
    except ValueError:
        print("[ERRO] Porta inválida, usando 8888")
        port = 8888
    
    server = TCPServer(host, port)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n[INFO] Interrompido pelo usuário")
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
    finally:
        # Garantir que o servidor seja sempre parado
        if server.running:
            server.stop_server()

if __name__ == "__main__":
    main()