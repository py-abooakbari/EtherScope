# 🔍 EtherScope - Web3 Wallet Intelligence Telegram Bot

A production-grade Telegram bot that analyzes Ethereum wallet addresses and returns structured analytics including balance, token distribution, transaction history, and behavioral classification.

## 🎯 Features

- **Real-time Wallet Analysis**: Fetch current balance, token holdings, and transaction history
- **Behavioral Classification**: Detect wallet activity patterns (DeFi usage, NFT trading, contract deployment)
- **Intelligent Scoring**: Calculate comprehensive wallet scores (0-100) based on multiple factors
- **Smart Caching**: In-memory caching with TTL to optimize API usage
- **Structured Logging**: JSON-based structured logging for better observability
- **Error Handling**: Comprehensive error handling with API retry logic
- **Rate Limiting**: Built-in rate limiting for external API calls
- **Multiple Blockchain APIs**: Support for both Etherscan and Alchemy

## 🏗️ Architecture

This project follows clean architecture principles with strict separation of concerns:

```
web3-wallet-intelligence-bot/
├── bot/                          # Telegram bot layer
│   ├── main.py                   # Bot application factory
│   ├── handlers.py               # Command handlers (/start, /analyze, /health)
│   └── middlewares.py            # Request logging and error handling
├── services/                     # Business logic layer
│   ├── blockchain_service.py     # Ethereum API interactions
│   ├── analysis_service.py       # Wallet analysis algorithms
│   └── cache_service.py          # In-memory caching with TTL
├── models/                       # Data models (Pydantic)
│   ├── wallet.py                 # Wallet analysis data models
│   ├── transaction.py            # Transaction models
│   └── token.py                  # Token models
├── core/                         # Core utilities
│   ├── config.py                 # Configuration management
│   ├── logger.py                 # Structured logging setup
│   └── exceptions.py             # Custom exceptions
├── tests/                        # Unit tests
│   ├── test_blockchain_service.py
│   ├── test_analysis_service.py
│   └── test_cache_service.py
├── run.py                        # Application entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from BotFather)
- Blockchain API Key (Etherscan or Alchemy)

### Installation

1. **Clone or set up the project**:

```bash
cd EtherScope
```

2. **Create a virtual environment**:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Configure environment**:

```bash
cp .env.example .env
# Edit .env with your API keys and bot token
```

5. **Run the bot**:

```bash
python run.py
```

## 📋 Configuration

Create a `.env` file in the project root:

```env
# Required
TELEGRAM_BOT_TOKEN=your_token_here
BLOCKCHAIN_API_PROVIDER=etherscan
ETHERSCAN_API_KEY=your_key_here

# Optional
CACHE_ENABLED=true
LOG_LEVEL=INFO
ENVIRONMENT=production
DEBUG=false
```

### Available Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | - | **Required** Telegram bot token |
| `BLOCKCHAIN_API_PROVIDER` | `etherscan` | Blockchain API: `etherscan` or `alchemy` |
| `ETHERSCAN_API_KEY` | - | Required for Etherscan provider |
| `ALCHEMY_API_KEY` | - | Required for Alchemy provider |
| `CACHE_ENABLED` | `true` | Enable response caching |
| `CACHE_TTL_SECONDS` | `300` | Cache time-to-live in seconds |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `ENVIRONMENT` | `production` | Environment type |
| `DEBUG` | `false` | Enable debug mode |

## 🤖 Bot Commands

### `/start`
Display welcome message with available commands and usage examples.

### `/analyze <wallet_address>`
Analyze an Ethereum wallet address and return comprehensive report.

**Example:**
```
/analyze 0x1234567890123456789012345678901234567890
```

**Response includes:**
- ETH balance
- Token holdings (top 5)
- Transaction statistics
- Behavioral analysis
- Wallet score (0-100)
- Account age

### `/health`
Check bot operational status and cache statistics.

## 📊 Wallet Analysis Report

The analysis report includes:

### 💰 Financial Information
- ETH balance (in ETH)
- USD valuation (if available)
- Total tokens held
- Top token holdings with balances

### 📈 Transaction Statistics
- Total transaction count
- Unique addresses interacted with
- Contract interaction count
- Failed transaction count
- Last 3 transactions with details

### 🎯 Behavioral Classification

#### Activity Levels
- **Dormant**: No transactions
- **Low**: 5-19 transactions
- **Moderate**: 20-99 transactions
- **Active**: 100-999 transactions
- **Highly Active**: 1000+ transactions

#### Detection Features
- **DeFi User**: Detects smart contract interactions (20%+ of transactions)
- **NFT Trader**: Identifies NFT-related transfers
- **Contract Deployer**: Detects contract deployment transactions

### 🏆 Wallet Score (0-100)

Calculated based on:
- **Transaction Frequency** (40%): Activity level classification
- **Contract Interactions** (30%): Percentage of smart contract calls
- **Token Diversity** (15%): Number of unique addresses interacted with
- **Advanced Activities** (15%): DeFi usage, NFT trading, contract deployment

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ --cov=. --cov-report=html
```

### Test Files

- `test_blockchain_service.py`: Address validation and formatting
- `test_analysis_service.py`: Activity detection and scoring algorithms
- `test_cache_service.py`: Caching functionality

## 🔐 Security

- **API Keys**: Never exposed in logs or error messages
- **User Input**: All wallet addresses are validated before use
- **Rate Limiting**: Built-in protection against API quota exhaustion
- **Error Handling**: User-friendly error messages without sensitive information
- **Environment Variables**: All secrets loaded from .env file

## 🏃 Performance

- **Caching**: 5-minute cache TTL reduces redundant API calls
- **Async Architecture**: Fully async operations for non-blocking I/O
- **Rate Limiting**: 60 requests per minute to external APIs
- **Retry Logic**: Exponential backoff for failed requests

## 📝 Logging

Structured logging with JSON format includes:
- Timestamp (ISO 8601)
- Log level
- Logger name
- Message and context
- Line number and function name
- Exception details when applicable

Example log entry:
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "EtherScope.bot.handlers",
  "message": "Analysis requested by user 123456789",
  "module": "handlers",
  "function": "analyze",
  "line": 145,
  "user_id": 123456789
}
```

## 🐳 Docker Deployment

Build Docker image:

```bash
docker build -t etherscope .
```

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "run.py"]
```

Run container:

```bash
docker run -d \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e ETHERSCAN_API_KEY=your_key \
  --name etherscope \
  etherscope
```

## 🔄 API Rate Limiting

The bot implements rate limiting to respect external API quotas:

- **Etherscan**: 60 requests per minute (free tier)
- **Retry Logic**: Exponential backoff (1s, 2s, 4s, etc.)
- **Rate Limit Handling**: Automatic cooldown on 429 responses

## 📚 Project Standards

This project follows production-grade engineering standards:

- ✅ **Type Hints**: Full type annotations throughout
- ✅ **Docstrings**: Comprehensive docstrings for all public APIs
- ✅ **Error Handling**: Custom exceptions with context
- ✅ **PEP 8**: Code formatted with Black, linted with Flake8
- ✅ **Async First**: Full async/await architecture
- ✅ **Clean Architecture**: Strict separation of concerns
- ✅ **Dependency Injection**: Services are configurable
- ✅ **Unit Tested**: Comprehensive test coverage
- ✅ **Secure**: No hardcoded secrets or sensitive data

## 🛠️ Development

### Code Quality

Format code with Black:
```bash
black .
```

Check types with Mypy:
```bash
mypy . --ignore-missing-imports
```

Lint with Flake8:
```bash
flake8 . --max-line-length=100
```

### Project Structure

**Key Design Decisions:**

1. **Async-First**: All I/O operations use async/await
2. **Service Layer**: Business logic isolated from handlers
3. **Pydantic Models**: Strong typing and validation
4. **In-Memory Cache**: Fast response times for repeated queries
5. **Middleware Pattern**: Cross-cutting concerns (logging, error handling)

## 🤝 Contributing

1. Ensure code follows PEP 8 standards
2. Add type hints to all functions
3. Write tests for new features
4. Update documentation
5. Format code with Black

## 📞 Troubleshooting

### Bot not responding
- Check that bot token is correct
- Verify network connectivity
- Check logs with `LOG_LEVEL=DEBUG`

### API rate limit errors
- Wait before retrying (bot auto-retries)
- Consider upgrading to Alchemy for higher limits
- Check API key is valid

### Invalid wallet address
- Ensure address is 42 characters (0x + 40 hex chars)
- Address must be valid Ethereum address
- Avoid spaces and special characters

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- Built with python-telegram-bot
- Data from Etherscan and Alchemy APIs
- Pydantic for data validation

---

**Created by a Senior Backend Engineer**

*Production-grade code for Web3 intelligence*
