#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import os
import sys
import signal
from datetime import datetime
from urllib.parse import unquote

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'TCP_ClientServer'))
from server import TCPServer

class HTTPServer(TCPServer):
    def __init__(self, host='localhost', port=8888):
        super().__init__(host, port)
        self.web_root = "web_files"
        
        if not os.path.exists(self.web_root):
            os.makedirs(self.web_root)
    
    def signal_handler(self, signum, frame):
        print(f"\n[INFO] Sinal {signum} recebido - encerrando servidor...")
        self.running = False
    
    def get_content_type(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.html': 'text/html; charset=UTF-8',
            '.htm': 'text/html; charset=UTF-8',
            '.jpeg': 'image/jpeg',
            '.jpg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.css': 'text/css; charset=UTF-8',
            '.js': 'application/javascript; charset=UTF-8',
            '.txt': 'text/plain; charset=UTF-8',
            '.json': 'application/json; charset=UTF-8',
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def parse_http_request(self, request_data):
        try:
            if '\r\n' in request_data:
                lines = request_data.split('\r\n')
            else:
                lines = request_data.split('\n')
            
            if not lines or not lines[0]:
                return None
            
            request_line = lines[0].strip()
            if not request_line:
                return None
            
            parts = request_line.split()
            
            if len(parts) < 2:
                print(f"[DEBUG] Request line inválida: {request_line}")
                return None
            
            method = parts[0].strip().upper()
            path = parts[1].strip()
            version = parts[2].strip() if len(parts) > 2 else 'HTTP/1.0'
            
            headers = {}
            for i in range(1, len(lines)):
                line = lines[i].strip()
                if not line:
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            return {
                'method': method,
                'path': path,
                'version': version,
                'headers': headers
            }
        except Exception as e:
            print(f"[ERRO] Erro ao fazer parse da requisição HTTP: {e}")
            print(f"[DEBUG] Dados recebidos: {request_data[:200]}")
            return None
    
    def send_http_response(self, client_socket, status_code, status_text, content='', content_type='text/html'):
        try:
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = content
            
            content_length = len(content_bytes)
            
            response_headers = [
                f"HTTP/1.1 {status_code} {status_text}",
                f"Server: Python HTTP Server",
                f"Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}",
                f"Content-Type: {content_type}",
                f"Content-Length: {content_length}",
                "Connection: close"
            ]
            
            response = '\r\n'.join(response_headers) + '\r\n\r\n'
            
            header_bytes = response.encode('utf-8')
            response_bytes = header_bytes + content_bytes
            
            expected_total = len(header_bytes) + len(content_bytes)
            if len(response_bytes) != expected_total:
                print(f"[ERRO] Tamanho da resposta não corresponde! Esperado: {expected_total}, Real: {len(response_bytes)}")
            
            total_size = len(response_bytes)
            header_size = len(header_bytes)
            body_size = len(content_bytes)
            
            print(f"[DEBUG] Resposta HTTP: Header={header_size} bytes, Body={body_size} bytes, Total={total_size} bytes")
            print(f"[DEBUG] Content-Length no header: {content_length} bytes")
            print(f"[DEBUG] Verificação: Header + Body = {header_size} + {body_size} = {header_size + body_size} bytes")
            
            try:
                client_socket.sendall(response_bytes)
                
                print(f"[DEBUG] Resposta HTTP enviada: {status_code} {status_text}")
                print(f"[DEBUG] Total enviado: {total_size} bytes (Header: {header_size} + Body: {body_size})")
                print(f"[DEBUG] Content-Length no header: {content_length} bytes")
                
                if body_size != content_length:
                    print(f"[ERRO] ERRO: Body size ({body_size}) != Content-Length ({content_length})!")
                else:
                    print(f"[DEBUG] ✓ Verificação OK: Body size = Content-Length = {content_length} bytes")
                    
            except socket.error as e:
                print(f"[ERRO] Erro de socket ao enviar resposta: {e}")
                raise
            except Exception as e:
                print(f"[ERRO] Erro ao enviar resposta HTTP: {e}")
                raise
            
        except Exception as e:
            print(f"[ERRO] Erro ao enviar resposta HTTP: {e}")
            import traceback
            traceback.print_exc()
    
    def send_error_response(self, client_socket, status_code, status_text, error_message):
        error_html = f"""<html>
<head>
<title>{status_code} {status_text}</title>
</head>
<body>
<h1>{status_code} {status_text}</h1>
<p>{error_message}</p>
</body>
</html>"""
        self.send_http_response(client_socket, status_code, status_text, error_html, 'text/html; charset=UTF-8')
    
    def serve_file(self, client_socket, file_path):
        try:
            file_path = unquote(file_path)
            
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            full_path = os.path.join(self.web_root, file_path)
            
            full_path = os.path.normpath(full_path)
            web_root_abs = os.path.abspath(self.web_root)
            full_path_abs = os.path.abspath(full_path)
            
            if not full_path_abs.startswith(web_root_abs):
                print(f"[ERRO] Tentativa de acesso fora do diretório web: {file_path}")
                self.send_error_response(client_socket, 403, "Forbidden", 
                                       "Acesso negado: tentativa de acessar arquivo fora do diretório permitido")
                return False
            
            if not os.path.exists(full_path):
                print(f"[INFO] Arquivo não encontrado: {file_path}")
                self.send_error_response(client_socket, 404, "Not Found", 
                                       f"O arquivo '{file_path}' não foi encontrado no servidor.")
                return False
            
            if not os.path.isfile(full_path):
                print(f"[INFO] Caminho não é um arquivo: {file_path}")
                self.send_error_response(client_socket, 404, "Not Found", 
                                       f"'{file_path}' não é um arquivo válido.")
                return False
            
            content_type = self.get_content_type(full_path)
            
            with open(full_path, 'rb') as f:
                content_bytes = f.read()
            
            content_size = len(content_bytes)
            
            print(f"[INFO] Servindo arquivo: {file_path} ({content_size} bytes, {content_type})")
            self.send_http_response(client_socket, 200, "OK", content_bytes, content_type)
            return True
            
        except PermissionError:
            print(f"[ERRO] Sem permissão para ler arquivo: {file_path}")
            self.send_error_response(client_socket, 403, "Forbidden", 
                                   "Sem permissão para acessar este arquivo.")
            return False
        except Exception as e:
            print(f"[ERRO] Erro ao servir arquivo {file_path}: {e}")
            self.send_error_response(client_socket, 500, "Internal Server Error", 
                                   f"Erro interno do servidor: {str(e)}")
            return False
    
    def handle_client(self, client_socket, client_address):
        self.client_counter += 1
        client_id = self.client_counter
        
        print(f"[INFO] Cliente {client_id} conectado de {client_address}")
        
        try:
            request_data = b''
            client_socket.settimeout(10.0)
            
            max_attempts = 10
            attempts = 0
            while attempts < max_attempts:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                request_data += chunk
                attempts += 1
                
                if b'\r\n\r\n' in request_data:
                    header_end = request_data.find(b'\r\n\r\n')
                    if header_end != -1:
                        request_data = request_data[:header_end + 4]
                    break
                
                if attempts >= 2:
                    if b'\r\n' in request_data:
                        break
            
            if not request_data:
                print(f"[INFO] Cliente {client_id} desconectou sem enviar requisição")
                return
            
            print(f"[DEBUG] Cliente {client_id} - Recebeu {len(request_data)} bytes")
            print(f"[DEBUG] Primeiros 200 bytes: {request_data[:200]}")
            
            try:
                request_str = request_data.decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"[ERRO] Erro ao decodificar requisição do Cliente {client_id}: {e}")
                self.send_error_response(client_socket, 400, "Bad Request", 
                                       "Requisição inválida: encoding não suportado")
                return
            
            request = self.parse_http_request(request_str)
            
            if not request:
                print(f"[ERRO] Requisição HTTP inválida do Cliente {client_id}")
                print(f"[DEBUG] Requisição recebida: {request_str[:500]}")
                self.send_error_response(client_socket, 400, "Bad Request", 
                                       "Requisição HTTP inválida")
                return
            
            print(f"[INFO] Cliente {client_id} - {request['method']} {request['path']} {request['version']}")
            
            if request['method'].upper() != 'GET':
                print(f"[INFO] Método não suportado: {request['method']}")
                self.send_error_response(client_socket, 501, "Not Implemented", 
                                       f"Método {request['method']} não é suportado. Apenas GET é suportado.")
                return
            
            path = request['path']
            if path == '/' or path == '':
                path = '/index.html'
            
            print(f"[DEBUG] Cliente {client_id} - Servindo arquivo: {path}")
            
            self.serve_file(client_socket, path)
            
        except socket.timeout:
            print(f"[INFO] Timeout na comunicação com Cliente {client_id}")
        except Exception as e:
            print(f"[ERRO] Erro na comunicação com Cliente {client_id}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                client_socket.close()
            except:
                pass
            print(f"[INFO] Cliente {client_id} desconectado")
    
    def server_chat_input(self):
        """Sobrescrever para não fazer nada - HTTP não precisa de chat do servidor"""
        pass
    
    def start_server(self):
        print("=" * 60)
        print(f"[INFO] Servidor HTTP/TCP Multithread iniciado")
        print(f"[INFO] Endereço: {self.host}:{self.port}")
        print(f"[INFO] Diretório web: {os.path.abspath(self.web_root)}")
        print(f"[INFO] Acesse no navegador: http://{self.host}:{self.port}/")
        print("[INFO] Aguardando conexões...")
        print("[INFO] Pressione Ctrl+C para parar o servidor")
        print("=" * 60)
        
        super().start_server()
    
    def stop_server(self):
        print("\n[INFO] Encerrando servidor HTTP...")
        super().stop_server()

def main():
    print("=== Servidor HTTP/TCP Multithread ===")
    print("Trabalho 3 - Redes de Computadores")
    print("Baseado no Trabalho 2 - Servidor TCP Multithread")
    print()
    
    host = input("Digite o endereço IP do servidor (Enter para 0.0.0.0 - todas as interfaces): ").strip()
    if not host:
        host = '0.0.0.0'
    
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
    
    server = HTTPServer(host, port)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n[INFO] Interrompido pelo usuário")
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
    finally:
        if server.running:
            server.stop_server()

if __name__ == "__main__":
    main()

