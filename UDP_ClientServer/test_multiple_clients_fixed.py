#!/usr/bin/env python3
"""
Teste de múltiplos clientes com portas separadas
Cada cliente usa uma porta diferente para evitar mistura de mensagens
"""

import subprocess
import time
import os
import signal

def test_multiple_clients_fixed():
    print("🧪 TESTE DE MÚLTIPLOS CLIENTES COM PORTAS SEPARADAS")
    print("=" * 70)
    
    # Inicia servidor na porta base
    print("📡 Iniciando servidor na porta 8901...")
    server_process = subprocess.Popen([
        "python3", "server.py", "--port", "8901"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Aguarda servidor inicializar
    time.sleep(3)
    print("✅ Servidor iniciado na porta 8901")
    
    try:
        # Cliente 1 (arquivo pequeno) na porta 8901
        print("\n👤 Iniciando Cliente 1 (arquivo_pequeno.txt) na porta 8901...")
        client1_process = subprocess.Popen([
            "python3", "client.py", "127.0.0.1", "8901", "arquivo_pequeno.txt"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Aguarda um pouco antes de iniciar o segundo cliente
        time.sleep(2)
        
        # Cliente 2 (arquivo médio) na porta 8902
        print("👤 Iniciando Cliente 2 (arquivo_medio.txt) na porta 8902...")
        
        # Inicia segundo servidor na porta 8902
        server2_process = subprocess.Popen([
            "python3", "server.py", "--port", "8902"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(2)  # Aguarda segundo servidor inicializar
        
        client2_process = subprocess.Popen([
            "python3", "client.py", "127.0.0.1", "8902", "arquivo_medio.txt"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("\n⏳ Aguardando clientes terminarem...")
        
        # Aguarda clientes com timeout
        client1_result = None
        client2_result = None
        
        try:
            client1_result = client1_process.wait(timeout=60)
            print(f"✅ Cliente 1 terminou com código: {client1_result}")
        except subprocess.TimeoutExpired:
            print("❌ Cliente 1 excedeu timeout")
            client1_process.terminate()
            client1_process.wait()
            client1_result = -1
        
        try:
            client2_result = client2_process.wait(timeout=60)
            print(f"✅ Cliente 2 terminou com código: {client2_result}")
        except subprocess.TimeoutExpired:
            print("❌ Cliente 2 excedeu timeout")
            client2_process.terminate()
            client2_process.wait()
            client2_result = -1
        
        # Verifica resultados
        if client1_result == 0 and client2_result == 0:
            print("\n🎉 AMBOS OS CLIENTES FUNCIONARAM COM PORTAS SEPARADAS!")
        else:
            print("\n⚠️ ALGUNS CLIENTES FALHARAM:")
            if client1_result != 0:
                print(f"   Cliente 1: código {client1_result}")
            if client2_result != 0:
                print(f"   Cliente 2: código {client2_result}")
        
        # Mostra saídas dos clientes
        print("\n📋 SAÍDA DO CLIENTE 1:")
        print(client1_process.stdout.read().decode() if client1_process.stdout else "Sem saída")
        print("\n📋 ERROS DO CLIENTE 1:")
        print(client1_process.stderr.read().decode() if client1_process.stderr else "Sem erros")
        
        print("\n📋 SAÍDA DO CLIENTE 2:")
        print(client2_process.stdout.read().decode() if client2_process.stdout else "Sem saída")
        print("\n📋 ERROS DO CLIENTE 2:")
        print(client2_process.stderr.read().decode() if client2_process.stderr else "Sem erros")
        
    finally:
        # Para servidores
        print("\n🛑 Parando servidores...")
        server_process.terminate()
        server_process.wait()
        if 'server2_process' in locals():
            server2_process.terminate()
            server2_process.wait()
        print("✅ Servidores parados")

if __name__ == "__main__":
    test_multiple_clients_fixed()
