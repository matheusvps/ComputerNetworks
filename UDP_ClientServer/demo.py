#!/usr/bin/env python3
"""
Script de Demonstração do Sistema UDP de Transferência de Arquivos
Demonstra como usar o servidor e cliente para transferir arquivos
"""

import os
import time
import subprocess
import threading
import sys

def run_command(cmd, description, background=False):
    """Executa um comando e retorna o processo"""
    print(f"\n{'='*50}")
    print(f"Executando: {description}")
    print(f"Comando: {cmd}")
    print(f"{'='*50}")
    
    if background:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    else:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Comando executado com sucesso")
            if result.stdout:
                print("Saída:", result.stdout)
        else:
            print("✗ Erro na execução:")
            if result.stderr:
                print(result.stderr)
        return result

def wait_for_server(port, max_wait=10):
    """Aguarda o servidor estar disponível"""
    import socket
    
    print(f"Aguardando servidor na porta {port}...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            sock.sendto(b"TEST", ("127.0.0.1", port))
            sock.close()
            print("✓ Servidor está respondendo")
            return True
        except:
            time.sleep(0.5)
    
    print("✗ Timeout aguardando servidor")
    return False

def demo_hello_world():
    """Demonstra o exemplo Hello World UDP"""
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO: Hello World UDP")
    print("="*60)
    
    # Inicia servidor em background
    server_process = run_command(
        "python3 hello_world_udp.py server",
        "Iniciando servidor Hello World UDP",
        background=True
    )
    
    time.sleep(2)  # Aguarda servidor inicializar
    
    # Executa cliente
    run_command(
        "python3 hello_world_udp.py client",
        "Executando cliente Hello World UDP"
    )
    
    # Para servidor
    server_process.terminate()
    server_process.wait()

def demo_file_transfer():
    """Demonstra a transferência de arquivos UDP"""
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO: Transferência de Arquivos UDP")
    print("="*60)
    
    # Cria arquivo de teste
    print("\n1. Criando arquivo de teste...")
    run_command(
        "python3 create_test_file.py --filename demo_file.txt --size 1",
        "Criando arquivo de teste de 1MB"
    )
    
    # Verifica se arquivo foi criado
    if not os.path.exists("demo_file.txt"):
        print("✗ Erro: Arquivo de teste não foi criado")
        return
    
    file_size = os.path.getsize("demo_file.txt")
    print(f"✓ Arquivo criado: demo_file.txt ({file_size} bytes)")
    
    # Inicia servidor em background
    print("\n2. Iniciando servidor UDP...")
    server_process = run_command(
        "python3 server.py --port 8888",
        "Iniciando servidor UDP na porta 8888",
        background=True
    )
    
    # Aguarda servidor inicializar
    if not wait_for_server(8888):
        print("✗ Falha ao iniciar servidor")
        server_process.terminate()
        return
    
    # Executa cliente para baixar arquivo
    print("\n3. Executando cliente UDP...")
    run_command(
        "python3 client.py 127.0.0.1 8888 demo_file.txt --output-dir downloads",
        "Baixando arquivo via UDP"
    )
    
    # Verifica se arquivo foi baixado
    downloaded_file = "downloads/demo_file.txt"
    if os.path.exists(downloaded_file):
        downloaded_size = os.path.getsize(downloaded_file)
        print(f"✓ Arquivo baixado com sucesso: {downloaded_file}")
        print(f"  Tamanho original: {file_size} bytes")
        print(f"  Tamanho baixado: {downloaded_size} bytes")
        
        if file_size == downloaded_size:
            print("  ✓ Tamanhos coincidem - transferência bem-sucedida!")
        else:
            print("  ✗ Tamanhos não coincidem - erro na transferência")
    else:
        print("✗ Arquivo não foi baixado")
    
    # Para servidor
    print("\n4. Parando servidor...")
    server_process.terminate()
    server_process.wait()

def demo_with_loss_simulation():
    """Demonstra transferência com simulação de perda"""
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO: Transferência com Simulação de Perda")
    print("="*60)
    
    # Inicia servidor
    print("\n1. Iniciando servidor UDP...")
    server_process = run_command(
        "python3 server.py --port 8889",
        "Iniciando servidor UDP na porta 8889",
        background=True
    )
    
    if not wait_for_server(8889):
        print("✗ Falha ao iniciar servidor")
        server_process.terminate()
        return
    
    # Executa cliente com simulação de perda
    print("\n2. Executando cliente com simulação de perda...")
    run_command(
        "python3 client.py 127.0.0.1 8889 demo_file.txt --output-dir downloads_loss --simulate-loss --loss-probability 0.2",
        "Baixando arquivo com 20% de perda simulada"
    )
    
    # Para servidor
    server_process.terminate()
    server_process.wait()

def cleanup():
    """Remove arquivos de teste"""
    print("\n" + "="*60)
    print("LIMPEZA: Removendo arquivos de teste")
    print("="*60)
    
    files_to_remove = [
        "demo_file.txt",
        "downloads/demo_file.txt",
        "downloads_loss/demo_file.txt"
    ]
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✓ Removido: {file_path}")
    
    # Remove diretórios vazios
    dirs_to_remove = ["downloads", "downloads_loss"]
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path) and not os.listdir(dir_path):
            os.rmdir(dir_path)
            print(f"✓ Removido diretório vazio: {dir_path}")

def main():
    """Função principal"""
    print("SISTEMA UDP DE TRANSFERÊNCIA DE ARQUIVOS")
    print("Demonstração Completa")
    print("="*60)
    
    try:
        # Demonstração Hello World
        demo_hello_world()
        
        # Demonstração transferência de arquivos
        demo_file_transfer()
        
        # Demonstração com simulação de perda
        demo_with_loss_simulation()
        
        print("\n" + "="*60)
        print("✓ TODAS AS DEMONSTRAÇÕES CONCLUÍDAS COM SUCESSO!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\nDemonstração interrompida pelo usuário")
    except Exception as e:
        print(f"\n\nErro durante demonstração: {e}")
    finally:
        # Pergunta se deve limpar arquivos
        try:
            response = input("\nDeseja remover arquivos de teste? (s/n): ").lower().strip()
            if response in ['s', 'sim', 'y', 'yes']:
                cleanup()
        except:
            pass
        
        print("\nDemonstração finalizada!")

if __name__ == "__main__":
    main()
