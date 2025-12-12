#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'TCP_ClientServer'))
from client import TCPClient

class HTTPClient(TCPClient):
    def __init__(self):
        super().__init__()
        self.downloads_dir = "http_downloads"
        
        if not os.path.exists(self.downloads_dir):
            os.makedirs(self.downloads_dir)
    
    def send_http_request(self, method='GET', path='/', host=None, port=None):
        """Envia uma requisição HTTP diretamente pelo socket (não usa protocolo customizado)"""
        try:
            if not self.connected or not self.client_socket:
                print("[ERRO] Cliente não está conectado")
                return False
            
            request = f"{method} {path} HTTP/1.1\r\n"
            request += f"Host: {host}:{port}\r\n"
            request += "Connection: close\r\n"
            request += "\r\n"
            
            request_bytes = request.encode('utf-8')
            self.client_socket.sendall(request_bytes)
            
            print(f"[INFO] Requisição HTTP enviada: {method} {path}")
            return True
            
        except Exception as e:
            print(f"[ERRO] Erro ao enviar requisição HTTP: {e}")
            self.connected = False
            return False
    
    def receive_http_response(self):
        """Recebe uma resposta HTTP diretamente do socket (não usa protocolo customizado)"""
        try:
            if not self.connected or not self.client_socket:
                return None
            
            response_data = b''
            self.client_socket.settimeout(10.0)
            
            while b'\r\n\r\n' not in response_data:
                chunk = self.client_socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                
                if len(response_data) > 8192:
                    break
            
            if not response_data:
                return None
            
            header_end = response_data.find(b'\r\n\r\n')
            if header_end == -1:
                return None
            
            headers_data = response_data[:header_end]
            body_start = header_end + 4
            
            headers_str = headers_data.decode('utf-8', errors='ignore')
            headers_lines = headers_str.split('\r\n')
            
            if not headers_lines:
                return None
            
            status_line = headers_lines[0]
            status_parts = status_line.split(' ', 2)
            if len(status_parts) < 3:
                return None
            
            http_version = status_parts[0]
            status_code = int(status_parts[1])
            status_text = status_parts[2]
            
            headers = {}
            for line in headers_lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            content_length = None
            if 'content-length' in headers:
                try:
                    content_length = int(headers['content-length'])
                except ValueError:
                    pass
            
            body_data = response_data[body_start:]
            
            if content_length is not None:
                while len(body_data) < content_length:
                    remaining = content_length - len(body_data)
                    chunk = self.client_socket.recv(min(4096, remaining))
                    if not chunk:
                        break
                    body_data += chunk
            else:
                try:
                    while True:
                        chunk = self.client_socket.recv(4096)
                        if not chunk:
                            break
                        body_data += chunk
                except socket.timeout:
                    pass
            
            return {
                'version': http_version,
                'status_code': status_code,
                'status_text': status_text,
                'headers': headers,
                'body': body_data,
                'content_length': content_length
            }
            
        except socket.timeout:
            print("[ERRO] Timeout ao receber resposta HTTP")
            return None
        except Exception as e:
            print(f"[ERRO] Erro ao receber resposta HTTP: {e}")
            return None
    
    def connect_to_server(self, host, port):
        """Sobrescrever para usar a conexão do TCPClient mas sem thread de escuta"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            self.connected = True
            
            print(f"[INFO] Conectado ao servidor HTTP {host}:{port}")
            
            
            return True
            
        except Exception as e:
            print(f"[ERRO] Erro ao conectar ao servidor: {e}")
            self.connected = False
            return False
    
    def get(self, url):
        """Faz uma requisição HTTP GET para a URL especificada"""
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                parsed = urlparse('http://' + url)
            
            host = parsed.hostname or 'localhost'
            port = parsed.port or 80
            path = parsed.path or '/'
            
            if parsed.query:
                path += '?' + parsed.query
            
            if not self.connected:
                if not self.connect_to_server(host, port):
                    return None
            
            if not self.send_http_request('GET', path, host, port):
                return None
            
            response = self.receive_http_response()
            
            return response
            
        except Exception as e:
            print(f"[ERRO] Erro ao fazer requisição GET: {e}")
            return None
    
    def download_file(self, url, filename=None):
        """Baixa um arquivo via HTTP GET"""
        try:
            response = self.get(url)
            
            if not response:
                print("[ERRO] Não foi possível obter resposta do servidor")
                return False
            
            if response['status_code'] != 200:
                print(f"[ERRO] Servidor retornou erro: {response['status_code']} {response['status_text']}")
                return False
            
            if not filename:
                if 'content-disposition' in response['headers']:
                    content_disp = response['headers']['content-disposition']
                    if 'filename=' in content_disp:
                        filename = content_disp.split('filename=')[1].strip('"\'')
                
                if not filename:
                    parsed = urlparse(url)
                    filename = os.path.basename(parsed.path) or 'index.html'
            
            file_path = os.path.join(self.downloads_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response['body'])
            
            file_size = len(response['body'])
            print(f"[SUCESSO] Arquivo baixado: {filename} ({file_size} bytes)")
            print(f"[INFO] Salvo em: {os.path.abspath(file_path)}")
            
            return True
            
        except Exception as e:
            print(f"[ERRO] Erro ao baixar arquivo: {e}")
            return False
    
    def disconnect(self):
        """Desconectar do servidor"""
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        print("[INFO] Cliente HTTP desconectado")
    
    def show_menu(self):
        """Menu interativo do cliente HTTP"""
        print("\n" + "="*50)
        print("CLIENTE HTTP")
        print("="*50)
        print("1. Fazer requisição GET")
        print("2. Baixar arquivo")
        print("3. Listar arquivos baixados")
        print("4. Sair")
        print("="*50)
    
    def list_downloaded_files(self):
        """Lista arquivos baixados"""
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
    
    def run(self):
        """Loop principal do cliente HTTP"""
        print("=== Cliente HTTP ===")
        print("Trabalho 3 - Redes de Computadores")
        print("Baseado no Trabalho 2 - Cliente TCP")
        print()
        
        try:
            while True:
                self.show_menu()
                
                try:
                    choice = input("Digite sua opção: ").strip()
                    
                    if choice == "1":
                        url = input("Digite a URL (ex: http://localhost:8888/index.html): ").strip()
                        if url:
                            response = self.get(url)
                            if response:
                                print(f"\n[INFO] Status: {response['status_code']} {response['status_text']}")
                                print(f"[INFO] Content-Type: {response['headers'].get('content-type', 'N/A')}")
                                print(f"[INFO] Content-Length: {response['content_length'] or len(response['body'])} bytes")
                                
                                content_type = response['headers'].get('content-type', '').lower()
                                if 'text' in content_type or 'html' in content_type:
                                    body_text = response['body'][:500].decode('utf-8', errors='ignore')
                                    print(f"\n[PREVIEW] Primeiros 500 caracteres:")
                                    print("-" * 40)
                                    print(body_text)
                                    if len(response['body']) > 500:
                                        print("...")
                                    print("-" * 40)
                        else:
                            print("[ERRO] URL não pode estar vazia")
                    
                    elif choice == "2":
                        url = input("Digite a URL do arquivo: ").strip()
                        if url:
                            filename = input("Digite o nome do arquivo (Enter para usar o nome da URL): ").strip()
                            if not filename:
                                filename = None
                            self.download_file(url, filename)
                        else:
                            print("[ERRO] URL não pode estar vazia")
                    
                    elif choice == "3":
                        self.list_downloaded_files()
                    
                    elif choice == "4":
                        print("[INFO] Encerrando cliente...")
                        break
                    
                    else:
                        print("[ERRO] Opção inválida")
                
                except EOFError:
                    print("\n[INFO] Entrada interrompida")
                    break
                except KeyboardInterrupt:
                    print("\n[INFO] Operação cancelada pelo usuário")
                    continue
        
        except KeyboardInterrupt:
            print("\n[INFO] Programa interrompido pelo usuário")
        
        finally:
            try:
                self.disconnect()
            except:
                pass

def main():
    client = HTTPClient()
    
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

