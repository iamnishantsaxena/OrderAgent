# 📚 Project Navigation Guide

## 🎯 Start Here Based on Your Goal

### 🚀 I want to get started quickly
→ Read **[QUICKSTART.md](QUICKSTART.md)** (5 minutes)
→ Then run: `streamlit run app.py`

### 📖 I want to understand the project
→ Read **[README.md](README.md)** (complete overview)
→ Then **[ARCHITECTURE.md](ARCHITECTURE.md)** (system design)

### 💻 I want to use it programmatically
→ Read **[API.md](API.md)** (complete API reference)
→ Check **[examples/usage_examples.py](examples/usage_examples.py)** (7 examples)

### 🔧 I want to customize it
→ Read **[ARCHITECTURE.md](ARCHITECTURE.md)** (extension points)
→ Edit files in `src/` directory

### 🧪 I want to test it
→ Run: `python tests/test_agent.py`
→ Check `tests/sample_inputs/` for sample data

### 📊 I want to see the workflow
→ Read **[WORKFLOW.md](WORKFLOW.md)** (visual diagrams)

## 📁 File Organization

### 📄 Documentation Files (Read These!)

| File | Purpose | When to Read |
|------|---------|--------------|
| **PROJECT_SUMMARY.md** | Project overview | First! |
| **QUICKSTART.md** | 5-minute setup | Want to start now |
| **README.md** | Complete documentation | Need full details |
| **API.md** | API reference | Coding/integration |
| **ARCHITECTURE.md** | System design | Want deep understanding |
| **WORKFLOW.md** | Visual diagrams | Visual learner |

### 💻 Core Application Files

| File | Purpose | Lines | Edit if... |
|------|---------|-------|-----------|
| **app.py** | Streamlit UI | ~350 | Change UI/UX |
| **src/agent.py** | Main orchestrator | ~300 | Change workflow |
| **src/tools.py** | Extraction tools | ~350 | Add extraction logic |
| **src/schema.py** | Data models | ~250 | Add/modify fields |
| **src/prompts.py** | LLM prompts | ~200 | Change LLM behavior |
| **src/pdf_processor.py** | PDF handling | ~300 | PDF processing |
| **src/database.py** | Storage (optional) | ~250 | Database changes |
| **src/config.py** | Configuration | ~100 | Settings/env vars |

### 🧪 Testing & Examples

| File/Dir | Purpose | Run with |
|----------|---------|----------|
| **tests/test_agent.py** | Test suite | `python tests/test_agent.py` |
| **tests/sample_inputs/** | Sample data | Use for testing |
| **examples/usage_examples.py** | Usage demos | `python examples/usage_examples.py` |

### ⚙️ Configuration Files

| File | Purpose |
|------|---------|
| **requirements.txt** | Python dependencies |
| **.gitignore** | Git ignore rules |

## 🎓 Learning Path

### Path 1: Quick Start (30 minutes)
1. Read QUICKSTART.md (5 min)
2. Install Ollama + dependencies (15 min)
3. Run `streamlit run app.py` (2 min)
4. Try sample inputs (8 min)

### Path 2: Developer (2 hours)
1. Read README.md (15 min)
2. Read API.md (20 min)
3. Study src/agent.py (30 min)
4. Run examples/usage_examples.py (20 min)
5. Modify and test (35 min)

### Path 3: Deep Dive (4+ hours)
1. Read all documentation (1 hour)
2. Study all source files (2 hours)
3. Trace through workflow (30 min)
4. Experiment with modifications (30+ min)

## 🔍 Quick Reference

### Common Tasks

**Start the app:**
```bash
streamlit run app.py
```

**Run tests:**
```bash
python tests/test_agent.py
```

**Use programmatically:**
```python
from src.agent import OrderExtractionAgent
agent = OrderExtractionAgent()
result = agent.extract_order(text)
```

**Process PDF:**
```python
result = agent.process_pdf("document.pdf")
```

**Save to database:**
```python
from src.database import OrderDatabase
db = OrderDatabase()
order_id = db.save_order(result)
```

### File Size Reference

Total project size:
- **~5,800 lines** of code and documentation
- **20+ files** across multiple directories
- **100% Python** with Markdown docs

### Dependencies

Core dependencies:
- `langchain` - Agent framework
- `ollama` - LLM integration
- `streamlit` - Web UI
- `pydantic` - Data validation
- `pypdf2` + `pdfplumber` - PDF processing

See **requirements.txt** for complete list.

## 🎯 Quick Navigation by Task

### Want to... → Go to...

| Task | File(s) |
|------|---------|
| Run the app | `app.py` |
| Understand extraction | `src/agent.py`, `WORKFLOW.md` |
| Add custom field | `src/schema.py` |
| Modify extraction logic | `src/tools.py` |
| Change UI | `app.py` |
| Adjust prompts | `src/prompts.py` |
| Configure settings | `src/config.py` |
| Add database features | `src/database.py` |
| See examples | `examples/usage_examples.py` |
| Test with samples | `tests/sample_inputs/` |

## 💡 Tips for Navigation

### First Time Users
1. Start with PROJECT_SUMMARY.md
2. Then QUICKSTART.md
3. Run the app and try it out
4. Come back to docs as needed

### Developers
1. API.md for reference
2. src/agent.py to understand flow
3. examples/ for patterns
4. Experiment and iterate

### Customizers
1. ARCHITECTURE.md for design
2. Identify the file to modify (table above)
3. Make changes
4. Test with test suite

## 📞 Getting Help

### Documentation Order
1. **PROJECT_SUMMARY.md** - High-level overview
2. **QUICKSTART.md** - Setup help
3. **README.md** - General questions
4. **API.md** - API/coding questions
5. **ARCHITECTURE.md** - Design questions
6. **WORKFLOW.md** - Flow visualization

### Debugging
1. Check logs in `logs/agent.log`
2. Enable debug mode in UI
3. Run with `verbose=True`
4. Check `tests/test_agent.py` for working examples

## 🎊 Project Statistics

```
📦 Order Extraction Agent
├── 📄 Documentation:  ~3,500 lines
├── 💻 Source Code:    ~2,000 lines
├── 🧪 Tests/Examples: ~300 lines
├── 📁 Files:          20+
├── 🎨 UI:            Streamlit
├── 🤖 AI:            Ollama + Llama 3.2
└── ⚡ Status:        Production Ready
```

## ✅ What's Included

- ✅ Complete web application
- ✅ CLI/programmatic interface
- ✅ PDF, text, email support
- ✅ LangChain agent orchestration
- ✅ Ollama LLM integration
- ✅ Confidence scoring
- ✅ Data validation
- ✅ Optional database storage
- ✅ Comprehensive documentation
- ✅ Test suite with samples
- ✅ Usage examples
- ✅ Production-ready code

---

**Ready to start?** → [QUICKSTART.md](QUICKSTART.md)

**Need the big picture?** → [README.md](README.md)

**Want API docs?** → [API.md](API.md)

**Happy building! 🚀**
