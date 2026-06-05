# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-06-05

### 🎉 Initial Release

#### Added
- ✨ **Chat Mode** - Ask coding questions and get real-time responses
- 🔨 **Build Mode** - Describe an app in English and watch it build live
- 👁️ **Live Preview** - Real-time rendering of generated applications
- 📝 **Code Editor** - Full-featured editor with syntax highlighting
- 📂 **File Explorer** - Browse and manage generated project files
- 📦 **ZIP Export** - Download complete projects in one click
- 🌐 **Web Search** - Real-time DuckDuckGo/Brave search integration
- 📡 **Terminal Access** - Built-in terminal with WebSocket support
- 🔒 **100% Private** - All processing runs locally on your machine
- 💾 **Session Management** - Multiple independent chat sessions
- 🎨 **Dark/Light Themes** - Customizable UI with accent colors
- ⚙️ **Model Switching** - Switch between installed Ollama models
- 📱 **Responsive Design** - Works on desktop and tablets

#### Backend
- Flask REST API with comprehensive endpoints
- Ollama integration for local LLM inference
- WebSocket support for real-time terminal
- Secure file operations and path sanitization
- Environment-based configuration
- Production-ready error handling

#### Frontend
- Vanilla JavaScript (no build dependencies)
- Monaco Editor integration
- xterm.js for terminal emulation
- Real-time message updates
- Persistent chat history in localStorage
- Settings persistence across sessions

#### Deployment
- Support for local development
- Production startup script with Gunicorn
- Replit configuration included
- Docker-ready structure
- GitHub Actions CI workflow
- Environment configuration templates

#### Documentation
- Comprehensive README
- Installation and deployment guide
- Configuration documentation
- MIT License

---

## Future Roadmap

### v1.1.0 (Planned)
- [ ] Streaming responses for faster feedback
- [ ] Advanced file editing with multi-tab support
- [ ] Code formatting and linting integration
- [ ] Conversation export (JSON, Markdown)
- [ ] Version control integration

### v1.2.0 (Planned)
- [ ] Custom system prompts
- [ ] Conversation templates
- [ ] Local model management UI
- [ ] Advanced search filters
- [ ] Keyboard shortcuts panel

### v2.0.0 (Future)
- [ ] Collaborative editing
- [ ] Cloud sync (optional)
- [ ] Plugin system
- [ ] Advanced analytics
- [ ] Mobile app

---

## Notes

- Built with ❤️ by MangliJuliano
- Open source and free to use
- No telemetry or external tracking
- 100% runs on your machine
