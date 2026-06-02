# 🤖 AI Assistant Unlimited with Real-Time Web Search

A **completely free, unlimited-use AI coding expert assistant** with **real-time web search and automatic version checking**. No API keys, no payments, no rate limits—always up-to-date with the latest information.

## ✨ NEW: Real-Time Information Features

✅ **🌐 Live Web Search** - Get current news, tutorials, and documentation  
✅ **📦 Automatic Version Checking** - Notified of new releases instantly  
✅ **🔄 Always Updated** - Never outdated information  
✅ **🎯 Smart Context** - Searches automatically when you ask about "latest", "new", "update", etc.  

### Example: It Works Like This

**You:** "What's the latest version of Vercel?"  
**AI:** Shows latest Vercel release with download link + then answers your question with current info

**You:** "How do I use React with TypeScript?"  
**AI:** Searches for latest React + TypeScript tutorials + provides current best practices

---

## 🎯 Core Features

✅ **100% Free Forever** - No API costs, no subscriptions, unlimited usage  
✅ **Offline & Private** - All processing happens locally on your machine  
✅ **Multiple AI Models** - Switch between different models instantly  
✅ **Code Expert** - Specialized for programming and technical questions  
✅ **Beautiful Web Interface** - Modern, responsive chat UI  
✅ **REST API** - Integrate with your other applications  
✅ **Conversation Memory** - Maintains context across messages  
✅ **GPU Support** - Automatic acceleration with NVIDIA/AMD GPUs  
✅ **Real-Time Web Search** - Access to current information  
✅ **Version Tracking** - Know about new releases instantly  

---

## 📋 Prerequisites

- **Python 3.8 or higher**
- **Ollama** (free AI model runner)
- **4GB+ RAM** (8GB recommended)
- **Disk space** for models (varies by model, typically 2-13GB)
- **Internet connection** (optional: for web search features)

---

## 🚀 Installation & Setup

### Step 1: Install Ollama

Download and install Ollama from [ollama.ai](https://ollama.ai)

**macOS:**
```bash
brew install ollama
```

**Windows/Linux:**
- Download installer from [ollama.ai](https://ollama.ai)
- Run the installer

### Step 2: Download an AI Model

Open a terminal and pull a model:

```bash
# Fast, lightweight (recommended for first time)
ollama pull mistral

# Or choose another model:
ollama pull llama2
ollama pull neural-chat
ollama pull codellama        # Best for coding
```

**Model Sizes:**
| Model | Size | Speed | RAM | Best For |
|-------|------|-------|-----|----------|
| mistral | 4.1B | ⚡⚡⚡ Fast | 4GB | General, fast |
| neural-chat | 7B | ⚡⚡ Medium | 6GB | Conversations |
| llama2 | 7B | ⚡⚡ Medium | 6GB | Versatile |
| codellama | 7B | ⚡⚡ Medium | 6GB | **Code** |
| dolphin-mixtral | 12B | ⚡ Slower | 8GB | Complex tasks |

### Step 3: Start Ollama Server

```bash
ollama serve
```

You should see:
```
Listening on 127.0.0.1:11434
```

**Keep this terminal open!** Ollama needs to run in the background.

### Step 4: Clone & Setup the Project

```bash
git clone https://github.com/julianomangli/ai-assistant-unlimited.git
cd ai-assistant-unlimited
```

### Step 5: Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv

# Activate it:
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 6 (Optional): Setup Brave Search API

For faster, higher-quality web search results:

1. Get free API key: [api.search.brave.com](https://api.search.brave.com)
2. Create `.env` file:
   ```
   BRAVE_API_KEY=your_api_key_here
   ```

### Step 7: Run the Application

```bash
python app.py
```

You should see:
```
🤖 AI Assistant running at http://localhost:5000
Model: mistral
Web Search: Enabled ✅
Version Checking: Enabled ✅
```

### Step 8: Open in Browser

Visit **http://localhost:5000** in your web browser and start chatting! 🎉

---

## 💬 How to Use with Real-Time Features

### Web Search - Automatically Triggered

The AI automatically searches the web when you ask about:
- **Latest/Newest**: "What's the latest version of X?"
- **Current Updates**: "What's new in React?"
- **How-To Guides**: "How do I use Vercel with Next.js?"
- **Documentation**: "Where can I find FastAPI documentation?"
- **Errors/Issues**: "How do I fix this error?"

### Examples

**Question 1:**
```
You: "What's the latest Vercel release?"

AI Response:
📰 **Latest Search Results:**
(Updated: 2026-06-02 12:34 UTC)

1. **Vercel v28.5.0 Released**
   📌 Source: GitHub
   🔗 URL: https://github.com/vercel/vercel/releases/tag/v28.5.0
   📝 New features: Edge Functions improvements, better analytics...

🆕 **New Version Available:**
📦 Package: vercel
📌 Latest Version: 28.5.0
📅 Released: 2026-06-02
📥 Download: [link]

Here are the latest improvements in Vercel:
- Enhanced Edge Functions with faster execution
- Improved analytics dashboard
- [Your AI continues with detailed explanation]
```

**Question 2:**
```
You: "How to use TypeScript with React in 2026?"

AI Response:
📰 **Latest Search Results:**
(Updated: 2026-06-02 12:35 UTC)

[Shows 3 latest tutorials and best practices]

🆕 **New Version Available:**
📦 Package: typescript
📌 Latest Version: 5.1.6
...

[AI then provides current best practices with code examples]
```

---

## 🐍 Using as a Python Library

### Basic Usage with Web Search

```python
from assistant import AIAssistant

# Initialize (web search enabled by default)
assistant = AIAssistant(model="mistral", enable_web_search=True)

# Ask a question - automatically searches the web
response = assistant.chat("What's the latest version of Flask?")
print(response)
```

### Disable Web Search for Specific Queries

```python
assistant = AIAssistant()

# With web search
response1 = assistant.chat("Latest Python news")  # Searches

# Without web search (offline mode)
response2 = assistant.chat("Explain Python decorators")  # No search
```

### Stream with Real-Time Context

```python
assistant = AIAssistant()

print("AI: ", end="", flush=True)
for chunk in assistant.chat_stream("Show me latest Node.js updates"):
    print(chunk, end="", flush=True)
print()
```

---

## 🌐 Using the REST API with Web Search

### Send a Message (Auto Web Search)

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the latest JavaScript frameworks?",
    "model": "mistral",
    "enable_web_search": true
  }'
```

### Disable Web Search for a Query

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain async/await",
    "model": "mistral",
    "enable_web_search": false
  }'
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Enable/disable web search
ENABLE_WEB_SEARCH = True

# Enable/disable version checking
ENABLE_VERSION_CHECK = True

# Brave Search API key (optional)
BRAVE_API_KEY = "your_api_key"

# Default model
DEFAULT_MODEL = "mistral"

# Response length
MAX_TOKENS = 2048

# Creativity
TEMPERATURE = 0.7
```

Or use environment variables:

```bash
export ENABLE_WEB_SEARCH="True"
export ENABLE_VERSION_CHECK="True"
export BRAVE_API_KEY="your_api_key"
python app.py
```

---

## 🔍 What Triggers Web Search

The assistant automatically searches for:

- **"latest"** - Latest versions, news, updates
- **"newest"** - New releases
- **"current"** - Current state of things
- **"today"** - Today's news/events
- **"recently"** - Recent developments
- **"what's new"** - New features
- **"update"** - Version updates
- **"release"** - New releases
- **"how to"** - Tutorials and guides
- **"documentation"** - Official docs
- **"error"** - Error solutions
- **"issue"** - Problem troubleshooting

---

## 📦 Version Checking

Automatically detects and reports new versions for:

**Python Packages** (PyPI)
```
pip install flask
django
requests
```

**Node.js Packages** (NPM)
```
npm install react
vue
typescript
```

**GitHub Projects**
```
ollama/ollama
vercel/vercel
facebook/react
```

---

## 🎯 Real-World Examples

### Example 1: Web Development
```
You: "How do I deploy a Next.js app with Vercel in 2026?"

AI:
1. Searches for latest Vercel deployment docs
2. Checks for new Next.js version
3. Provides current best practices
4. Includes latest tutorial links
```

### Example 2: Data Science
```
You: "What's new in TensorFlow?"

AI:
1. Finds latest TensorFlow release
2. Searches for new features
3. Shows recent tutorials
4. Provides migration guides if needed
```

### Example 3: DevOps
```
You: "Latest Docker best practices"

AI:
1. Searches current Docker documentation
2. Checks for new Docker version
3. Shows recent security updates
4. Provides current examples
```

---

## 🐛 Troubleshooting

### Web Search Not Working
```
✓ Check internet connection
✓ Try disabling: ENABLE_WEB_SEARCH="False"
✓ Verify DuckDuckGo is not blocked
✓ Consider using Brave Search (get free API key)
```

### Version Checking Errors
```
✓ Package might not exist
✓ PyPI/NPM/GitHub might be temporarily down
✓ Disable with: ENABLE_VERSION_CHECK="False"
✓ Check your internet connection
```

### Slow Responses
```
✓ Web search adds 1-3 seconds
✓ Try disabling web search for speed
✓ Use faster model (mistral)
✓ Enable GPU acceleration
```

---

## 🚀 Advanced Features

### Custom Search Filters

```python
from assistant import AIAssistant

assistant = AIAssistant()
# Searches automatically for current data
response = assistant.chat("Recent advances in AI")
```

### Combine Web Search with Custom Prompts

```python
assistant = AIAssistant(
    system_prompt="You are a tech news expert. Always cite sources.",
    enable_web_search=True
)

response = assistant.chat("Tech news this week")
```

---

## 📊 Performance

| Feature | Speed Impact | Worth It? |
|---------|--------------|-----------|
| Web Search | +1-3 seconds | ✅ Yes for current info |
| Version Checking | +0.5-1 second | ✅ Yes for updates |
| Offline Mode | Instant | ✅ Yes for speed |

---

## 🔐 Privacy & Security

✅ Local AI models - no data sent to external APIs  
✅ Web search results cached locally  
✅ Conversations stored only on your machine  
✅ No tracking or telemetry  
✅ Open source - inspect the code  

---

## 📝 License

MIT License - Feel free to use, modify, and distribute

---

## ⚠️ Disclaimer

- Web search results are from third-party sources
- Always verify important information
- AI responses may contain errors
- Always review code before production use
- Respect robots.txt when web searching

---

## 🙋 FAQ

**Q: Will web search work offline?**  
A: No, web search requires internet. But the AI model works completely offline.

**Q: Does web search cost money?**  
A: No! DuckDuckGo is free. Brave Search is optional with free tier.

**Q: How often do results update?**  
A: Results are fetched in real-time on each query.

**Q: Can I disable web search?**  
A: Yes! Set `ENABLE_WEB_SEARCH=False` in config.

**Q: Does this send my data anywhere?**  
A: Web searches are sent to search engines (DuckDuckGo/Brave), but all AI processing is local.

---

**🚀 Your AI is now always up-to-date!**

Never miss an update again. Your AI assistant now brings you the latest information while maintaining complete privacy and offline capabilities.
