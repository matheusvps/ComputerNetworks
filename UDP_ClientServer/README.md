# Sistema UDP de Transferência de Arquivos Confiável

Este projeto implementa uma aplicação cliente-servidor para transferência de arquivos utilizando o protocolo UDP, demonstrando como implementar mecanismos de confiabilidade diretamente sobre UDP, simulando funcionalidades que o TCP oferece nativamente.

## 🎯 Objetivos do Projeto

- Desenvolver uma aplicação cliente-servidor para transferência de arquivos usando UDP
- Implementar mecanismos básicos de controle e confiabilidade sobre UDP
- Demonstrar segmentação, verificação de integridade e retransmissão
- Contrastar com os serviços que o TCP disponibiliza para a camada de aplicação

## 🏗️ Arquitetura do Sistema

### Componentes Principais

1. **Servidor UDP** (`server.py`) - Recebe requisições e envia arquivos segmentados
2. **Cliente UDP** (`client.py`) - Solicita arquivos e os reconstrói
3. **Exemplo Hello World** (`hello_world_udp.py`) - Demonstração básica de sockets UDP
4. **Gerador de Arquivos de Teste** (`create_test_file.py`) - Cria arquivos para demonstração
5. **Script de Demonstração** (`demo.py`) - Executa demonstrações completas

### Protocolo de Aplicação

O sistema implementa um protocolo customizado sobre UDP com os seguintes elementos:

#### Mensagens de Controle
- `GET filename` - Solicita um arquivo
- `FILE_INFO filename size segments` - Informações do arquivo
- `RETRANSMIT filename segment_number` - Solicita retransmissão
- `END_TRANSMISSION filename` - Sinal de fim de transmissão
- `ERROR message` - Mensagem de erro

#### Estrutura dos Segmentos
```
[segment_number(4)][checksum(16)][filename_length(2)][data_length(2)][filename][data]
```

- **segment_number**: Número sequencial do segmento (4 bytes)
- **checksum**: MD5 dos dados (16 bytes)
- **filename_length**: Tamanho do nome do arquivo (2 bytes)
- **data_length**: Tamanho dos dados (2 bytes)
- **filename**: Nome do arquivo
- **data**: Dados do segmento

## 🚀 Como Usar

### Pré-requisitos

- Python 3.6+
- Bibliotecas padrão do Python (não requer instalação adicional)

### Execução Rápida

1. **Demonstração Completa** (recomendado para iniciantes):
   ```bash
   python3 demo.py
   ```

2. **Exemplo Hello World UDP**:
   ```bash
   # Terminal 1 - Servidor
   python3 hello_world_udp.py server
   
   # Terminal 2 - Cliente
   python3 hello_world_udp.py client
   ```

3. **Transferência de Arquivos**:
   ```bash
   # Terminal 1 - Servidor
   python3 server.py --port 8888
   
   # Terminal 2 - Cliente
   python3 client.py 127.0.0.1 8888 nome_do_arquivo.txt
   ```

### Uso Avançado

#### Servidor
```bash
python3 server.py [opções]

Opções:
  --host HOST        Host para escutar (padrão: 0.0.0.0)
  --port PORT        Porta para escutar (padrão: 8888)
  --buffer-size SIZE Tamanho do buffer (padrão: 1024)
```

#### Cliente
```bash
python3 client.py SERVER_HOST SERVER_PORT FILENAME [opções]

Opções:
  --output-dir DIR       Diretório de saída (padrão: .)
  --timeout SECONDS      Timeout em segundos (padrão: 5.0)
  --simulate-loss        Habilita simulação de perda
  --loss-probability P   Probabilidade de perda (padrão: 0.1)
```

#### Criação de Arquivos de Teste
```bash
python3 create_test_file.py [opções]

Opções:
  --filename NAME    Nome do arquivo (padrão: test_file.txt)
  --size SIZE        Tamanho em MB (padrão: 2)
```

## 🔧 Funcionalidades Implementadas

### ✅ Requisitos Obrigatórios

- [x] **Servidor UDP** com porta > 1024
- [x] **Protocolo de aplicação** customizado sobre UDP
- [x] **Segmentação** de arquivos em múltiplos datagramas
- [x] **Cabeçalho customizado** com informações de controle
- [x] **Verificação de integridade** usando MD5
- [x] **Detecção de perda** e segmentos faltantes
- [x] **Retransmissão** de segmentos específicos
- [x] **Simulação de perda** para testes
- [x] **Reconstrução** de arquivos a partir de segmentos

### 🎯 Características Técnicas

- **Tamanho do payload**: 1024 bytes por segmento
- **Tamanho do cabeçalho**: 20 bytes
- **Algoritmo de checksum**: MD5
- **Timeout configurável**: Padrão 5 segundos
- **Processamento multithread**: Servidor atende múltiplos clientes
- **Cache de segmentos**: Evita leitura repetida do disco

## 📊 Considerações de Design do Protocolo

### Segmentação e Tamanho do Buffer

- **Tamanho fixo**: 1024 bytes por segmento para simplicidade
- **Relacionamento com MTU**: Considera o MTU típico de Ethernet (1500 bytes)
- **Overhead**: 20 bytes de cabeçalho + nome do arquivo
- **Eficiência**: Balanceia entre overhead e número de segmentos

### Detecção de Erros

- **Checksum MD5**: 16 bytes para verificação de integridade
- **Verificação por segmento**: Cada segmento é verificado individualmente
- **Detecção de corrupção**: Segmentos com checksum inválido são rejeitados

### Ordenação e Detecção de Perda

- **Números de sequência**: 4 bytes para identificação única
- **Detecção de perda**: Comparação entre segmentos esperados e recebidos
- **Timeout**: Detecção de segmentos atrasados ou perdidos

### Controle de Fluxo

- **Pausa entre segmentos**: 10ms para evitar sobrecarga
- **Processamento assíncrono**: Cliente processa segmentos em thread separada
- **Buffer de recepção**: Armazena segmentos até reconstrução completa

## 🧪 Testes e Demonstrações

### Cenários de Teste

1. **Transferência Normal**: Arquivo pequeno sem perdas
2. **Transferência Grande**: Arquivo > 1MB para testar segmentação
3. **Simulação de Perda**: 10-20% de perda para testar retransmissão
4. **Múltiplos Clientes**: Teste de concorrência do servidor

### Métricas de Performance

- **Taxa de transferência**: Dependente da rede e tamanho do arquivo
- **Overhead de protocolo**: ~2% para arquivos grandes
- **Tempo de recuperação**: Dependente do número de segmentos perdidos

## 🔍 Análise Comparativa: UDP vs TCP

### Vantagens do UDP neste Projeto

- **Controle total**: Implementação customizada de confiabilidade
- **Flexibilidade**: Protocolo adaptado às necessidades específicas
- **Educacional**: Demonstra conceitos de redes e protocolos

### Desvantagens vs TCP

- **Complexidade**: Muito mais código para implementar confiabilidade
- **Performance**: Overhead adicional de cabeçalhos e retransmissões
- **Manutenção**: Mais difícil de debugar e manter

### Quando Usar

- **Educação**: Aprendizado sobre protocolos de rede
- **Casos específicos**: Quando TCP não é adequado
- **Controle fino**: Necessidade de controle total sobre a transferência

## 🚨 Limitações e Melhorias Futuras

### Limitações Atuais

- **Sem controle de congestionamento**: Pode sobrecarregar a rede
- **Timeout fixo**: Não se adapta às condições da rede
- **Sem compressão**: Dados são enviados em texto puro
- **Sem criptografia**: Dados são transmitidos em texto plano

### Melhorias Sugeridas

- **Controle de congestionamento**: Implementar algoritmo similar ao TCP
- **Timeout adaptativo**: Ajustar baseado no RTT da rede
- **Compressão**: Reduzir tamanho dos dados transmitidos
- **Criptografia**: Adicionar segurança à transmissão
- **Interface gráfica**: GUI para facilitar o uso

## 📚 Referências e Recursos

### Conceitos de Redes

- **UDP (User Datagram Protocol)**: RFC 768
- **MTU (Maximum Transmission Unit)**: Conceito fundamental de redes
- **Checksum**: Algoritmos de verificação de integridade
- **Retransmissão**: Estratégias para recuperação de dados perdidos

### Documentação Python

- **Socket Programming**: [docs.python.org](https://docs.python.org/3/library/socket.html)
- **Struct Module**: [docs.python.org](https://docs.python.org/3/library/struct.html)
- **Hashlib**: [docs.python.org](https://docs.python.org/3/library/hashlib.html)

## 🤝 Contribuições

Este projeto foi desenvolvido como trabalho educacional para demonstrar conceitos de redes de computadores. Contribuições são bem-vindas para melhorar a implementação e adicionar novas funcionalidades.

## 📄 Licença

Este projeto é de código aberto e está disponível para uso educacional e de pesquisa.

---

**Desenvolvido para fins educacionais** - Demonstra a implementação de protocolos de rede customizados sobre UDP
