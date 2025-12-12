#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de teste simples para verificar se o servidor HTTP está funcionando
"""

import socket
import sys

def test_server(host='localhost', port=8888):
    """Testa se o servidor está respondendo"""
    try:
        # Criar socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Conectar
        print(f"Conectando a {host}:{port}...")
        sock.connect((host, port))
        print("✓ Conectado com sucesso!")
        
        # Enviar requisição HTTP GET
        request = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        print(f"Enviando requisição: {request}")
        sock.sendall(request.encode('utf-8'))
        
        # Receber resposta
        response = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            # Se recebeu headers completos, parar
            if b'\r\n\r\n' in response:
                break
        
        sock.close()
        
        # Verificar resposta
        response_str = response.decode('utf-8', errors='ignore')
        print(f"\n✓ Resposta recebida ({len(response)} bytes):")
        print("-" * 60)
        print(response_str[:500])  # Primeiros 500 caracteres
        print("-" * 60)
        
        if "200 OK" in response_str or "HTTP/1.1" in response_str:
            print("\n✓ Servidor está funcionando corretamente!")
            return True
        else:
            print("\n✗ Resposta não parece ser HTTP válida")
            return False
            
    except socket.timeout:
        print("✗ Timeout: Servidor não respondeu")
        return False
    except ConnectionRefusedError:
        print(f"✗ Conexão recusada: Servidor não está rodando em {host}:{port}")
        print("  Execute: python http_server.py")
        return False
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8888
    
    print("=" * 60)
    print("Teste do Servidor HTTP/TCP")
    print("=" * 60)
    
    success = test_server(host, port)
    
    sys.exit(0 if success else 1)



