#!/usr/bin/env python3
"""
Exemplo Simples de Hello World UDP
Demonstra o uso básico de sockets UDP para familiarização com a API
"""

import socket
import threading
import time

class HelloWorldUDPServer:
    def __init__(self, host='127.0.0.1', port=9999):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
    
    def start(self):
        """Inicia o servidor Hello World"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.running = True
            
            print(f"Servidor Hello World UDP iniciado em {self.host}:{self.port}")
            print("Aguardando mensagens...")
            
            while self.running:
                try:
                    data, client_address = self.socket.recvfrom(1024)
                    message = data.decode('utf-8')
                    
                    print(f"Mensagem recebida de {client_address}: {message}")
                    
                    # Responde com Hello World
                    response = f"Hello World! Você disse: {message}"
                    self.socket.sendto(response.encode('utf-8'), client_address)
                    
                except Exception as e:
                    if self.running:
                        print(f"Erro: {e}")
                        
        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")
    
    def stop(self):
        """Para o servidor"""
        self.running = False
        if self.socket:
            self.socket.close()
        print("Servidor parado")

class HelloWorldUDPClient:
    def __init__(self, server_host='127.0.0.1', server_port=9999):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
    
    def connect(self):
        """Conecta ao servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print(f"Cliente conectado ao servidor {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return False
    
    def send_message(self, message):
        """Envia uma mensagem para o servidor"""
        try:
            if not self.socket:
                print("Cliente não conectado")
                return None
            
            # Envia mensagem
            self.socket.sendto(message.encode('utf-8'), (self.server_host, self.server_port))
            
            # Aguarda resposta
            self.socket.settimeout(5.0)
            data, _ = self.socket.recvfrom(1024)
            response = data.decode('utf-8')
            
            return response
            
        except socket.timeout:
            print("Timeout ao aguardar resposta")
            return None
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return None
    
    def disconnect(self):
        """Desconecta do servidor"""
        if self.socket:
            self.socket.close()
        print("Cliente desconectado")

def run_server():
    """Executa o servidor"""
    server = HelloWorldUDPServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nParando servidor...")
        server.stop()

def run_client():
    """Executa o cliente"""
    client = HelloWorldUDPClient()
    
    if not client.connect():
        return
    
    try:
        # Envia algumas mensagens de teste
        messages = ["Olá!", "Como vai?", "Teste UDP", "Fim"]
        
        for message in messages:
            print(f"Enviando: {message}")
            response = client.send_message(message)
            
            if response:
                print(f"Resposta: {response}")
            else:
                print("Sem resposta")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nOperação cancelada")
    finally:
        client.disconnect()

def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python hello_world_udp.py [server|client]")
        print("  server - Executa o servidor")
        print("  client - Executa o cliente")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == 'server':
        run_server()
    elif mode == 'client':
        run_client()
    else:
        print("Modo inválido. Use 'server' ou 'client'")

if __name__ == "__main__":
    main()
