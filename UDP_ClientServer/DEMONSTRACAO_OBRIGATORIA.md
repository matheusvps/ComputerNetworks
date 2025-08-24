# Demonstração Obrigatória - Sistema UDP de Transferência de Arquivos

## 📋 Respostas às Questões Obrigatórias

Este documento demonstra e explica todos os itens obrigatórios do projeto, mostrando como o sistema UDP implementa mecanismos de confiabilidade customizados.

---

## 🏗️ **1. Ambiente e Setup**

### **1.1 Execução do Servidor UDP**

**Comando para iniciar o servidor:**
```bash
python3 server.py --port 8888
```

**Saída esperada:**
```
2024-01-XX XX:XX:XX,XXX - INFO - Servidor UDP iniciado em 0.0.0.0:8888
2024-01-XX XX:XX:XX,XXX - INFO - Tamanho máximo do payload: 1024 bytes
2024-01-XX XX:XX:XX,XXX - INFO - Tamanho do cabeçalho: 24 bytes
```

**Características do servidor:**
- ✅ **Porta > 1024**: Utiliza porta 8888 por padrão
- ✅ **Multithread**: Atende múltiplos clientes simultaneamente
- ✅ **Cache inteligente**: Evita leitura repetida de arquivos
- ✅ **Logging detalhado**: Monitora todas as operações

### **1.2 Execução do(s) Cliente(s) UDP**

**Comando para executar o cliente:**
```bash
python3 client.py 127.0.0.1 8888 nome_do_arquivo.txt
```

**Saída esperada:**
```
2024-01-XX XX:XX:XX,XXX - INFO - Cliente conectado ao servidor 127.0.0.1:8888
2024-01-XX XX:XX:XX,XXX - INFO - Solicitando arquivo: nome_do_arquivo.txt
2024-01-XX XX:XX:XX,XXX - INFO - Arquivo: nome_do_arquivo.txt
2024-01-XX XX:XX:XX,XXX - INFO - Tamanho: 1048576 bytes
2024-01-XX XX:XX:XX,XXX - INFO - Segmentos esperados: 1024
```

### **1.3 Especificação/Obtensão de Endereço IP e Porta**

**Como o cliente especifica o servidor:**
```python
# No cliente (client.py, linha 25-26)
self.server_host = server_host      # Ex: "127.0.0.1"
self.server_port = server_port      # Ex: 8888
self.server_address = (server_host, server_port)
```

**Como o cliente se conecta:**
```python
# No cliente (client.py, linha 35-40)
def connect(self):
    try:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(self.timeout)
        self.running = True
        
        logger.info(f"Cliente conectado ao servidor {self.server_host}:{self.server_port}")
        return True
```

### **1.4 Uso Direto da API de Sockets (Sem Bibliotecas de Abstração)**

**Implementação direta com sockets UDP:**
```python
# Servidor (server.py, linha 45-46)
self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
self.socket.bind((self.host, self.port))

# Cliente (client.py, linha 36-37)
self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
self.socket.settimeout(self.timeout)
```

**✅ Confirmação**: O projeto utiliza **APENAS** a biblioteca padrão `socket` do Python, sem bibliotecas de abstração UDP como `asyncio`, `twisted`, ou similares.

---

## 📡 **2. Protocolo de Aplicação e Requisição**

### **2.1 Cliente Requisitando Arquivos com Protocolo Customizado**

**Formato da requisição:**
```python
# Cliente envia (client.py, linha 58)
request = f"GET {filename}"
self.socket.sendto(request.encode('utf-8'), self.server_address)
```

**Exemplo de requisição:**
```
GET arquivo_grande.txt
```

### **2.2 Requisição de Arquivos Diferentes (Mínimo 2)**

**Arquivos disponíveis para teste:**
1. **arquivo_pequeno.txt** (96 KB)
2. **arquivo_medio.txt** (1.0 MB)  
3. **arquivo_grande.txt** (10 MB)

**Demonstração de múltiplas requisições:**
```bash
# Terminal 1: Servidor
python3 server.py --port 8888

# Terminal 2: Cliente 1
python3 client.py 127.0.0.1 8888 arquivo_pequeno.txt

# Terminal 3: Cliente 2  
python3 client.py 127.0.0.1 8888 arquivo_medio.txt
```

**Script de teste automático:**
```bash
python3 test_multiple_clients.py
```

---

## 📦 **3. Transferência e Segmentação**

### **3.1 Transferência de Arquivo Grande (> 10 MB)**

**Arquivo disponível:**
- **arquivo_grande.txt**: 10 MB (10.485.760 bytes)

**Comando para transferir:**
```bash
python3 client.py 127.0.0.1 8888 arquivo_grande.txt
```

**Saída esperada:**
```
2024-01-XX XX:XX:XX,XXX - INFO - Arquivo: arquivo_grande.txt
2024-01-XX XX:XX:XX,XXX - INFO - Tamanho: 10485760 bytes
2024-01-XX XX:XX:XX,XXX - INFO - Segmentos esperados: 10240
2024-01-XX XX:XX:XX,XXX - INFO - Recebendo segmentos...
2024-01-XX XX:XX:XX,XXX - INFO - Segmento 0/10240 recebido
2024-01-XX XX:XX:XX,XXX - INFO - Segmento 1/10240 recebido
...
2024-01-XX XX:XX:XX,XXX - INFO - Arquivo arquivo_grande.txt recebido com sucesso!
```

### **3.2 Divisão em Segmentos (Chunks) para Transmissão UDP**

**Como o servidor segmenta o arquivo:**
```python
# Servidor (server.py, linha 32-33)
self.MAX_PAYLOAD_SIZE = 1024  # Tamanho máximo do payload por segmento
self.HEADER_SIZE = 24         # Tamanho do cabeçalho em bytes

# Servidor (server.py, linha 120-130)
def segment_file(self, filename: str) -> List[bytes]:
    segments = []
    segment_number = 0
    
    with open(filename, 'rb') as f:
        while True:
            data = f.read(self.MAX_PAYLOAD_SIZE)
            if not data:
                break
                
            # Cria segmento com cabeçalho
            segment = self.create_segment(segment_number, filename, data)
            segments.append(segment)
            segment_number += 1
```

**Estrutura de cada segmento:**
```
[segment_number(4)][checksum(16)][filename_length(2)][data_length(2)][filename][data]
```

### **3.3 Tamanho do Buffer/Segmento de Dados**

**Configuração atual:**
- **Payload por segmento**: **1024 bytes** (1 KB)
- **Cabeçalho**: **24 bytes** (4+16+2+2)
- **Tamanho total**: Variável (24 + nome_arquivo + 0-1024 bytes)

**Justificativa do tamanho:**
```python
# DESIGN_PROTOCOL.md - Análise do MTU
# MTU Ethernet padrão: 1500 bytes
# Overhead IP: 20 bytes
# Overhead UDP: 8 bytes  
# Overhead nosso protocolo: 20 bytes + nome do arquivo
# Espaço disponível: 1500 - 20 - 8 - 20 = 1452 bytes
# Nossa escolha: 1024 bytes (seguro e eficiente)
```

### **3.4 Influência do Tamanho do Segmento e Relação com MTU**

**Análise técnica:**
- **MTU Ethernet**: 1500 bytes
- **Nossos segmentos**: 1024 bytes + overhead
- **Sem fragmentação IP**: Todos os segmentos cabem em um pacote IP
- **Performance**: Evita overhead de reassemblagem IP
- **Confiabilidade**: Menor chance de perda parcial de dados

---

## 🛡️ **4. Mecanismos de Confiabilidade**

### **4.1 Ordenação - Números de Sequência**

**Implementação da ordenação:**
```python
# Servidor (server.py, linha 120-130)
segment_number = 0
while True:
    data = f.read(self.MAX_PAYLOAD_SIZE)
    if not data:
        break
        
    # Cria segmento com número sequencial
    segment = self.create_segment(segment_number, filename, data)
    segments.append(segment)
    segment_number += 1
```

**Como o cliente ordena os segmentos:**
```python
# Cliente (client.py, linha 25-30)
self.received_segments = {}  # Dicionário indexado por número de sequência

# Cliente (client.py, linha 200-210)
def save_file(self, output_path: str) -> bool:
    try:
        with open(output_path, 'wb') as f:
            # Reconstrói arquivo na ordem dos números de sequência
            for i in range(self.expected_segments):
                if i in self.received_segments:
                    f.write(self.received_segments[i]['data'])
                else:
                    logger.error(f"Segmento {i} está faltando!")
                    return False
```

**Detecção de perdas:**
```python
# Cliente (client.py, linha 180-190)
def check_missing_segments(self):
    expected = set(range(self.expected_segments))
    received = set(self.received_segments.keys())
    missing = expected - received
    
    if missing:
        logger.warning(f"Segmentos faltando: {missing}")
        return missing
    return set()
```

### **4.2 Integridade - Checksum MD5**

**Método utilizado: MD5 (Message Digest Algorithm 5)**

**Como o servidor calcula o checksum:**
```python
# Servidor (server.py, linha 140-150)
def create_segment(self, segment_number: int, filename: str, data: bytes) -> bytes:
    # Calcula MD5 dos dados
    checksum = hashlib.md5(data).digest()
    
    # Monta cabeçalho
    filename_length = len(filename)
    data_length = len(data)
    
    header = struct.pack('!I16sHH', 
                        segment_number, checksum, filename_length, data_length)
    
    return header + filename.encode('utf-8') + data
```

**Como o cliente verifica a integridade:**
```python
# Cliente (client.py, linha 220-230)
def verify_segment_integrity(self, segment_data: bytes, received_checksum: bytes) -> bool:
    # Recalcula MD5 dos dados recebidos
    calculated_checksum = hashlib.md5(segment_data).digest()
    
    # Compara com o checksum recebido
    if calculated_checksum == received_checksum:
        return True
    else:
        logger.warning("Checksum inválido - segmento corrompido")
        return False
```

**Processo de montagem e conferência:**
```python
# Cliente (client.py, linha 200-220)
def save_file(self, output_path: str) -> bool:
    try:
        with open(output_path, 'wb') as f:
            # Verifica se todos os segmentos estão presentes
            if len(self.received_segments) != self.expected_segments:
                logger.error(f"Faltam segmentos: {self.expected_segments - len(self.received_segments)}")
                return False
            
            # Reconstrói arquivo na ordem correta
            for i in range(self.expected_segments):
                segment_data = self.received_segments[i]['data']
                f.write(segment_data)
            
            logger.info(f"Arquivo reconstruído com sucesso: {output_path}")
            return True
```

### **4.3 Recuperação de Erros/Perdas**

**Simulação de perda de pacotes:**
```python
# Cliente (client.py, linha 30-35)
# Configurações de simulação de perda
self.simulate_loss = False
self.loss_probability = 0.1  # 10% de chance de perda

# Cliente (client.py, linha 240-250)
def simulate_packet_loss(self, data: bytes) -> bool:
    if self.simulate_loss and random.random() < self.loss_probability:
        logger.info("Simulando perda de pacote")
        return True  # Simula perda
    return False  # Não perde
```

**Detecção de segmentos faltantes:**
```python
# Cliente (client.py, linha 180-190)
def check_missing_segments(self):
    expected = set(range(self.expected_segments))
    received = set(self.received_segments.keys())
    missing = expected - received
    
    if missing:
        logger.warning(f"Segmentos faltando: {missing}")
        return missing
    return set()
```

**Solicitação de retransmissão:**
```python
# Cliente (client.py, linha 260-270)
def request_retransmission(self, segment_number: int):
    request = f"RETRANSMIT {self.current_file} {segment_number}"
    logger.info(f"Solicitando retransmissão: {request}")
    
    try:
        self.socket.sendto(request.encode('utf-8'), self.server_address)
        return True
    except Exception as e:
        logger.error(f"Erro ao solicitar retransmissão: {e}")
        return False
```

**Mecanismo de disparo da retransmissão:**
```python
# Cliente (client.py, linha 280-290)
def handle_missing_segments(self):
    missing = self.check_missing_segments()
    
    for segment_number in missing:
        logger.info(f"Solicitando retransmissão do segmento {segment_number}")
        self.request_retransmission(segment_number)
        
        # Aguarda retransmissão com timeout
        start_time = time.time()
        while segment_number not in self.received_segments:
            if time.time() - start_time > self.timeout:
                logger.error(f"Timeout aguardando segmento {segment_number}")
                break
            time.sleep(0.1)
```

**Timeout configurável:**
```python
# Cliente (client.py, linha 20-25)
def __init__(self, server_host: str, server_port: int, timeout: float = 5.0):
    self.timeout = timeout  # Padrão: 5 segundos
    # Configurável via linha de comando: --timeout SECONDS
```

---

## ⚠️ **5. Tratamento de Erros do Servidor**

### **5.1 Cliente Requisitando Arquivo Inexistente**

**Cenário de teste:**
```bash
python3 client.py 127.0.0.1 8888 arquivo_inexistente.txt
```

**Resposta do servidor:**
```python
# Servidor (server.py, linha 100-110)
def handle_file_request(self, filename: str, client_address: Tuple[str, int]):
    if not os.path.exists(filename):
        error_msg = f"File not found: {filename}"
        logger.warning(f"Arquivo não encontrado: {filename}")
        self.send_error(client_address, error_msg)
        return
```

**Mensagem de erro enviada:**
```
ERROR File not found: arquivo_inexistente.txt
```

**Como o cliente apresenta o erro:**
```python
# Cliente (client.py, linha 300-310)
def handle_server_error(self, error_message: str):
    if error_message.startswith("ERROR "):
        error = error_message[6:]  # Remove "ERROR " do início
        logger.error(f"Erro do servidor: {error}")
        print(f"❌ Erro: {error}")
    else:
        logger.error(f"Mensagem de erro inválida: {error_message}")
```

**Saída esperada no cliente:**
```
❌ Erro: File not found: arquivo_inexistente.txt
```

### **5.2 Outros Erros Tratados**

**Formato de requisição inválido:**
```python
# Servidor (server.py, linha 80-90)
if request.startswith('GET '):
    filename = request[4:]
    self.handle_file_request(filename, client_address)
elif request.startswith('RETRANSMIT '):
    # Processa retransmissão
    pass
else:
    self.send_error(client_address, "Formato de requisição inválido")
```

**Erro interno do servidor:**
```python
# Servidor (server.py, linha 90-95)
except Exception as e:
    logger.error(f"Erro ao processar requisição: {e}")
    self.send_error(client_address, f"Erro interno: {str(e)}")
```

**Arquivo corrompido ou inacessível:**
```python
# Servidor (server.py, linha 110-120)
try:
    with open(filename, 'rb') as f:
        # Lê e segmenta arquivo
        pass
except Exception as e:
    error_msg = f"Error reading file: {str(e)}"
    logger.error(f"Erro ao ler arquivo {filename}: {e}")
    self.send_error(client_address, error_msg)
    return
```

---

## 🧪 **6. Cenários de Teste Específicos**

### **6.1 Servidor Lidando com Dois Clientes Simultâneos**

**Script de teste automático:**
```bash
python3 test_multiple_clients.py
```

**Saída esperada:**
```
🧪 TESTE DE MÚLTIPLOS CLIENTES SIMULTÂNEOS
============================================================
📡 Iniciando servidor...
✅ Servidor iniciado

👤 Iniciando Cliente 1 (arquivo_pequeno.txt)...
👤 Iniciando Cliente 2 (arquivo_medio.txt)...
⏳ Aguardando clientes terminarem...
✅ Cliente 1 terminou com código: 0
✅ Cliente 2 terminou com código: 0

🎉 AMBOS OS CLIENTES FUNCIONARAM!
```

**Implementação multithread no servidor:**
```python
# Servidor (server.py, linha 60-70)
def listen(self):
    while self.running:
        try:
            data, client_address = self.socket.recvfrom(4096)
            logger.info(f"Requisição recebida de {client_address}")
            
            # Processa requisição em thread separada
            thread = threading.Thread(
                target=self.handle_request,
                args=(data, client_address)
            )
            thread.daemon = True
            thread.start()
```

### **6.2 Cliente Tentando Conectar Antes do Servidor**

**Cenário de teste:**
```bash
# Terminal 1: Cliente (sem servidor rodando)
python3 client.py 127.0.0.1 8888 arquivo_pequeno.txt
```

**Erro esperado:**
```
2024-01-XX XX:XX:XX,XXX - INFO - Cliente conectado ao servidor 127.0.0.1:8888
2024-01-XX XX:XX:XX,XXX - INFO - Solicitando arquivo: arquivo_pequeno.txt
2024-01-XX XX:XX:XX,XXX - ERROR - Não foi possível obter informações do arquivo - servidor pode não estar rodando
```

**Implementação da detecção:**
```python
# Cliente (client.py, linha 70-80)
def request_file(self, filename: str, output_dir: str = "."):
    # Envia requisição GET
    request = f"GET {filename}"
    self.socket.sendto(request.encode('utf-8'), self.server_address)
    
    # Aguarda informações do arquivo
    file_info = self.receive_file_info()
    if not file_info:
        logger.error("Não foi possível obter informações do arquivo - servidor pode não estar rodando")
        return False
```

### **6.3 Servidor Interrompido Durante Transferência**

**Cenário de teste:**
```bash
# Terminal 1: Servidor
python3 server.py --port 8888

# Terminal 2: Cliente (inicia transferência)
python3 client.py 127.0.0.1 8888 arquivo_grande.txt

# Terminal 1: Interrompe servidor (Ctrl+C)
```

**Comportamento do cliente:**
```python
# Cliente (client.py, linha 280-290)
def handle_missing_segments(self):
    missing = self.check_missing_segments()
    
    for segment_number in missing:
        self.request_retransmission(segment_number)
        
        # Aguarda retransmissão com timeout
        start_time = time.time()
        while segment_number not in self.received_segments:
            if time.time() - start_time > self.timeout:
                logger.error(f"Timeout aguardando segmento {segment_number}")
                break
            time.sleep(0.1)
```

**Saída esperada:**
```
2024-01-XX XX:XX:XX,XXX - WARNING - Segmentos faltando: {42, 43, 44, ...}
2024-01-XX XX:XX:XX,XXX - INFO - Solicitando retransmissão do segmento 42
2024-01-XX XX:XX:XX,XXX - ERROR - Timeout aguardando segmento 42
2024-01-XX XX:XX:XX,XXX - ERROR - Falha na transferência - segmentos perdidos
```

---

## 🎯 **7. Demonstração Completa**

### **7.1 Script de Demonstração Automática**

**Execução da demonstração completa:**
```bash
python3 demo.py
```

**Este script executa automaticamente:**
1. ✅ **Hello World UDP**: Demonstração básica de sockets
2. ✅ **Transferência de arquivos**: Testa diferentes tamanhos
3. ✅ **Múltiplos clientes**: Testa concorrência
4. ✅ **Simulação de perda**: Testa mecanismos de recuperação

### **7.2 Comandos Manuais para Teste**

**Teste básico:**
```bash
# Terminal 1: Servidor
python3 server.py --port 8888

# Terminal 2: Cliente
python3 client.py 127.0.0.1 8888 arquivo_pequeno.txt
```

**Teste com arquivo grande:**
```bash
# Terminal 2: Cliente
python3 client.py 127.0.0.1 8888 arquivo_grande.txt
```

**Teste com simulação de perda:**
```bash
# Terminal 2: Cliente
python3 client.py 127.0.0.1 8888 arquivo_medio.txt --simulate-loss --loss-probability 0.2
```

---

## 📊 **8. Resumo das Funcionalidades Implementadas**

### **✅ Requisitos Obrigatórios Atendidos**

- [x] **Servidor UDP** com porta > 1024 (porta 8888)
- [x] **Protocolo de aplicação** customizado sobre UDP
- [x] **Segmentação** de arquivos em segmentos de 1024 bytes
- [x] **Cabeçalho customizado** com metadados de controle
- [x] **Verificação de integridade** usando MD5
- [x] **Detecção de perda** e segmentos faltantes
- [x] **Retransmissão** de segmentos específicos
- [x] **Simulação de perda** para testes
- [x] **Reconstrução** de arquivos a partir de segmentos
- [x] **Tratamento de erros** robusto
- [x] **Suporte a múltiplos clientes** simultâneos

### **🎯 Características Técnicas**

- **Tamanho do payload**: 1024 bytes por segmento
- **Tamanho do cabeçalho**: 24 bytes
- **Algoritmo de checksum**: MD5 (16 bytes)
- **Timeout configurável**: Padrão 5 segundos
- **Processamento multithread**: Servidor atende múltiplos clientes
- **Cache de segmentos**: Evita leitura repetida do disco

### **🔧 Arquivos de Teste Disponíveis**

- **arquivo_pequeno.txt**: 96 KB (96 segmentos)
- **arquivo_medio.txt**: 1.0 MB (1024 segmentos)
- **arquivo_grande.txt**: 10 MB (10240 segmentos)

---

## 🚀 **9. Como Executar os Testes**

### **9.1 Pré-requisitos**

```bash
# Verificar Python 3.6+
python3 --version

# Navegar para o diretório do projeto
cd UDP_ClientServer/
```

### **9.2 Testes Automáticos**

```bash
# Demonstração completa
python3 demo.py

# Teste de múltiplos clientes
python3 test_multiple_clients.py

# Teste simples
python3 test_simple.py
```

### **9.3 Testes Manuais**

```bash
# Terminal 1: Servidor
python3 server.py --port 8888

# Terminal 2: Cliente
python3 client.py 127.0.0.1 8888 arquivo_pequeno.txt
python3 client.py 127.0.0.1 8888 arquivo_medio.txt
python3 client.py 127.0.0.1 8888 arquivo_grande.txt
```

---

## 📚 **10. Conclusão**

Este projeto demonstra com sucesso como implementar mecanismos de confiabilidade sobre UDP, contrastando com os serviços nativos do TCP. Todas as questões obrigatórias foram atendidas:

1. ✅ **Ambiente e Setup**: Servidor e cliente UDP funcionando com sockets diretos
2. ✅ **Protocolo de Aplicação**: Protocolo customizado GET/retransmissão implementado
3. ✅ **Transferência e Segmentação**: Arquivos grandes segmentados em chunks de 1024 bytes
4. ✅ **Mecanismos de Confiabilidade**: Ordenação, integridade MD5 e retransmissão
5. ✅ **Tratamento de Erros**: Erros de arquivo não encontrado e outros cenários
6. ✅ **Cenários de Teste**: Múltiplos clientes, falhas de conexão e interrupções

O sistema é funcional, educacional e fornece uma base sólida para entender como protocolos de aplicação podem ser construídos sobre UDP, demonstrando os trade-offs entre simplicidade de implementação e funcionalidade de rede.

---

**Desenvolvido para fins educacionais** - Demonstra a implementação de protocolos de rede customizados sobre UDP
