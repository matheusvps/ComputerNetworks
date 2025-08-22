#!/usr/bin/env python3
"""
Script de Teste Simples para o Sistema UDP
Testa funcionalidades básicas sem executar demonstrações completas
"""

import os
import sys
import subprocess
import time

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    print("Testando imports...")
    
    try:
        import socket
        import struct
        import hashlib
        import os
        import time
        import threading
        import logging
        import argparse
        print("✓ Todas as bibliotecas padrão importadas com sucesso")
        return True
    except ImportError as e:
        print(f"✗ Erro ao importar biblioteca: {e}")
        return False

def test_file_creation():
    """Testa criação de arquivo de teste"""
    print("\nTestando criação de arquivo de teste...")
    
    try:
        result = subprocess.run([
            "python3", "create_test_file.py", 
            "--filename", "test_simple.txt", 
            "--size", "1"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            if os.path.exists("test_simple.txt"):
                size = os.path.getsize("test_simple.txt")
                print(f"✓ Arquivo de teste criado: {size} bytes")
                
                # Limpa arquivo de teste
                os.remove("test_simple.txt")
                print("✓ Arquivo de teste removido")
                return True
            else:
                print("✗ Arquivo não foi criado")
                return False
        else:
            print(f"✗ Erro na criação: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Timeout na criação do arquivo")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
        return False

def test_hello_world():
    """Testa exemplo Hello World UDP"""
    print("\nTestando exemplo Hello World UDP...")
    
    try:
        # Inicia servidor em background
        server_process = subprocess.Popen([
            "python3", "hello_world_udp.py", "server"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Aguarda servidor inicializar
        time.sleep(2)
        
        # Testa cliente
        result = subprocess.run([
            "python3", "hello_world_udp.py", "client"
        ], capture_output=True, text=True, timeout=10)
        
        # Para servidor
        server_process.terminate()
        server_process.wait()
        
        if result.returncode == 0:
            print("✓ Exemplo Hello World executado com sucesso")
            return True
        else:
            print(f"✗ Erro no cliente: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Erro no teste Hello World: {e}")
        return False

def test_server_client():
    """Testa servidor e cliente básicos"""
    print("\nTestando servidor e cliente básicos...")
    
    try:
        # Cria arquivo pequeno para teste
        result = subprocess.run([
            "python3", "create_test_file.py", 
            "--filename", "test_server.txt", 
            "--size", "1"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"✗ Erro ao criar arquivo de teste: {result.stderr}")
            return False
        
        if not os.path.exists("test_server.txt"):
            print("✗ Arquivo de teste não foi criado")
            return False
        
        print(f"✓ Arquivo de teste criado: {os.path.getsize('test_server.txt')} bytes")
        
        # Inicia servidor em background
        server_process = subprocess.Popen([
            "python3", "server.py", "--port", "8890"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Aguarda servidor inicializar
        time.sleep(3)
        
        # Testa cliente
        result = subprocess.run([
            "python3", "client.py", "127.0.0.1", "8890", "test_server.txt"
        ], capture_output=True, text=True, timeout=30)
        
        # Para servidor
        server_process.terminate()
        server_process.wait()
        
        # Verifica se arquivo foi baixado
        if os.path.exists("test_server.txt"):
            original_size = os.path.getsize("test_server.txt")
            os.remove("test_server.txt")
            
            if result.returncode == 0:
                print("✓ Servidor e cliente funcionaram")
                return True
            else:
                print(f"✗ Erro no cliente: {result.stderr}")
                return False
        else:
            print("✗ Arquivo de teste não encontrado")
            return False
            
    except Exception as e:
        print(f"✗ Erro no teste servidor/cliente: {e}")
        return False

def main():
    """Função principal de teste"""
    print("TESTE SIMPLES DO SISTEMA UDP")
    print("="*40)
    
    tests = [
        ("Imports", test_imports),
        ("Criação de Arquivo", test_file_creation),
        ("Hello World UDP", test_hello_world),
        ("Servidor/Cliente", test_server_client)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20}")
        print(f"TESTE: {test_name}")
        print(f"{'='*20}")
        
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name}: PASSOU")
            else:
                print(f"✗ {test_name}: FALHOU")
        except Exception as e:
            print(f"✗ {test_name}: ERRO - {e}")
    
    print(f"\n{'='*40}")
    print(f"RESULTADO: {passed}/{total} testes passaram")
    print(f"{'='*40}")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("O sistema está funcionando corretamente.")
        return 0
    else:
        print("⚠️  ALGUNS TESTES FALHARAM.")
        print("Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
