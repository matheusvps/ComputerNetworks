#!/bin/bash

# Script de Instalação e Verificação do Sistema UDP
# Este script verifica dependências e testa a instalação

echo "=========================================="
echo "INSTALAÇÃO DO SISTEMA UDP DE TRANSFERÊNCIA"
echo "=========================================="

# Verifica se Python 3 está instalado
echo "Verificando Python 3..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "✓ Python 3 encontrado: $PYTHON_VERSION"
else
    echo "✗ Python 3 não encontrado!"
    echo "Por favor, instale Python 3.6+ e tente novamente."
    exit 1
fi

# Verifica versão mínima do Python
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 6 ]); then
    echo "✗ Python 3.6+ é necessário. Versão atual: $PYTHON_MAJOR.$PYTHON_MINOR"
    exit 1
fi

echo "✓ Versão do Python é compatível: $PYTHON_MAJOR.$PYTHON_MINOR"

# Verifica se os arquivos principais existem
echo -e "\nVerificando arquivos do sistema..."
REQUIRED_FILES=(
    "server.py"
    "client.py"
    "hello_world_udp.py"
    "create_test_file.py"
    "demo.py"
    "test_simple.py"
    "config.py"
    "README.md"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (faltando)"
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo -e "\n✗ Arquivos faltando: ${MISSING_FILES[*]}"
    echo "Por favor, certifique-se de que todos os arquivos estão presentes."
    exit 1
fi

# Verifica permissões de execução
echo -e "\nConfigurando permissões de execução..."
chmod +x *.py

# Testa imports básicos
echo -e "\nTestando imports básicos..."
python3 -c "
import socket
import struct
import hashlib
import os
import time
import threading
import logging
import argparse
print('✓ Todas as bibliotecas padrão importadas com sucesso')
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ Imports básicos funcionando"
else
    echo "✗ Erro nos imports básicos"
    exit 1
fi

# Valida configurações
echo -e "\nValidando configurações..."
python3 config.py 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ Configurações válidas"
else
    echo "✗ Erro nas configurações"
    exit 1
fi

# Executa teste simples
echo -e "\nExecutando teste simples..."
python3 test_simple.py

if [ $? -eq 0 ]; then
    echo -e "\n🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
    echo -e "\nPara começar a usar o sistema:"
    echo "1. Demonstração completa: python3 demo.py"
    echo "2. Exemplo Hello World: python3 hello_world_udp.py [server|client]"
    echo "3. Transferência de arquivos:"
    echo "   - Servidor: python3 server.py --port 8888"
    echo "   - Cliente: python3 client.py 127.0.0.1 8888 nome_do_arquivo.txt"
    echo -e "\nConsulte o README.md para mais informações."
else
    echo -e "\n⚠️  ALGUNS TESTES FALHARAM."
    echo "Verifique os erros acima e tente novamente."
    exit 1
fi

echo -e "\n=========================================="
echo "INSTALAÇÃO FINALIZADA"
echo "=========================================="
