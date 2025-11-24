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

## Project Structure

```
CY-590-Adversarial-Project/
├── attacks/                    # Attack implementation
│   ├── attack_runner.py        # Core attack execution engine
│   ├── attack_result.py        # Result data structures
│   └── prompt_loader.py        # JSON prompt loading utilities
├── defenses/                   # Defense implementation
│   ├── system_prompts.py       # Defensive system prompt engineering
│   ├── input_filters.py        # Input layer defenses (encoding, keywords)
│   ├── output_validators.py    # Output layer defenses (refusal enforcement)
│   └── session_context_tracker.py  # Multi-turn attack detection
├── evaluation/                 # Evaluation system
│   ├── response_evaluator.py   # Jailbreak success detection
│   └── metrics.py              # Statistics and reporting
├── models/                     # Model interface
│   └── mistral_interface.py    # Ollama/Mistral wrapper
├── prompts/                    # Attack prompts and test data
│   ├── jailbreak_attacks/      # 10 categories of jailbreak prompts
│   ├── harmful_requests/       # Test harmful queries
│   ├── base_prompts/           # Safe baseline prompts
│   └── encoding_utils.py       # Obfuscation encoding functions
├── results/                    # Test results (CSV/JSON)
├── run_no_defense_full.py      # Run attacks WITHOUT defense
├── run_strong_defense_full.py  # Run attacks WITH defense
└── example_attack.py           # Example usage script
```

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
   pip install -r requirements.txt
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

## Running Experiments

### Run Attacks Without Defense (Baseline)

```powershell
python run_no_defense_full.py
```

This runs all jailbreak attack combinations against the undefended model and saves results to `results/no_defense_full_TIMESTAMP.csv`.

### Run Attacks With Defense

```powershell
python run_strong_defense_full.py
```

This runs the same attacks against the defended model (system prompt + input filters + output validators) and saves results to `results/strong_defense_full_TIMESTAMP.csv`.

### Quick Example

```powershell
python example_attack.py
```

Runs a demonstration of the attack framework with sample output.

## Attack Categories

The project implements 10 categories of jailbreaking attacks:

| Category | Description | Example Techniques |
|----------|-------------|-------------------|
| **Roleplay** | Persona-based attacks | DAN, Developer Mode, Evil AI |
| **Hypothetical** | Fictional framing | "What if" scenarios, thought experiments |
| **Payload Splitting** | Multi-turn building | Sequential context injection |
| **Obfuscation** | Encoding attacks | Base64, hex, leetspeak, homoglyphs |
| **Competing Objectives** | Priority manipulation | Ethical dilemmas, instruction hierarchy |
| **Context Manipulation** | Delimiter injection | Prompt stuffing, format confusion |
| **Refusal Suppression** | Force compliance | Format constraints, affirmation priming |
| **Cognitive Hacking** | Logical tricks | Paradoxes, false premises, authority claims |
| **Social Engineering** | Psychological manipulation | Emotional appeals, urgency |
| **Token Manipulation** | Tokenization exploits | Special tokens, whitespace, unicode |

## Defense Implementation

### Defense Layers

1. **System Prompt Engineering** (`defenses/system_prompts.py`)
   - Comprehensive safety instructions
   - Jailbreak pattern awareness
   - Explicit refusal guidelines

2. **Input Filters** (`defenses/input_filters.py`)
   - Encoding detection (base64, hex)
   - Delimiter and tag removal
   - Harmful keyword blocking

3. **Output Validators** (`defenses/output_validators.py`)
   - Refusal enforcement
   - Step-by-step instruction detection
   - Fiction framing detection

4. **Session Context Tracking** (`defenses/session_context_tracker.py`)
   - Multi-turn attack detection
   - Progressive suspicion scoring

## Evaluation System

### Metrics Calculated

- **Overall success rate**: Percentage of successful jailbreaks
- **Success by category**: Which attack types are most effective
- **Success by severity**: How severity affects success rates
- **Baseline vs defense**: Improvement from defense implementation
- **Top effective attacks**: Individual attacks with highest success

### Running Evaluation

Results are automatically evaluated using keyword-based detection:
- Refusal patterns (74 phrases)
- Compliance indicators (18 phrases)
- Response length analysis

## Results

Test results are saved to the `results/` directory:
- **CSV files**: Full attack results with all metadata
- **JSON files**: Aggregated metrics and statistics

## License

This project is for educational purposes as part of CY-590 Adversarial AI coursework.

## Ethical Guidelines

All testing is conducted on locally-hosted open-source models in accordance with responsible AI security research practices. This research aims to improve AI safety, not enable malicious use.
