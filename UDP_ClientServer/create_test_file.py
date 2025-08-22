#!/usr/bin/env python3
"""
Script para criar arquivo de teste grande para demonstrar a segmentação UDP
"""

import os
import random
import string

def create_test_file(filename: str, size_mb: float = 2.0):
    """Cria um arquivo de teste com tamanho especificado em MB"""
    size_bytes = size_mb * 1024 * 1024
    
    print(f"Criando arquivo de teste: {filename}")
    print(f"Tamanho: {size_mb} MB ({size_bytes} bytes)")
    
    with open(filename, 'w') as f:
        # Gera conteúdo aleatório
        chunk_size = 1024  # 1KB por vez
        remaining = size_bytes
        
        while remaining > 0:
            # Gera linha de texto aleatória
            line_length = int(min(chunk_size, remaining))
            line = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=line_length))
            
            f.write(line)
            remaining -= line_length
            
            # Adiciona quebra de linha a cada 80 caracteres para legibilidade
            if remaining > 0 and line_length == chunk_size:
                f.write('\n')
                remaining -= 1
    
    actual_size = os.path.getsize(filename)
    print(f"Arquivo criado com sucesso!")
    print(f"Tamanho real: {actual_size} bytes")
    print(f"Diferença: {actual_size - size_bytes} bytes")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cria arquivo de teste para demonstração UDP')
    parser.add_argument('--filename', default='test_file.txt', help='Nome do arquivo (padrão: test_file.txt)')
    parser.add_argument('--size', type=float, default=2.0, help='Tamanho em MB (padrão: 2.0)')
    
    args = parser.parse_args()
    
    if args.size <= 0:
        print("Erro: Tamanho deve ser maior que 0")
        return
    
    create_test_file(args.filename, args.size)

if __name__ == "__main__":
    main()
