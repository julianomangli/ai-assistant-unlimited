# 🤖 AI Assistant Unlimited

A **completely free, unlimited-use AI coding expert assistant** powered by local open-source models. No API keys, no payments, no rate limits—just pure AI power running on your machine.

## ✨ Features

✅ **100% Free Forever** - No API costs, no subscriptions, unlimited usage  
✅ **Offline & Private** - All processing happens locally on your machine  
✅ **Multiple AI Models** - Switch between different models instantly  
✅ **Code Expert** - Specialized for programming and technical questions  
✅ **Beautiful Web Interface** - Modern, responsive chat UI  
✅ **REST API** - Integrate with your other applications  
✅ **Conversation Memory** - Maintains context across messages  
✅ **GPU Support** - Automatic acceleration with NVIDIA/AMD GPUs  

---

## 📋 Prerequisites

- **Python 3.8 or higher**
- **Ollama** (free AI model runner)
- **4GB+ RAM** (8GB recommended)
- **Disk space** for models (varies by model, typically 2-13GB)

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

### Step 6: Run the Application

```bash
python app.py
```

You should see:
```
🤖 AI Assistant running at http://localhost:5000
Model: mistral
```

### Step 7: Open in Browser

Visit **http://localhost:5000** in your web browser and start chatting! 🎉

---

## 💬 How to Use the Web Interface

### Basic Chat

1. Type your question or request in the text box at the bottom
2. Press **Enter** or click **Send**
3. Wait for the AI to respond
4. Ask follow-up questions—context is maintained!

### Change Models

1. Click the **Model** dropdown at the top of the chat box
2. Select a different model:
   - **Mistral (Fast)** - For quick answers
   - **Neural Chat** - For conversations
   - **Llama 2** - Balanced all-around
   - **Code Llama** - For programming

### Clear Chat History

Click the **Clear** button to start a fresh conversation.

---

## 🐍 Using as a Python Library

### Basic Usage

```python
from assistant import AIAssistant

# Initialize
assistant = AIAssistant(model="mistral")

# Ask a question
response = assistant.chat("Write a Python function to calculate factorial")
print(response)
```

### Streaming Responses

```python
assistant = AIAssistant(model="mistral")

# Stream the response word-by-word
print("AI: ", end="", flush=True)
for chunk in assistant.chat_stream("Explain machine learning in simple terms"):
    print(chunk, end="", flush=True)
print()
```

### Maintain Conversation Context

```python
assistant = AIAssistant(model="llama2")

# First message
response1 = assistant.chat("What is Python?")
print("Q1:", response1)

# Follow-up maintains context
response2 = assistant.chat("What are its main use cases?")
print("Q2:", response2)

# Access conversation history
history = assistant.get_history()
print(history)
```

### Custom System Prompts

```python
# Make it a coding expert
coding_expert = AIAssistant(
    model="codellama",
    system_prompt="You are a senior software engineer with 15 years of experience. "
                  "Provide detailed, production-ready code with explanations."
)

code = coding_expert.chat("Design a REST API using FastAPI")
print(code)
```

### Switch Models Dynamically

```python
assistant = AIAssistant()

# Switch between models
response1 = assistant.chat("Fast answer please", model="mistral")
response2 = assistant.chat("Detailed analysis", model="llama2")
```

---

## 🌐 Using the REST API

The app exposes HTTP endpoints for integration with other applications.

### Send a Message

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a hello world in Python",
    "model": "mistral"
  }'
```

**Response:**
```json
{
  "response": "Here's a simple Python hello world program:\n\nprint(\"Hello, World!\")\n\nThis is the simplest..."
}
```

### Get Available Models

```bash
curl http://localhost:5000/api/models
```

**Response:**
```json
{
  "models": ["mistral", "llama2", "neural-chat", "codellama"]
}
```

### Clear History

```bash
curl -X POST http://localhost:5000/api/clear-history
```

---

## ⚙️ Configuration

Edit `config.py` to customize behavior:

```python
# Ollama server address
OLLAMA_HOST = "http://localhost:11434"

# Default model
DEFAULT_MODEL = "mistral"

# Response length limit
MAX_TOKENS = 2048

# Creativity (0-1, higher = more creative/random)
TEMPERATURE = 0.7

# Diversity (0-1, higher = more diverse)
TOP_P = 0.9

# Web server port
FLASK_PORT = 5000
```

Or use environment variables:

```bash
export OLLAMA_HOST="http://localhost:11434"
export DEFAULT_MODEL="codellama"
export TEMPERATURE="0.5"
python app.py
```

---

## 🎯 Example Use Cases

### 1. Code Generation
```
"Write a Python function that validates email addresses using regex"
"Create a SQL query to find the top 10 customers by revenue"
"Write a React component for a user login form"
```

### 2. Learning & Explanation
```
"Explain how neural networks work in simple terms"
"What's the difference between async/await and promises in JavaScript?"
"How does garbage collection work in Python?"
```

### 3. Debugging & Help
```
"Why does this code throw a TypeError? [paste code]"
"How can I optimize this database query?"
"What's the best way to handle errors in this function?"
```

### 4. Writing & Documentation
```
"Write a README for a Python web scraper project"
"Create API documentation for a REST endpoint"
"Write unit tests for this function: [paste code]"
```

---

## 🐛 Troubleshooting

### Error: "Could not connect to Ollama at http://localhost:11434"

**Solution:** Make sure Ollama is running
```bash
# Terminal 1 - Start Ollama
ollama serve

# Terminal 2 - Run the app
python app.py
```

### Error: "Out of memory" or slow responses

**Solution:** Use a smaller model
```bash
# Try the lightest model
ollama pull mistral

# Or in Python
assistant = AIAssistant(model="mistral")
```

### Model not found error

**Solution:** Pull the model first
```bash
ollama pull llama2
```

### Web interface won't load at localhost:5000

**Solutions:**
- Check if port 5000 is already in use
- Change port in `config.py`: `FLASK_PORT = 8080`
- Ensure Flask is installed: `pip install -r requirements.txt`
- Try http://127.0.0.1:5000 instead

### Responses are very slow

**Solutions:**
- Close other applications to free up RAM
- Use a smaller, faster model (mistral)
- Enable GPU support (see below)
- Reduce `MAX_TOKENS` in config.py

---

## 🎮 GPU Acceleration (Optional)

Speed up responses dramatically with GPU support!

### NVIDIA GPUs (CUDA)

1. Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
2. Install [cuDNN](https://developer.nvidia.com/cudnn)
3. Ollama will automatically detect and use your GPU

### AMD GPUs (ROCm)

```bash
HIP_VISIBLE_DEVICES=0 ollama serve
```

### Check GPU Usage

```bash
# Monitor while chatting
nvidia-smi watch -n 1  # NVIDIA
```

---

## 📦 Project Structure

```
ai-assistant-unlimited/
├── app.py                    # Flask web server
├── assistant.py              # Core AI Assistant class
├── models.py                 # Ollama API integration
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore
├── templates/
│   └── index.html            # Web interface HTML
└── static/
    ├── style.css             # Styling
    └── script.js             # Frontend JavaScript
```

---

## 🔧 Advanced Features

### Custom Prompts for Different Roles

```python
# Python expert
python_expert = AIAssistant(
    system_prompt="You are a Python expert. Always provide Pythonic, clean code."
)

# JavaScript specialist
js_expert = AIAssistant(
    system_prompt="You are a JavaScript/Node.js expert with expertise in modern frameworks."
)

# Writer
writer = AIAssistant(
    system_prompt="You are a professional technical writer. Write clearly and concisely."
)
```

### Batch Processing

```python
assistant = AIAssistant()

questions = [
    "What is machine learning?",
    "Explain supervised learning",
    "What are neural networks?"
]

for q in questions:
    print(f"Q: {q}")
    print(f"A: {assistant.chat(q)}\n")
```

---

## 🤝 Contributing

Contributions welcome! Some ideas:
- Add support for more models
- Improve the web UI
- Add file upload support
- Create Docker container
- Add database for chat history

---

## 📝 License

MIT License - Feel free to use, modify, and distribute

---

## ⚠️ Disclaimer

- Model responses are AI-generated and may contain errors
- Always review code before using in production
- Models may hallucinate or provide inaccurate information
- Opinions expressed by the AI are not endorsed

---

## 🙋 FAQ

**Q: Is this really free?**  
A: Yes! Completely free. No API keys, no payments, no limits.

**Q: Does it work offline?**  
A: Yes! Everything runs locally. You don't even need internet.

**Q: Can I use this commercially?**  
A: Yes! MIT license allows commercial use.

**Q: How do I get better results?**  
A: Use more specific prompts, provide context, and try different models.

**Q: Can I use this on a server?**  
A: Yes! Change the host in `config.py` from `127.0.0.1` to `0.0.0.0`

**Q: Is my data private?**  
A: Completely private! All data stays on your machine.

---

## 📚 Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Model Library](https://ollama.ai/library)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Prompt Engineering Tips](https://platform.openai.com/docs/guides/prompt-engineering)

---

**Happy coding! 🚀**

Need help? Check the troubleshooting section or open an issue on GitHub.
