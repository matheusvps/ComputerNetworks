#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar arquivos de teste para demonstração
Trabalho 2 - Redes de Computadores
"""

import os
import random
import string

def create_test_file(filename, size_mb, content_type="text"):
    """
    Cria um arquivo de teste com tamanho específico
    
    Args:
        filename (str): Nome do arquivo
        size_mb (float): Tamanho em MB
        content_type (str): Tipo de conteúdo ("text" ou "binary")
    """
    size_bytes = int(size_mb * 1024 * 1024)
    
    print(f"Criando arquivo: {filename} ({size_mb} MB)")
    
    with open(filename, 'wb' if content_type == "binary" else 'w', encoding='utf-8' if content_type == "text" else None) as f:
        if content_type == "text":
            # Cria conteúdo de texto
            chars = string.ascii_letters + string.digits + ' \n'
            content = ""
            
            while len(content.encode('utf-8')) < size_bytes:
                # Adiciona linhas de texto aleatório
                line_length = random.randint(50, 100)
                line = ''.join(random.choices(chars[:-2], k=line_length)) + '\n'
                content += line
                
                # Adiciona algumas linhas especiais para tornar o arquivo mais interessante
                if len(content) % 1000 == 0:
                    content += f"=== Linha especial {len(content)} ===\n"
            
            # Trunca para o tamanho exato
            content_bytes = content.encode('utf-8')
            if len(content_bytes) > size_bytes:
                content = content_bytes[:size_bytes].decode('utf-8', errors='ignore')
            
            f.write(content)
        
        else:
            # Cria conteúdo binário
            chunk_size = 4096
            written = 0
            
            while written < size_bytes:
                remaining = min(chunk_size, size_bytes - written)
                chunk = bytes([random.randint(0, 255) for _ in range(remaining)])
                f.write(chunk)
                written += remaining
    
    print(f"Arquivo criado: {filename} ({os.path.getsize(filename)} bytes)")

def main():
    """
    Cria arquivos de teste para demonstração
    """
    print("=== Criador de Arquivos de Teste ===")
    print("Trabalho 2 - Redes de Computadores")
    print()
    
    # Diretório de arquivos do servidor
    server_dir = "server_files"
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)
    
    os.chdir(server_dir)
    
    # Cria arquivos de diferentes tamanhos
    test_files = [
        ("arquivo_pequeno.txt", 0.01, "text"),      # 10 KB
        ("arquivo_medio.txt", 1.0, "text"),         # 1 MB
        ("arquivo_grande.txt", 5.0, "text"),        # 5 MB
        ("arquivo_muito_grande.txt", 15.0, "text"), # 15 MB (> 10 MB para requisito)
        ("dados_binarios.bin", 2.0, "binary"),     # 2 MB binário
        ("documento.txt", 0.5, "text"),             # 500 KB
    ]
    
    for filename, size_mb, content_type in test_files:
        if not os.path.exists(filename):
            create_test_file(filename, size_mb, content_type)
        else:
            print(f"Arquivo já existe: {filename}")
    
    # Cria um arquivo de texto com conteúdo específico
    readme_content = """=== ARQUIVO DE DEMONSTRAÇÃO ===
Trabalho 2 - Redes de Computadores
Cliente/Servidor TCP Multithread

Este arquivo foi criado automaticamente para demonstrar
a funcionalidade de transferência de arquivos do sistema.

Características do sistema:
- Servidor TCP multithread
- Transferência de arquivos com verificação SHA-256
- Sistema de chat bidirecional
- Suporte a arquivos grandes (> 10 MB)
- Tratamento de múltiplos clientes simultâneos

Protocolo de Aplicação:
- ARQUIVO:<nome> - Solicita arquivo
- CHAT:<mensagem> - Envia mensagem de chat
- SAIR - Desconecta do servidor

Data de criação: """ + str(os.path.getctime(__file__) if os.path.exists(__file__) else "N/A") + """

=== FIM DO ARQUIVO ===
"""
    
    with open("readme_demo.txt", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("\n=== Resumo dos Arquivos Criados ===")
    files = os.listdir(".")
    total_size = 0
    
    for filename in sorted(files):
        if os.path.isfile(filename):
            size = os.path.getsize(filename)
            total_size += size
            
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            
            print(f"  {filename:<25} {size_str:>10}")
    
    print(f"\nTotal: {total_size / (1024 * 1024):.1f} MB")
    print(f"Diretório: {os.path.abspath('.')}")

if __name__ == "__main__":
    main()

