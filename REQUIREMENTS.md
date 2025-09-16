# Requirements and Installation

This document describes the dependencies and installation process for the SWE-bench Generation and Evaluation Pipeline.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/dipikakhullar/vibe-coding.git
cd vibe-coding

# Run the installation script
./install_requirements.sh
```

## Requirements Files

### `requirements.txt` - Full Installation
Contains all dependencies including optional features:
- Core AI/ML frameworks
- SWE-bench evaluation tools
- Development and testing tools
- Monitoring and cloud integration (optional)
- Docker support (for real evaluation)

### `requirements-core.txt` - Minimal Installation
Contains only essential dependencies for basic functionality:
- Core AI/ML frameworks
- SWE-bench evaluation tools
- Basic utilities

## Manual Installation

### Option 1: Full Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### Option 2: Core Installation Only
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies only
pip install -r requirements-core.txt
```

## Key Dependencies

### Required for Basic Functionality
- **inspect-ai** (≥0.4.0): AI evaluation framework
- **datasets** (≥2.14.0): Hugging Face datasets
- **swebench** (≥4.1.0): SWE-bench evaluation harness
- **openai** (≥1.0.0): OpenAI API client
- **requests** (≥2.31.0): HTTP client

### Optional for Enhanced Features
- **docker** (≥6.0.0): For real SWE-bench evaluation
- **wandb** (≥0.15.0): Experiment tracking
- **boto3** (≥1.26.0): AWS cloud integration

## System Requirements

### Minimum Requirements
- Python 3.8+
- 4GB RAM
- 2GB disk space

### Recommended for Full Evaluation
- Python 3.9+
- 8GB RAM
- 10GB disk space
- Docker Desktop (for real SWE-bench evaluation)

## Platform Support

- ✅ **macOS** (Intel and Apple Silicon)
- ✅ **Linux** (Ubuntu 20.04+, CentOS 8+)
- ⚠️ **Windows** (WSL2 recommended)

## Troubleshooting

### Common Issues

1. **Docker not found**
   ```bash
   # Install Docker Desktop
   # macOS: brew install --cask docker
   # Linux: Follow Docker installation guide
   ```

2. **CUDA/GPU issues**
   ```bash
   # Most models run via API, no local GPU required
   # For local models, install appropriate CUDA drivers
   ```

3. **Memory issues**
   ```bash
   # Reduce batch size in configuration
   # Use --limit parameter to process fewer samples
   ```

### Getting Help

- Check `pipeline/EVALUATION_STATUS.md` for current capabilities
- Review individual component READMEs in `pipeline/` directories
- Open an issue on GitHub for bugs or feature requests

## Environment Variables

Set these environment variables for full functionality:

```bash
# Required for OpenRouter API
export OPENROUTER_API_KEY="your-api-key-here"

# Optional: Custom paths
export SWE_SPLIT="test"  # or "dev"
export PRED_PATH="results/predictions.jsonl"
```

## Verification

After installation, verify everything works:

```bash
# Test basic functionality
python pipeline/run_full_pipeline.py --limit 1 --skip-eval

# Test with evaluation
python pipeline/run_full_pipeline.py --limit 1
```
