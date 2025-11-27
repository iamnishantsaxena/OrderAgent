# Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Ollama (optional if already then no need)

**macOS/Linux:**
```bash
cd Full_order_agent_application (mandatory as you need to be inside this folder to run this project hassle free)
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [https://ollama.com/download](https://ollama.com/download)

### Step 2: Pull the Model

```bash
ollama pull llama3.2:latest
```

This will download the Llama 3.2 model (~2GB). Wait for it to complete.

### Step 3: Install Python Dependencies

```bash
#Install uv (optional if already done then no need)
curl -LsSf https://astral.sh/uv/install.sh | sh

#Refer this website for more details about uv
https://docs.astral.sh/uv/

# Create virtual environment
uv venv --python=3.12

# Activate it
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Install requirements
uv pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
ollama serve (In seperate bash/terminal window)
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 🎯 First Test

1. Click **"Initialize Agent"** in the sidebar
2. Select **"Paste Text/Email"** tab
3. Copy this example:

```
Order from: John Smith
Email: john@example.com
5 laptops at $1000 each
Ship to: 123 Main St, City, State 12345
</```

4. Click **"Generate Order JSON"**
5. Review the extracted order!

## 📊 Test with Samples

Run the test suite with sample data:

```bash
python tests/test_agent.py
```

This will process all sample files in `tests/sample_inputs/`

## 🔧 Troubleshooting

### "Connection refused" or "Ollama not found"

**Fix:**
```bash
# Check if Ollama is running
ollama list

# If not, it should start automatically
# On Linux/Mac, you can also manually start:
ollama serve
```

### "Model not found"

**Fix:**
```bash
ollama pull llama3.2:latest
```

### Slow performance

**Solutions:**
1. Use a smaller model:
   ```bash
   ollama pull llama3.2:1b
   ```
   Then select it in the Streamlit sidebar

2. Reduce PDF chunk size in settings

3. Close other applications

### Import errors

**Fix:**
```bash
uv pip install --upgrade -r requirements.txt
```

## 💡 Tips

### Better Results

1. **Be specific**: More detailed input = better extraction
2. **Structure helps**: Headers and clear labels improve accuracy
3. **PDF quality**: Better quality PDFs = better text extraction

### Performance

- **Batch processing**: Process multiple orders sequentially
- **Model choice**: llama3.2:1b is faster, llama3.2:latest is more accurate
- **Temperature**: Lower (0.1) = more consistent, Higher (0.5) = more creative

### Customization

Edit `src/schema.py` to add custom fields:
```python
class Order(BaseModel):
    # Add your field here
    custom_field: Optional[str] = None
```

## 📚 Next Steps

1. Try the sample files in `tests/sample_inputs/`
2. Upload your own PDFs or paste real emails
3. Customize the schema for your needs
4. Integrate with your existing systems

## 🆘 Need Help?

Check the main README.md for:
- Full documentation
- Architecture details
- Advanced configuration
- API usage examples

## 🎓 Learning More

- **LangChain**: [docs.langchain.com](https://docs.langchain.com)
- **Ollama**: [ollama.com/docs](https://ollama.com/docs)
- **Streamlit**: [docs.streamlit.io](https://docs.streamlit.io)

---

**Ready to extract orders? Let's go! 🚀**
