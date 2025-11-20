# CY-590-Adversarial-Project: Jailbreaking & Prompt Injection

## Project Overview

This project explores the offensive and defensive aspects of adversarial AI by developing prompt injection and jailbreaking attacks against the open-source Mistral language model, then implementing corresponding defenses.

### Why This Matters

As LLMs become integrated into critical applications, understanding their vulnerabilities is essential for:
- Building robust AI safety mechanisms
- Developing effective guardrails for production systems
- Understanding real-world attack vectors against AI systems
- Creating better security practices for LLM deployment

### Project Goals

1. **Attack Development**: Create and test various prompt injection and jailbreaking techniques against Mistral
2. **Defense Implementation**: Develop countermeasures including system prompt engineering, input filtering, and model fine-tuning
3. **Quantitative Evaluation**: Measure attack success rates and defense effectiveness with minimal impact on legitimate use

## Setup Instructions

### Prerequisites

- Windows 10/11 (or macOS/Linux with appropriate modifications)
- Python 3.13+ 
- At least 4GB of available RAM
- ~4GB of disk space for the model

### Installation Steps

1. **Clone the Repository**
   ```powershell
   git clone https://github.com/tyehuan1/CY-590-Adversarial-Project.git
   cd CY-590-Adversarial-Project
   ```

2. **Install Ollama**
   
   Download and install Ollama from [ollama.com](https://ollama.com/download)
   
   After installation, restart your terminal.

3. **Install Python Dependencies**
   ```powershell
   pip install ollama
   ```

4. **Download the Mistral Model**
   
   We use a quantized version to reduce memory requirements:
   ```powershell
   python -c "import ollama; ollama.pull('mistral:7b-instruct-q4_0')"
   ```
   
   This will download ~4GB. It may take a few minutes depending on your connection.

5. **Verify Installation**
   ```powershell
   python -c "from models import MistralInterface; m = MistralInterface(model_name='mistral:7b-instruct-q4_0'); print(m.generate('Hello'))"
   ```

   or run our interface:

   ```powershell
   python models/mistral_interface.py
   ```

## Troubleshooting

### "model requires more system memory"

Use the smaller quantized model:
```powershell
python -c "import ollama; ollama.pull('mistral:7b-instruct-q4_0')"
```

### "ModuleNotFoundError: No module named 'ollama'"

Install the ollama Python package:
```powershell
python -m pip install ollama
```

### "ollama: command not found"

Either:
1. Restart your terminal after installing Ollama
2. Use Python to pull models: `python -c "import ollama; ollama.pull('mistral')"`

### Slow response times

This is expected with the quantized model on systems with limited RAM. For faster responses:
- Close other applications to free memory
- Consider using a machine with more RAM
- Use Ollama's API caching (responses get faster after first use)


## License

This project is for educational purposes as part of CY-590 Adversarial AI coursework.

## Ethical Guidelines

All testing is conducted on locally-hosted open-source models in accordance with responsible AI security research practices. This research aims to improve AI safety, not enable malicious use.