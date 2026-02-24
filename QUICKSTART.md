"""QUICKSTART.md - Get up and running in 5 minutes"""

# 🚀 EtherScope - Quick Start Guide

## Prerequisites
- Python 3.11+
- Telegram Bot Token (from @BotFather)
- Etherscan API Key (free from etherscan.io/apis)

## 1️⃣ Setup (2 minutes)

```bash
# Clone/navigate to project
cd EtherScope

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2️⃣ Configure (1 minute)

```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
# TELEGRAM_BOT_TOKEN=your_bot_token
# ETHERSCAN_API_KEY=your_etherscan_key
```

## 3️⃣ Run (instantly)

```bash
python run.py
```

## 4️⃣ Test in Telegram

Send commands to your bot:
```
/start                                    # See welcome message
/analyze 0xd8da6bf26964af9d7eed9e03e53415d37aa96045  # Analyze wallet
/health                                   # Check bot status
```

## 🐳 Or use Docker

```bash
# Build
docker build -t etherscope .

# Run (with env file)
docker run --env-file .env etherscope
```

## 📊 What You Get

When you analyze a wallet, you receive:

```
💼 Wallet Analysis Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Address: 0x1234...
💰 ETH Balance: 25.5 ETH
Value: $45,000

🪙 Token Holdings
Total Tokens: 8
Top Tokens:
  • USDC: 10,000
  • DAI: 5,000
  • WETH: 2.5

📊 Transaction History
Total: 450 transactions
Unique Addresses: 127
Contract Interactions: 89
Failed: 3

🎯 Behavioral Analysis
Activity Level: ACTIVE
DeFi User: Yes
NFT Trader: No
Wallet Score: 78/100

📅 Account History
Active Days: 730
First Tx: 2022-01-15
```

## 🔧 Configuration Options

Edit `.env` to customize:

```env
# Blockchain provider
BLOCKCHAIN_API_PROVIDER=etherscan      # or 'alchemy'

# Caching (speed up repeated queries)
CACHE_ENABLED=true                     # 5-minute cache by default
CACHE_TTL_SECONDS=300

# Logging
LOG_LEVEL=INFO                         # INFO, DEBUG, WARNING, ERROR

# Environment
ENVIRONMENT=production                 # production or development
```

## 📚 Learn More

- Read [README.md](./README.md) for complete documentation
- See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment
- Check [IMPLEMENTATION.md](./IMPLEMENTATION.md) for technical details
- Run tests: `pytest tests/ -v`

## 🐛 Troubleshooting

### Bot not responding?
```bash
# Check logs
python run.py  # Look for error messages

# Verify token
echo $TELEGRAM_BOT_TOKEN
```

### Invalid address error?
- Ensure address is 42 characters (0x + 40 hex)
- Example valid: `0x1234567890123456789012345678901234567890`

### API rate limit?
- Upgrade from free Etherscan to paid tier
- Or switch to Alchemy provider
- Bot auto-retries with backoff

## 💡 Next Steps

1. Customize the bot response formatting in `bot/handlers.py`
2. Add database persistence using SQLAlchemy
3. Deploy to your favorite cloud platform
4. Set up monitoring and alerts
5. Add more blockchain analysis features

---

**Questions?** See the full [README.md](./README.md)
