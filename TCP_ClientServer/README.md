# Cliente/Servidor TCP Multithread com Transferência de Arquivos e Chat

**Trabalho 2 - Redes de Computadores**

## 📋 Descrição do Projeto

Este projeto implementa uma aplicação cliente-servidor utilizando o protocolo TCP e programação de sockets. O servidor é capaz de lidar com múltiplos clientes concorrentemente usando threads e oferece funcionalidades como transferência de arquivos grandes com verificação de integridade SHA-256 e um sistema de chat bidirecional.

## 🎯 Objetivos Atendidos

- ✅ **Servidor TCP Multithread**: Suporte a múltiplos clientes simultâneos
- ✅ **Transferência de Arquivos**: Suporte a arquivos grandes (> 10 MB) com verificação SHA-256
- ✅ **Sistema de Chat**: Comunicação bidirecional entre servidor e clientes
- ✅ **Protocolo de Aplicação**: Protocolo customizado bem definido
- ✅ **Tratamento de Erros**: Robustez na comunicação e tratamento de falhas
- ✅ **Uso Direto de Sockets**: Implementação usando API de sockets diretamente

## 🏗️ Arquitetura do Sistema

### Servidor (`server.py`)
- **Multithread**: Uma thread principal + uma thread por cliente conectado
- **Gerenciamento de Clientes**: Controle de conexões ativas
- **Chat do Servidor**: Thread dedicada para entrada de comandos/chat do servidor
- **Transferência de Arquivos**: Cálculo de SHA-256 e envio segmentado

### Cliente (`client.py`)
- **Interface de Usuário**: Menu interativo para operações
- **Thread de Escuta**: Recebimento assíncrono de mensagens de chat
- **Verificação de Integridade**: Validação SHA-256 de arquivos recebidos
- **Gerenciamento de Downloads**: Organização de arquivos baixados

## 📡 Protocolo de Aplicação

### Formato das Mensagens
Todas as mensagens seguem o padrão: `[TAMANHO:4bytes][DADOS:UTF-8]`

### Requisições do Cliente
| Comando | Formato | Descrição |
|---------|---------|-----------|
| `SAIR` | `SAIR` | Solicita desconexão |
| `ARQUIVO` | `ARQUIVO:<nome_arquivo>` | Solicita download de arquivo |
| `CHAT` | `CHAT:<mensagem>` | Envia mensagem de chat |

### Respostas do Servidor
| Resposta | Formato | Descrição |
|----------|---------|-----------|
| `OK` | `OK` | Operação bem-sucedida |
| `ERRO` | `ERRO` | Erro genérico |
| `ARQUIVO_NAO_ENCONTRADO` | `ARQUIVO_NAO_ENCONTRADO` | Arquivo não existe |
| `Metadados de Arquivo` | `OK\|<nome>\|<tamanho>\|<sha256>` | Informações do arquivo |
| `Chat do Servidor` | `CHAT_SERVER\|<mensagem>` | Mensagem do servidor |
| `Chat de Cliente` | `CHAT_CLIENT\|<mensagem>` | Mensagem de outro cliente |

### Fluxo de Transferência de Arquivo
1. Cliente envia: `ARQUIVO:<nome>`
2. Servidor responde: `OK|<nome>|<tamanho>|<sha256>` ou `ARQUIVO_NAO_ENCONTRADO`
3. Se OK, servidor envia dados binários do arquivo
4. Cliente recebe, salva e verifica integridade SHA-256

## 📁 Estrutura do Projeto

```
TCP_ClientServer/
├── server.py                 # Servidor TCP multithread
├── client.py                 # Cliente TCP
├── create_test_files.py      # Script para criar arquivos de teste
├── README.md                 # Esta documentação
├── server_files/             # Diretório de arquivos do servidor
│   ├── arquivo_pequeno.txt   # 10 KB
│   ├── arquivo_medio.txt     # 1 MB
│   ├── arquivo_grande.txt    # 5 MB
│   ├── arquivo_muito_grande.txt # 15 MB (> 10 MB)
│   ├── dados_binarios.bin    # 2 MB binário
│   ├── documento.txt         # 500 KB
│   └── readme_demo.txt       # Arquivo de demonstração
└── client_downloads/         # Diretório de downloads do cliente
```

## 🚀 Como Executar

### Pré-requisitos
- Python 3.6 ou superior
- Sistema operacional: Windows, Linux ou macOS

### Passo 1: Preparar Arquivos de Teste
```bash
cd TCP_ClientServer
python create_test_files.py
```

### Passo 2: Iniciar o Servidor
```bash
python server.py
```
- Digite o endereço IP (Enter para localhost)
- Digite a porta (Enter para 8888)
- O servidor estará pronto para receber conexões

### Passo 3: Conectar Clientes
Em terminais separados:
```bash
python client.py
```
- Digite o endereço IP do servidor
- Digite a porta do servidor
- Use o menu interativo para operações

## 🎮 Funcionalidades Demonstradas

### 1. Multithreading
- Execute múltiplos clientes simultaneamente
- Cada cliente opera independentemente
- Chat funciona entre todos os clientes conectados

### 2. Transferência de Arquivos
- Teste com `arquivo_muito_grande.txt` (15 MB)
- Verificação automática de integridade SHA-256
- Suporte a arquivos binários e de texto

### 3. Sistema de Chat
- **Cliente → Servidor**: Mensagens via menu do cliente
- **Servidor → Clientes**: Digite mensagens no console do servidor
- **Broadcast**: Mensagens são enviadas para todos os clientes

### 4. Comandos do Servidor
| Comando | Descrição |
|---------|-----------|
| `<mensagem>` | Envia mensagem para todos os clientes |
| `/status` | Mostra clientes conectados |
| `/help` | Mostra comandos disponíveis |
| `/quit` | Encerra o servidor |

### 5. Tratamento de Erros
- Arquivo não encontrado
- Conexão perdida durante transferência
- Verificação de integridade falha
- Cliente desconecta inesperadamente

## 🔧 Detalhes Técnicos

### Implementação de Sockets
- **Socket TCP**: `socket.AF_INET, socket.SOCK_STREAM`
- **Reutilização de Porta**: `SO_REUSEADDR`
- **Comunicação Bidirecional**: Full-duplex

### Gerenciamento de Threads
- **Thread Principal**: Aceita novas conexões
- **Thread por Cliente**: Gerencia comunicação individual
- **Thread de Chat**: Entrada do servidor (daemon)
- **Thread de Escuta**: Recebimento de mensagens no cliente (daemon)

### Verificação de Integridade
- **Algoritmo**: SHA-256
- **Implementação**: `hashlib.sha256()`
- **Verificação**: Comparação de hash calculado vs recebido

### Transferência de Arquivos Grandes
- **Segmentação**: Blocos de 4KB
- **Progresso**: Indicador para arquivos > 1MB
- **Robustez**: Tratamento de interrupções

## 🧪 Cenários de Teste

### Teste 1: Múltiplos Clientes
1. Inicie o servidor
2. Conecte 3+ clientes simultaneamente
3. Verifique chat entre todos os clientes

### Teste 2: Arquivo Grande
1. Solicite `arquivo_muito_grande.txt` (15 MB)
2. Verifique progresso da transferência
3. Confirme integridade SHA-256

### Teste 3: Chat Bidirecional
1. Cliente envia mensagem via menu
2. Servidor envia mensagem via console
3. Verifique recebimento em todos os clientes

### Teste 4: Tratamento de Erros
1. Solicite arquivo inexistente
2. Desconecte cliente durante transferência
3. Verifique recuperação do servidor

## 📊 Métricas de Performance

### Arquivos de Teste Incluídos
| Arquivo | Tamanho | Tipo | Propósito |
|---------|---------|------|-----------|
| `arquivo_pequeno.txt` | 10 KB | Texto | Teste básico |
| `arquivo_medio.txt` | 1 MB | Texto | Teste médio |
| `arquivo_grande.txt` | 5 MB | Texto | Teste grande |
| `arquivo_muito_grande.txt` | 15 MB | Texto | **Requisito > 10 MB** |
| `dados_binarios.bin` | 2 MB | Binário | Teste binário |
| `documento.txt` | 500 KB | Texto | Teste documento |

### Capacidades Testadas
- ✅ Arquivos > 10 MB
- ✅ Múltiplos clientes simultâneos
- ✅ Verificação SHA-256
- ✅ Chat bidirecional
- ✅ Tratamento de erros
- ✅ Robustez de conexão

## 🔍 Demonstração em Vídeo

### Roteiro de Demonstração
1. **Inicialização**
   - Mostrar estrutura de arquivos
   - Iniciar servidor
   - Conectar múltiplos clientes

2. **Funcionalidades Obrigatórias**
   - Multithreading (2+ clientes simultâneos)
   - Chat bidirecional
   - Transferência de arquivo > 10 MB
   - Verificação SHA-256
   - Tratamento de erro (arquivo não encontrado)

3. **Explicação do Código**
   - Protocolo de aplicação
   - Implementação multithread
   - Cálculo SHA-256
   - Gerenciamento de sockets

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3
- **Bibliotecas Padrão**:
  - `socket`: Comunicação TCP
  - `threading`: Programação multithread
  - `hashlib`: Cálculo SHA-256
  - `os`: Operações de arquivo
  - `sys`: Controle do sistema

## 👨‍💻 Autor

**Trabalho 2 - Redes de Computadores**
- Implementação completa do protocolo TCP
- Sistema multithread robusto
- Verificação de integridade de arquivos
- Interface de usuário intuitiva

## 📝 Notas de Implementação

### Decisões de Projeto
1. **Protocolo Binário**: Tamanho da mensagem em 4 bytes + dados UTF-8
2. **SHA-256**: Escolhido por segurança e disponibilidade
3. **Threads Daemon**: Para limpeza automática de recursos
4. **Blocos de 4KB**: Otimização entre memória e performance

### Robustez
- Tratamento de exceções em todas as operações de rede
- Limpeza automática de recursos
- Recuperação de erros de conexão
- Validação de entrada do usuário

### Escalabilidade
- Suporte teórico a centenas de clientes simultâneos
- Uso eficiente de memória para arquivos grandes
- Threads independentes por cliente

---

**🎯 Todos os requisitos do trabalho foram implementados e testados com sucesso!**

