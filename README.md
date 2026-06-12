# Diet Analysis – Cloud-Native Application
**Project 1 | Task 4: CI/CD Pipeline with GitHub Actions**

## Repository Structure
```
diet-analysis/
├── data_analysis.py              # Task 1 – data processing & visualisation
├── lambda_function.py            # Task 3 – serverless function (Azurite)
├── Dockerfile                    # Task 2 – containerisation
├── requirements.txt
├── tests/
│   └── test_data_analysis.py     # Unit tests (pytest)
└── .github/
    └── workflows/
        └── deploy.yml            # Task 4 – CI/CD pipeline
```

## CI/CD Pipeline Stages

| Stage | Tool | Description |
|-------|------|-------------|
| Lint | flake8 | Catch syntax errors & code-style issues |
| Test | pytest | Run unit tests against `data_analysis.py` |
| Build | Docker Buildx | Build the container image |
| Push | Docker Hub | Publish image (main branch only) |
| Deploy | Docker run | Smoke-test the published image |

## Setup

### 1. Fork / clone this repo
```bash
git clone https://github.com/<your-username>/diet-analysis.git
cd diet-analysis
```

### 2. Add GitHub Secrets
Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|--------|-------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub Access Token (generate at hub.docker.com → Account Settings → Security) |

### 3. Push to trigger the pipeline
```bash
git add .
git commit -m "Setup CI/CD pipeline simulation"
git push origin main
```

Monitor the run under the **Actions** tab of your repository.

## Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run analysis (requires All_Diets.csv in the working directory)
python data_analysis.py

# Build & run Docker container
docker build -t diet-analysis .
docker run --rm -v $(pwd)/All_Diets.csv:/app/All_Diets.csv diet-analysis
```
