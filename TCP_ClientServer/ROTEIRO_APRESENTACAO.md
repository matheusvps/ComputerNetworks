# 🎬 Roteiro de Apresentação - Projeto TCP Cliente/Servidor
**Trabalho 2 - Redes de Computadores**  
**Duração: 10 minutos**

---

## 📋 **PARTE 1: DEMONSTRAÇÃO PRÁTICA (5 minutos)**

### **⏱️ 0:00 - 0:30 | Introdução e Visão Geral**
- **Apresentação**: "Olá! Vou apresentar meu projeto de Cliente/Servidor TCP Multithread"
- **Mostrar estrutura do projeto**:
  ```
  TCP_ClientServer/
  ├── server.py          # Servidor multithread
  ├── client.py          # Cliente TCP
  ├── server_files/      # Arquivos para download
  └── client_downloads/  # Downloads dos clientes
  ```
- **Objetivos atendidos**: Multithreading, transferência de arquivos grandes, chat bidirecional, verificação SHA-256

### **⏱️ 0:30 - 1:30 | Inicialização do Sistema**
- **Iniciar o servidor**:
  ```bash
  python server.py
  ```
  - Mostrar configuração de IP e porta (localhost:8888)
  - Destacar mensagem: "Aguardando conexões..."
  - Explicar diretório de arquivos disponíveis

- **Mostrar arquivos de teste**:
  - `arquivo_muito_grande.txt` (15 MB) - **REQUISITO > 10 MB**
  - `dados_binarios.bin` (2 MB)
  - `arquivo_pequeno.txt` (10 KB)

### **⏱️ 1:30 - 2:30 | Multithreading - Múltiplos Clientes**
- **Conectar Cliente 1**:
  ```bash
  python client.py
  ```
  - Conectar em localhost:8888
  - Mostrar menu de opções
  - Destacar: "Cliente 1 conectado de ('127.0.0.1', porta)"

- **Conectar Cliente 2** (novo terminal):
  ```bash
  python client.py
  ```
  - Mostrar: "Cliente 2 conectado de ('127.0.0.1', porta)"
  - **DEMONSTRAR**: Servidor lidando com 2 clientes simultaneamente

### **⏱️ 2:30 - 3:30 | Chat Bidirecional**
- **Cliente → Servidor**:
  - Cliente 1: Escolher opção "3. Enviar mensagem de chat"
  - Digitar: "Olá do Cliente 1!"
  - Mostrar recebimento no servidor e broadcast para Cliente 2

- **Servidor → Clientes**:
  - No console do servidor, digitar: "Mensagem do servidor para todos!"
  - Mostrar recebimento em ambos os clientes
  - **DEMONSTRAR**: Chat funcionando bidirecionalmente

### **⏱️ 3:30 - 4:30 | Transferência de Arquivo Grande (>10MB)**
- **Cliente 1**: Solicitar arquivo grande
  - Escolher opção "2. Baixar arquivo"
  - Digitar: `arquivo_muito_grande.txt`
  - **MOSTRAR**:
    - Metadados recebidos (nome, tamanho: ~15MB, SHA-256)
    - Progresso da transferência em tempo real
    - "Arquivo recebido com sucesso!"

### **⏱️ 4:30 - 5:00 | Verificação de Integridade e Tratamento de Erro**
- **Verificação SHA-256**:
  - Mostrar: "Verificando integridade do arquivo..."
  - Resultado: "✅ Integridade verificada! Arquivo íntegro."

- **Tratamento de Erro**:
  - Cliente 2: Solicitar arquivo inexistente
  - Digitar: `arquivo_inexistente.txt`
  - Mostrar: "❌ Arquivo não encontrado no servidor"

---

## 💻 **PARTE 2: EXPLICAÇÃO DO CÓDIGO (5 minutos)**

### **⏱️ 5:00 - 6:00 | Protocolo de Aplicação**
- **Abrir `server.py` e `client.py`**
- **Explicar protocolo customizado**:
  ```python
  # Formato das mensagens: [TAMANHO:4bytes][DADOS:UTF-8]
  message_length = len(message_bytes)
  client_socket.send(message_length.to_bytes(4, byteorder='big'))
  client_socket.send(message_bytes)
  ```

- **Comandos implementados**:
  - `SAIR` - Desconexão limpa
  - `ARQUIVO:<nome>` - Solicitação de arquivo
  - `CHAT:<mensagem>` - Mensagem de chat

- **Respostas do servidor**:
  - `OK|<nome>|<tamanho>|<sha256>` - Metadados de arquivo
  - `ARQUIVO_NAO_ENCONTRADO` - Erro de arquivo
  - `CHAT_SERVER|<msg>` - Chat do servidor

### **⏱️ 6:00 - 7:00 | Implementação Multithread**
- **Mostrar código do servidor**:
  ```python
  # Thread principal aceita conexões
  client_socket, client_address = self.server_socket.accept()
  
  # Nova thread para cada cliente
  client_thread = threading.Thread(
      target=self.handle_client,
      args=(client_socket, client_address),
      daemon=True
  )
  client_thread.start()
  ```

- **Gerenciamento de clientes**:
  ```python
  self.clients[client_id] = {
      'socket': client_socket,
      'address': client_address,
      'connected_at': datetime.now()
  }
  ```

- **Thread de chat do servidor**:
  ```python
  chat_thread = threading.Thread(target=self.server_chat_input, daemon=True)
  ```

### **⏱️ 7:00 - 8:00 | Transferência de Arquivos e SHA-256**
- **Cálculo SHA-256**:
  ```python
  def calculate_sha256(self, file_path):
      sha256_hash = hashlib.sha256()
      with open(file_path, "rb") as f:
          for chunk in iter(lambda: f.read(4096), b""):
              sha256_hash.update(chunk)
      return sha256_hash.hexdigest()
  ```

- **Protocolo de transferência**:
  ```python
  # 1. Enviar metadados
  metadata = f"OK|{file_path}|{file_size}|{file_sha256}"
  self.send_message(client_socket, metadata)
  
  # 2. Aguardar confirmação
  confirmation = self.receive_message(client_socket)
  
  # 3. Enviar dados binários
  with open(full_path, 'rb') as f:
      while bytes_sent < file_size:
          chunk = f.read(16384)  # 16KB chunks
          client_socket.send(chunk)
  ```

### **⏱️ 8:00 - 8:30 | Uso Direto de Sockets TCP**
- **Criação do socket**:
  ```python
  # Servidor
  self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  self.server_socket.bind((self.host, self.port))
  self.server_socket.listen(5)
  
  # Cliente
  self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  self.client_socket.connect((host, port))
  ```

- **Destacar**: "Uso direto da API de sockets, sem bibliotecas que mascarem a implementação TCP"

### **⏱️ 8:30 - 9:30 | Robustez e Tratamento de Erros**
- **Tratamento de exceções**:
  ```python
  try:
      # Operações de rede
  except socket.timeout:
      # Timeout específico
  except socket.error as e:
      # Erros de socket
  except Exception as e:
      # Outros erros
  finally:
      # Limpeza de recursos
  ```

- **Verificação de integridade no cliente**:
  ```python
  received_hash = self.calculate_sha256(file_path)
  if received_hash == expected_hash:
      print("✅ Integridade verificada!")
  else:
      print("❌ Arquivo corrompido!")
  ```

- **Limpeza de recursos**:
  ```python
  def stop_server(self):
      for client_info in self.clients.values():
          client_info['socket'].close()
      self.server_socket.close()
  ```

### **⏱️ 9:30 - 10:00 | Conclusão e Requisitos Atendidos**
- **Resumo dos requisitos implementados**:
  - ✅ **Multithreading**: Múltiplos clientes simultâneos
  - ✅ **Transferência > 10MB**: `arquivo_muito_grande.txt` (15 MB)
  - ✅ **Verificação SHA-256**: Integridade garantida
  - ✅ **Chat Bidirecional**: Servidor ↔ Clientes
  - ✅ **Tratamento de Erros**: Arquivo não encontrado, conexão perdida
  - ✅ **Sockets TCP Diretos**: Sem bibliotecas que mascarem implementação
  - ✅ **Protocolo Customizado**: Bem definido e documentado

- **Tecnologias utilizadas**:
  - Python 3 com bibliotecas padrão
  - `socket`, `threading`, `hashlib`
  - Protocolo TCP puro

- **Encerramento**: "O projeto atende todos os requisitos solicitados, demonstrando uma implementação robusta e completa de um sistema cliente-servidor TCP multithread."

---

## 📝 **CHECKLIST DE DEMONSTRAÇÃO**

### **Itens Obrigatórios a Mostrar:**
- [ ] **Multithreading**: Pelo menos 2 clientes simultâneos
- [ ] **Funcionalidade "Sair"**: Desconexão limpa
- [ ] **Chat Bidirecional**: Cliente → Servidor e Servidor → Clientes
- [ ] **Transferência > 10MB**: `arquivo_muito_grande.txt` (15 MB)
- [ ] **Verificação SHA-256**: Integridade do arquivo
- [ ] **Tratamento de Erro**: Arquivo não encontrado
- [ ] **Robustez**: Sistema funcionando corretamente

### **Pontos Técnicos a Explicar:**
- [ ] **Protocolo de aplicação** customizado
- [ ] **Implementação multithread** no servidor
- [ ] **Cálculo SHA-256** para integridade
- [ ] **Uso direto de sockets TCP**
- [ ] **Tratamento de exceções** e robustez
- [ ] **Gerenciamento de recursos** e limpeza

---

## 🎯 **DICAS PARA GRAVAÇÃO**

### **Preparação:**
1. **Testar tudo antes** da gravação
2. **Fechar programas desnecessários** para melhor performance
3. **Aumentar fonte** dos terminais para melhor visualização
4. **Preparar arquivos de teste** com tamanhos adequados

### **Durante a Gravação:**
1. **Falar claramente** e em ritmo adequado
2. **Mostrar código relevante** enquanto explica
3. **Destacar pontos importantes** com cursor/mouse
4. **Manter cronograma** de 10 minutos

### **Estrutura Visual:**
- **Múltiplos terminais** organizados na tela
- **Editor de código** aberto com arquivos principais
- **Explorador de arquivos** mostrando estrutura do projeto

---

**🎬 Boa sorte com a apresentação! O projeto está completo e atende todos os requisitos.**

