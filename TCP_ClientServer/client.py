#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import hashlib
import os
import sys
import time
import queue
import signal
from datetime import datetime

class TCPClient:
    def __init__(self):
        self.client_socket = None
        self.connected = False
        self.downloads_dir = "client_downloads"
        self.file_response_queue = queue.Queue()
        self.download_cancelled = False
        self.downloading = False
        
        if not os.path.exists(self.downloads_dir):
            os.makedirs(self.downloads_dir)
    
    def calculate_sha256(self, file_path):
        sha256_hash = hashlib.sha256()
        try:
            print("[INFO] Verificando integridade do arquivo...")
            file_size = os.path.getsize(file_path)
            bytes_processed = 0
            last_progress_time = time.time()
            
            with open(file_path, "rb") as f:
                while True:
                    try:
                        chunk = f.read(2 * 1024 * 1024)  # Chunks de 2MB
                        if not chunk:
                            break
                        sha256_hash.update(chunk)
                        bytes_processed += len(chunk)
                        
                        # Mostrar progresso frequente para arquivos grandes
                        current_time = time.time()
                        if file_size > 5 * 1024 * 1024 and current_time - last_progress_time > 1.0:  # A cada segundo
                            progress = (bytes_processed / file_size) * 100
                            print(f"[INFO] Verificação SHA-256: {progress:.1f}%")
                            last_progress_time = current_time
                    
                    except KeyboardInterrupt:
                        print("\n[INFO] Verificação cancelada pelo usuário")
                        return None
            
            result = sha256_hash.hexdigest()
            print("[INFO] Verificação SHA-256 concluída")
            return result
        except KeyboardInterrupt:
            print("\n[INFO] Verificação cancelada pelo usuário")
            return None
        except Exception as e:
            print(f"[ERRO] Erro ao calcular SHA-256: {e}")
            return None
    
    def send_message(self, message):
        try:
            message_bytes = message.encode('utf-8')
            message_length = len(message_bytes)
            self.client_socket.send(message_length.to_bytes(4, byteorder='big'))
            self.client_socket.send(message_bytes)
        except Exception as e:
            print(f"[ERRO] Erro ao enviar mensagem: {e}")
            self.connected = False
    
    def receive_message(self):
        try:
            # Configurar timeout adequado baseado no estado
            original_timeout = self.client_socket.gettimeout()
            if not self.downloading:
                self.client_socket.settimeout(5.0)
            # Durante download, manter o timeout atual (será configurado pela thread de escuta)
            
            length_bytes = self.client_socket.recv(4)
            if not length_bytes:
                return None
            
            message_length = int.from_bytes(length_bytes, byteorder='big')
            
            message_bytes = b''
            while len(message_bytes) < message_length:
                chunk = self.client_socket.recv(message_length - len(message_bytes))
                if not chunk:
                    return None
                message_bytes += chunk
            
            # Restaurar timeout original
            if not self.downloading:
                self.client_socket.settimeout(original_timeout)
            
            return message_bytes.decode('utf-8')
        except socket.timeout:
            # Timeout é normal quando não há mensagens
            return None
        except Exception as e:
            if self.connected:  # Só mostrar erro se ainda estiver conectado
                print(f"[ERRO] Erro ao receber mensagem: {e}")
                self.connected = False
            return None
    
    def receive_file(self, file_name, file_size, expected_sha256):
        try:
            file_path = os.path.join(self.downloads_dir, file_name)
            
            print(f"[INFO] Recebendo arquivo: {file_name} ({file_size} bytes)")
            print(f"[INFO] SHA-256 esperado: {expected_sha256}")
            print("[INFO] Pressione Ctrl+C para cancelar o download")
            
            # Resetar flag de cancelamento
            self.download_cancelled = False
            
            # Configurar socket para downloads grandes
            original_timeout = self.client_socket.gettimeout()
            self.client_socket.settimeout(10.0)  # Timeout adequado (10s)
            
            print("[INFO] Aguardando início dos dados do arquivo...")
            
            with open(file_path, 'wb') as f:
                bytes_received = 0
                last_progress_time = time.time()
                last_bytes_received = 0
                consecutive_empty_chunks = 0
                max_empty_chunks = 50  # Máximo de chunks vazios consecutivos
                
                while bytes_received < file_size and not self.download_cancelled:
                    try:
                        remaining = file_size - bytes_received
                        # Usar chunks menores para melhor controle
                        chunk_size = min(16384, remaining)  # 16KB chunks (sincronizado com servidor)
                        
                        chunk = self.client_socket.recv(chunk_size)
                        
                        if not chunk:
                            consecutive_empty_chunks += 1
                            print(f"[DEBUG] Chunk vazio #{consecutive_empty_chunks}. Bytes recebidos: {bytes_received}/{file_size}")
                            
                            if consecutive_empty_chunks >= max_empty_chunks:
                                print(f"[ERRO] Muitos chunks vazios consecutivos ({consecutive_empty_chunks})")
                                print(f"[DEBUG] Possível desconexão ou fim prematuro dos dados")
                                return False
                            
                            # Pausa pequena antes de tentar novamente
                            time.sleep(0.01)  # Pausa menor
                            continue
                        
                        # Reset contador de chunks vazios quando receber dados
                        consecutive_empty_chunks = 0
                        
                        f.write(chunk)
                        bytes_received += len(chunk)
                        
                        # Mostrar progresso frequente
                        current_time = time.time()
                        if current_time - last_progress_time >= 1.0:  # Atualizar a cada segundo
                            progress = (bytes_received / file_size) * 100
                            bytes_per_sec = (bytes_received - last_bytes_received) / (current_time - last_progress_time)
                            speed_mbps = bytes_per_sec / (1024 * 1024)  # MB/s
                            
                            print(f"[INFO] Progresso: {progress:.1f}% ({bytes_received}/{file_size} bytes) - {speed_mbps:.2f} MB/s")
                            
                            last_progress_time = current_time
                            last_bytes_received = bytes_received
                    
                    except socket.timeout:
                        print(f"[DEBUG] Timeout no socket. Bytes recebidos: {bytes_received}/{file_size}")
                        # Verificar se ainda há dados para receber
                        if bytes_received < file_size:
                            consecutive_empty_chunks += 1
                            if consecutive_empty_chunks >= max_empty_chunks:
                                print(f"[ERRO] Timeout excessivo - download pode ter travado")
                                return False
                        continue
                    
                    except KeyboardInterrupt:
                        print("\n[INFO] Download cancelado pelo usuário")
                        self.download_cancelled = True
                        return False
                    
                    except Exception as e:
                        print(f"[ERRO] Erro durante recepção: {e}")
                        print(f"[DEBUG] Bytes recebidos até o erro: {bytes_received}/{file_size}")
                        return False
            
            # Debug: verificar se saiu do loop normalmente
            print(f"[DEBUG] Saiu do loop de download. Bytes recebidos: {bytes_received}/{file_size}")
            print(f"[DEBUG] Download cancelado: {self.download_cancelled}")
            
            # Restaurar timeout original
            self.client_socket.settimeout(original_timeout)
            
            # Verificar se foi cancelado
            if self.download_cancelled:
                print("[INFO] Download foi cancelado")
                return False
            
            print(f"[INFO] Arquivo salvo em: {os.path.abspath(file_path)}")
            
            calculated_sha256 = self.calculate_sha256(file_path)
            
            if calculated_sha256 is None:
                print("[AVISO] Não foi possível verificar a integridade do arquivo")
                print("[INFO] Arquivo baixado, mas verificação SHA-256 falhou")
                print("[DEBUG] Retornando True do receive_file (download completo, verificação falhou)")
                return True  # Arquivo foi baixado completamente, mesmo sem verificação
            
            print(f"[INFO] SHA-256 calculado: {calculated_sha256}")
            
            if calculated_sha256.lower() == expected_sha256.lower():
                print("[SUCESSO] Arquivo recebido com integridade verificada!")
                print("[DEBUG] Retornando True do receive_file")
                return True
            else:
                print("[ERRO] Falha na verificação de integridade! O arquivo pode estar corrompido.")
                print(f"[ERRO] Esperado: {expected_sha256}")
                print(f"[ERRO] Calculado: {calculated_sha256}")
                print("[AVISO] Arquivo foi baixado completamente, mas pode estar corrompido")
                print("[DEBUG] Retornando True do receive_file (download completo, hash diferente)")
                return True  # Arquivo foi baixado, deixar usuário decidir se quer usar
        
        except Exception as e:
            print(f"[ERRO] Erro ao receber arquivo: {e}")
            print("[DEBUG] Retornando False do receive_file (exception)")
            return False
        finally:
            # Garantir que o timeout seja sempre restaurado
            try:
                if 'original_timeout' in locals():
                    self.client_socket.settimeout(original_timeout)
            except:
                pass
    
    def listen_for_messages(self):
        while self.connected:
            try:
                # Durante download, NÃO escutar mensagens para evitar interferência
                if self.downloading:
                    time.sleep(0.1)
                    continue
                
                message = self.receive_message()
                if not message:
                    break
                
                print(f"[DEBUG] Mensagem recebida: {message}")  # Debug log
                
                if message.startswith("CHAT_SERVER|"):
                    chat_message = message[12:]
                    print(f"\n[CHAT] Servidor: {chat_message}")
                    print("Digite sua opção: ", end="", flush=True)
                
                elif message.startswith("CHAT_CLIENT|"):
                    chat_message = message[12:]
                    print(f"\n[CHAT] {chat_message}")
                    print("Digite sua opção: ", end="", flush=True)
                
                elif message == "OK":
                    # Resposta de confirmação do servidor - não precisa exibir nada
                    pass
                
                elif (message.startswith("OK|") or 
                      message == "ARQUIVO_NAO_ENCONTRADO" or 
                      message == "ERRO"):
                    # Mensagens relacionadas a arquivos - colocar na fila
                    self.file_response_queue.put(message)
                
                else:
                    print(f"[DEBUG] Mensagem não reconhecida: {message}")  # Debug log
            
            except Exception as e:
                if self.connected:
                    print(f"[ERRO] Erro ao escutar mensagens: {e}")
                break
    
    def connect_to_server(self, host, port):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            self.connected = True
            
            print(f"[INFO] Conectado ao servidor {host}:{port}")
            
            listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            listen_thread.start()
            
            return True
        
        except Exception as e:
            print(f"[ERRO] Erro ao conectar ao servidor: {e}")
            return False
    
    def signal_handler(self, signum, frame):
        """Handler para capturar Ctrl+C durante downloads"""
        print("\n[INFO] Sinal de interrupção recebido - cancelando download...")
        self.download_cancelled = True
    
    def wait_for_file_response(self, timeout=30):
        """Aguarda resposta específica do servidor para solicitação de arquivo"""
        try:
            # Configurar timeout temporário para receber apenas a resposta inicial
            original_timeout = self.client_socket.gettimeout()
            self.client_socket.settimeout(5.0)
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    message = self.receive_message()
                    if message and (message.startswith("OK|") or 
                                  message == "ARQUIVO_NAO_ENCONTRADO" or 
                                  message == "ERRO"):
                        # Restaurar timeout original
                        self.client_socket.settimeout(original_timeout)
                        return message
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[DEBUG] Erro ao aguardar resposta: {e}")
                    break
            
            # Restaurar timeout original
            self.client_socket.settimeout(original_timeout)
            return None
        except Exception as e:
            print(f"[ERRO] Erro ao aguardar resposta do servidor: {e}")
            return None

    def request_file(self, file_name):
        try:
            # Configurar handler para Ctrl+C
            old_handler = signal.signal(signal.SIGINT, self.signal_handler)
            
            request = f"ARQUIVO:{file_name}"
            self.send_message(request)
            
            if not self.connected:
                return
            
            print("[INFO] Aguardando resposta do servidor...")
            
            # Aguardar resposta diretamente do socket (sem usar a fila)
            response = self.wait_for_file_response(30)
            
            if not response:
                print("[ERRO] Timeout ao aguardar resposta do servidor")
                print("[INFO] O servidor pode estar ocupado com outro cliente")
                print("[INFO] Tente novamente em alguns segundos")
                return
            
            print(f"[DEBUG] Resposta recebida: {response}")
            
            if response == "ARQUIVO_NAO_ENCONTRADO":
                print(f"[ERRO] Arquivo '{file_name}' não encontrado no servidor")
                return
            
            elif response == "ERRO":
                print("[ERRO] Erro no servidor ao processar solicitação de arquivo")
                return
            
            elif response.startswith("OK|"):
                parts = response.split("|")
                if len(parts) != 4:
                    print("[ERRO] Resposta inválida do servidor")
                    return
                
                _, received_file_name, file_size_str, expected_sha256 = parts
                
                try:
                    file_size = int(file_size_str)
                except ValueError:
                    print("[ERRO] Tamanho de arquivo inválido recebido do servidor")
                    return
                
                print("[DEBUG] Chamando receive_file...")
                print(f"[DEBUG] Arquivo: {received_file_name}, Tamanho: {file_size} bytes")
                
                # Enviar confirmação para o servidor antes de começar o download
                print("[INFO] Enviando confirmação para o servidor...")
                self.send_message("READY")
                
                # AGORA sim, sinalizar que está fazendo download (após confirmação)
                self.downloading = True
                
                # Começar recepção do arquivo
                success = self.receive_file(received_file_name, file_size, expected_sha256)
                self.downloading = False  # Finalizar sinalização
                print(f"[DEBUG] receive_file retornou: {success}")
                
                if success:
                    print(f"[SUCESSO] Arquivo '{file_name}' baixado com sucesso!")
                else:
                    print(f"[ERRO] Falha ao baixar arquivo '{file_name}'")
                
                print("[DEBUG] Retornando do request_file")
                return  # Retorna ao menu principal após completar o download
            
            else:
                print(f"[ERRO] Resposta inesperada do servidor: {response}")
                return  # Retorna ao menu principal em caso de erro
        
        except KeyboardInterrupt:
            print("\n[INFO] Download cancelado pelo usuário")
            self.download_cancelled = True
            return
        except Exception as e:
            print(f"[ERRO] Erro ao solicitar arquivo: {e}")
        finally:
            # Garantir que a flag de download seja sempre resetada
            self.downloading = False
            # Restaurar handler original do Ctrl+C
            try:
                if 'old_handler' in locals():
                    signal.signal(signal.SIGINT, old_handler)
            except:
                pass
    
    def send_chat_message(self, message):
        try:
            request = f"CHAT:{message}"
            self.send_message(request)
            
            if not self.connected:
                return
            
            print("[INFO] Mensagem de chat enviada")
        
        except Exception as e:
            print(f"[ERRO] Erro ao enviar mensagem de chat: {e}")
    
    def disconnect(self):
        try:
            if self.connected:
                try:
                    self.send_message("SAIR")
                    
                    # Tentar receber resposta com timeout curto
                    original_timeout = self.client_socket.gettimeout()
                    self.client_socket.settimeout(2.0)  # Timeout curto para desconexão
                    
                    response = self.receive_message()
                    if response == "OK":
                        print("[INFO] Desconectado do servidor")
                    
                    self.client_socket.settimeout(original_timeout)
                except (KeyboardInterrupt, socket.timeout, Exception):
                    # Ignorar erros durante desconexão - apenas fechar socket
                    pass
                
                self.connected = False
        
        except Exception:
            # Ignorar todos os erros durante desconexão
            pass
        
        finally:
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
            print("[INFO] Cliente desconectado")
    
    def show_menu(self):
        print("\n" + "="*50)
        print("MENU DE OPÇÕES")
        print("="*50)
        print("1. Solicitar arquivo")
        print("2. Enviar mensagem de chat")
        print("3. Listar arquivos baixados")
        print("4. Testar conexão")
        print("5. Ajuda")
        print("6. Sair")
        print("="*50)
    
    def list_downloaded_files(self):
        try:
            files = os.listdir(self.downloads_dir)
            if not files:
                print("[INFO] Nenhum arquivo baixado ainda")
                return
            
            print(f"\n[INFO] Arquivos em {os.path.abspath(self.downloads_dir)}:")
            print("-" * 40)
            
            for file_name in files:
                file_path = os.path.join(self.downloads_dir, file_name)
                file_size = os.path.getsize(file_path)
                
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                print(f"  {file_name} ({size_str})")
            
            print("-" * 40)
        
        except Exception as e:
            print(f"[ERRO] Erro ao listar arquivos: {e}")
    
    def test_connection(self):
        try:
            print("[INFO] Testando conexão com o servidor...")
            
            # Enviar mensagem de teste (chat vazio)
            self.send_message("CHAT:")
            
            if self.connected:
                print("[SUCESSO] Conexão com o servidor está ativa")
            else:
                print("[ERRO] Conexão perdida")
        
        except Exception as e:
            print(f"[ERRO] Falha no teste de conexão: {e}")
            self.connected = False
    
    def show_help(self):
        print("\n" + "="*60)
        print("AJUDA - CLIENTE TCP")
        print("="*60)
        print("Este cliente permite:")
        print("• Baixar arquivos do servidor com verificação de integridade")
        print("• Enviar e receber mensagens de chat")
        print("• Verificar arquivos baixados")
        print()
        print("PROTOCOLO DE COMUNICAÇÃO:")
        print("• ARQUIVO:<nome> - Solicita um arquivo do servidor")
        print("• CHAT:<mensagem> - Envia mensagem de chat")
        print("• SAIR - Desconecta do servidor")
        print()
        print("VERIFICAÇÃO DE INTEGRIDADE:")
        print("• Todos os arquivos são verificados com SHA-256")
        print("• Arquivos corrompidos são detectados automaticamente")
        print()
        print("DIRETÓRIO DE DOWNLOADS:")
        print(f"• {os.path.abspath(self.downloads_dir)}")
        print("="*60)
    
    def run(self):
        print("=== Cliente TCP ===")
        print("Trabalho 2 - Redes de Computadores")
        print()
        
        host = input("Digite o endereço IP do servidor: ").strip()
        if not host:
            print("[ERRO] Endereço IP é obrigatório")
            return
        
        try:
            port = input("Digite a porta do servidor: ").strip()
            if not port:
                print("[ERRO] Porta é obrigatória")
                return
            port = int(port)
        except ValueError:
            print("[ERRO] Porta inválida")
            return
        
        if not self.connect_to_server(host, port):
            return
        
        try:
            while self.connected:
                self.show_menu()
                
                try:
                    choice = input("Digite sua opção: ").strip()
                    
                    if choice == "1":
                        file_name = input("Digite o nome do arquivo: ").strip()
                        if file_name:
                            print("[INFO] Iniciando download... (Pressione Ctrl+C para cancelar)")
                            self.request_file(file_name)
                        else:
                            print("[ERRO] Nome do arquivo é obrigatório")
                    
                    elif choice == "2":
                        message = input("Digite sua mensagem: ").strip()
                        if message:
                            self.send_chat_message(message)
                        else:
                            print("[ERRO] Mensagem não pode estar vazia")
                    
                    elif choice == "3":
                        self.list_downloaded_files()
                    
                    elif choice == "4":
                        self.test_connection()
                    
                    elif choice == "5":
                        self.show_help()
                    
                    elif choice == "6":
                        print("[INFO] Encerrando cliente...")
                        break
                    
                    else:
                        print("[ERRO] Opção inválida")
                
                except EOFError:
                    print("\n[INFO] Entrada interrompida")
                    break
                except KeyboardInterrupt:
                    print("\n[INFO] Operação cancelada pelo usuário")
                    # Continuar no loop principal ao invés de sair
                    continue
        
        except KeyboardInterrupt:
            print("\n[INFO] Programa interrompido pelo usuário")
        
        finally:
            try:
                self.disconnect()
            except KeyboardInterrupt:
                print("\n[INFO] Desconexão interrompida - forçando saída")
            except Exception:
                pass

def main():
    client = TCPClient()
    
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n[INFO] Programa encerrado pelo usuário")
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Saída forçada")
    except Exception:
        pass