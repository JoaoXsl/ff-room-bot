# 🎮 Free Fire Room Bot - Profissional

Bot de Telegram de nível profissional para venda e gerenciamento de keys com saldo para criação de salas no Free Fire via API externa (NixBot).

## 🚀 Funcionalidades

- **Sistema de Usuários:** Cadastro automático, identificação por ID e armazenamento de saldo.
- **Sistema de Keys:** Geração de keys únicas pelo admin e resgate pelo usuário.
- **Sistema de Saldo:** Controle rigoroso de saldo e histórico de transações.
- **Integração API:** Criação de salas em tempo real com parâmetros customizáveis.
- **Painel Admin:** Gerenciamento completo de usuários, keys e saldos.
- **Interface Moderna:** Menu organizado em botões inline para melhor experiência do usuário.

## 🛠 Tecnologias

- **Linguagem:** Python 3.11+
- **Framework:** [aiogram 3.x](https://docs.aiogram.dev/) (Assíncrono)
- **Banco de Dados:** PostgreSQL com SQLAlchemy (Async)
- **Logs:** Loguru
- **Validação:** Pydantic Settings

## 📦 Instalação

1. Clone o repositório ou extraia os arquivos.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure o arquivo `.env` baseado no `.env.example`:
   - `BOT_TOKEN`: Token do @BotFather.
   - `ADMIN_IDS`: Seus IDs do Telegram.
   - `DATABASE_URL`: URL de conexão do PostgreSQL.
   - `NIX_API_TOKEN`: Seu token da API NixBot.

4. Inicie o bot:
   ```bash
   python main.py
   ```

## 📂 Estrutura do Projeto

```text
ff_room_bot/
├── config/             # Configurações globais
├── src/
│   ├── database/       # Modelos e conexão DB
│   ├── handlers/       # Lógica dos comandos e botões
│   ├── services/       # Integração API e lógica de negócio
│   ├── utils/          # Teclados e utilitários
│   └── middlewares/    # Proteção contra spam (Throttling)
├── logs/               # Arquivos de log
├── main.py             # Ponto de entrada
└── requirements.txt    # Dependências
```

## 🔐 Segurança

- Proteção contra spam (Throttling Middleware).
- Validação de saldo antes de cada criação de sala.
- Acesso restrito ao painel administrativo.
- Logs detalhados de todas as operações críticas.

## 💼 Licença

Este projeto foi desenvolvido para fins comerciais e de revenda. Sinta-se à vontade para expandir e customizar conforme sua necessidade.
