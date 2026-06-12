# Task 4 – CI/CD Pipeline: Step-by-Step Guide

This guide walks you through everything you need to do for Task 4 from scratch. No steps are skipped.

---

## What You're Actually Doing

You're setting up a CI/CD pipeline using GitHub Actions. Every time you push code to GitHub, the pipeline will automatically:
1. Check your code for errors (lint)
2. Run your unit tests
3. Build a Docker image
4. Push it to Docker Hub
5. Simulate a deployment by running the container

---

## Part 1 — Accounts You Need

### 1.1 Create a GitHub account (if you don't have one)
1. Go to [https://github.com](https://github.com)
2. Click **Sign up** and create an account
3. Verify your email

### 1.2 Create a Docker Hub account (if you don't have one)
1. Go to [https://hub.docker.com](https://hub.docker.com)
2. Click **Sign up** and create a free account
3. Remember the username you choose — you'll need it later

---

## Part 2 — Create a GitHub Repository

1. Log in to GitHub
2. Click the **+** button in the top right corner → **New repository**
3. Name it: `diet-analysis`
4. Set it to **Public**
5. **Do NOT** tick "Add a README file" (we'll push our own)
6. Click **Create repository**
7. Copy the repository URL — it looks like: `https://github.com/YOUR_USERNAME/diet-analysis.git`

---

## Part 3 — Set Up Your Project Files Locally

Open a terminal on your Ubuntu VM.

### 3.1 Create the project folder
```bash
mkdir diet-analysis
cd diet-analysis
```

### 3.2 Create the folder structure
```bash
mkdir -p .github/workflows
mkdir tests
```

Your folder should look like this when you're done:
```
diet-analysis/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── tests/
│   └── test_data_analysis.py
├── data_analysis.py
├── Dockerfile
├── requirements.txt
└── .gitignore
```

### 3.3 Create each file

**File 1: `data_analysis.py`** — copy and paste this exactly:

```python
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json


CSV_PATH = os.environ.get("CSV_PATH", "All_Diets.csv")


def load_data(path=CSV_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"cant find the csv file at: {path}")
    df = pd.read_csv(path)
    return df


def clean_data(df):
    # convert protein/carbs/fat to numbers in case there's any weird string values
    for col in ["Protein(g)", "Carbs(g)", "Fat(g)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # fill any missing values with the average of that column
    df.fillna(df.select_dtypes(include="number").mean(), inplace=True)
    return df


def analyse(df):
    # get average protein, carbs, fat for each diet type
    avg_macros = df.groupby("Diet_type")[["Protein(g)", "Carbs(g)", "Fat(g)"]].mean()

    # find top 5 highest protein recipes in each diet type
    top_protein = (
        df.sort_values("Protein(g)", ascending=False)
        .groupby("Diet_type")
        .head(5)
    )

    # which diet type has the highest protein overall
    best_protein_diet = avg_macros["Protein(g)"].idxmax()

    # most common cuisine for each diet type
    common_cuisine = (
        df.groupby("Diet_type")["Cuisine_type"]
        .agg(lambda x: x.value_counts().index[0])
    )

    # add ratio columns
    df["Protein_to_Carbs_ratio"] = df["Protein(g)"] / df["Carbs(g)"].replace(0, float("nan"))
    df["Carbs_to_Fat_ratio"] = df["Carbs(g)"] / df["Fat(g)"].replace(0, float("nan"))

    return avg_macros, top_protein, best_protein_diet, common_cuisine


def plot(avg_macros, top_protein, out_dir="outputs"):
    os.makedirs(out_dir, exist_ok=True)

    # bar chart for average macros
    avg_macros.plot(kind="bar", figsize=(12, 6))
    plt.title("Average Macronutrient Content by Diet Type")
    plt.ylabel("Amount (g)")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/avg_macros_bar.png")
    plt.close()

    # heatmap to see the relationship between macros and diet types
    plt.figure(figsize=(10, 6))
    sns.heatmap(avg_macros, annot=True, fmt=".1f", cmap="YlOrRd")
    plt.title("Macronutrient Heatmap by Diet Type")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/macros_heatmap.png")
    plt.close()

    # scatter plot for top protein recipes
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=top_protein, x="Protein(g)", y="Fat(g)", hue="Cuisine_type")
    plt.title("Top 5 Protein-Rich Recipes by Cuisine")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/top_protein_scatter.png")
    plt.close()


def main():
    df = load_data()
    df = clean_data(df)
    avg_macros, top_protein, best_protein_diet, common_cuisine = analyse(df)

    print("Average macronutrients per diet type:")
    print(avg_macros.to_string())
    print(f"\nDiet type with highest average protein: {best_protein_diet}")
    print("\nMost common cuisine per diet type:")
    print(common_cuisine.to_string())

    # save results to json file (simulating nosql storage)
    summary = avg_macros.reset_index().to_dict(orient="records")
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    plot(avg_macros, top_protein)
    print("\ndone, charts saved to outputs folder")


if __name__ == "__main__":
    main()
```

---

**File 2: `tests/test_data_analysis.py`** — copy and paste this:

```python
import pandas as pd
import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_analysis import clean_data, analyse


# some fake data to use in the tests
@pytest.fixture
def sample_df():
    data = {
        "Diet_type":    ["Paleo", "Paleo", "Keto", "Keto", "Vegan", "Vegan"],
        "Recipe_name":  ["Recipe A", "Recipe B", "Recipe C", "Recipe D", "Recipe E", "Recipe F"],
        "Cuisine_type": ["american", "mexican", "italian", "american", "indian", "french"],
        "Protein(g)":   [30.0, 50.0, 20.0, 80.0, 10.0, 15.0],
        "Carbs(g)":     [10.0, 20.0, 5.0, 15.0, 40.0, 30.0],
        "Fat(g)":       [15.0, 25.0, 30.0, 40.0, 5.0, 8.0],
    }
    return pd.DataFrame(data)


# data with some missing values to test the cleaning function
@pytest.fixture
def dirty_df():
    data = {
        "Diet_type":    ["Paleo", "Keto", "Vegan"],
        "Recipe_name":  ["R1", "R2", "R3"],
        "Cuisine_type": ["american", "italian", "french"],
        "Protein(g)":   [30.0, None, 10.0],
        "Carbs(g)":     [10.0, 5.0, None],
        "Fat(g)":       [None, 30.0, 5.0],
    }
    return pd.DataFrame(data)


class TestCleanData:
    def test_no_nulls_after_cleaning(self, dirty_df):
        cleaned = clean_data(dirty_df)
        assert cleaned[["Protein(g)", "Carbs(g)", "Fat(g)"]].isnull().sum().sum() == 0

    def test_missing_protein_filled_with_mean(self, dirty_df):
        # keto row has no protein value, should be filled with mean of the other two
        expected_mean = dirty_df["Protein(g)"].mean()
        cleaned = clean_data(dirty_df.copy())
        assert cleaned.loc[1, "Protein(g)"] == pytest.approx(expected_mean)

    def test_handles_string_values(self):
        # sometimes the csv has "N/A" or other strings in numeric columns
        df = pd.DataFrame({
            "Diet_type":    ["Paleo"],
            "Recipe_name":  ["R1"],
            "Cuisine_type": ["american"],
            "Protein(g)":   ["N/A"],
            "Carbs(g)":     [5.0],
            "Fat(g)":       [3.0],
        })
        cleaned = clean_data(df)
        assert not np.isnan(cleaned.loc[0, "Protein(g)"])


class TestAnalyse:
    def test_returns_correct_number_of_diet_types(self, sample_df):
        avg_macros, *_ = analyse(sample_df.copy())
        # we have 3 diet types in our test data
        assert avg_macros.shape == (3, 3)

    def test_average_protein_is_correct(self, sample_df):
        avg_macros, *_ = analyse(sample_df.copy())
        # paleo has protein values 30 and 50, so average should be 40
        expected = (30.0 + 50.0) / 2
        assert avg_macros.loc["Paleo", "Protein(g)"] == pytest.approx(expected)

    def test_keto_has_highest_protein(self, sample_df):
        _, _, best_diet, _ = analyse(sample_df.copy())
        # keto average is (20+80)/2 = 50 which is the highest
        assert best_diet == "Keto"

    def test_most_common_cuisine_keto(self, sample_df):
        _, _, _, common_cuisine = analyse(sample_df.copy())
        # in keto we have italian and american, american shows up twice
        assert common_cuisine["Keto"] == "american"

    def test_ratio_columns_added(self, sample_df):
        df = sample_df.copy()
        analyse(df)
        assert "Protein_to_Carbs_ratio" in df.columns
        assert "Carbs_to_Fat_ratio" in df.columns

    def test_top_protein_no_more_than_5(self, sample_df):
        _, top_protein, *_ = analyse(sample_df.copy())
        counts = top_protein.groupby("Diet_type").size()
        assert (counts <= 5).all()
```

---

**File 3: `Dockerfile`**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "data_analysis.py"]
```

---

**File 4: `requirements.txt`**

```
pandas>=1.5.0
matplotlib>=3.6.0
seaborn>=0.12.0
pytest>=7.0.0
azure-storage-blob>=12.14.0
```

---

**File 5: `.gitignore`**

```
__pycache__/
*.pyc
.env
outputs/
*.csv
.DS_Store
```

---

**File 6: `.github/workflows/deploy.yml`** — this is the main CI/CD file:

```yaml
name: diet analysis pipeline

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

env:
  IMAGE_NAME: diet-analysis

jobs:

  lint:
    name: check code style
    runs-on: ubuntu-latest

    steps:
      - name: checkout code
        uses: actions/checkout@v4

      - name: setup python
        uses: actions/setup-python@v5
        with:
          python-version: "3.9"

      - name: install flake8
        run: pip install flake8

      - name: run flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-line-length=120 --statistics

  test:
    name: run unit tests
    runs-on: ubuntu-latest
    needs: lint

    steps:
      - name: checkout code
        uses: actions/checkout@v4

      - name: setup python
        uses: actions/setup-python@v5
        with:
          python-version: "3.9"

      - name: install dependencies
        run: pip install -r requirements.txt

      - name: run tests
        run: pytest tests/ -v --tb=short

  build:
    name: build docker image
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: checkout code
        uses: actions/checkout@v4

      - name: setup docker buildx
        uses: docker/setup-buildx-action@v3

      - name: build the image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: ${{ env.IMAGE_NAME }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: quick check that image works
        run: |
          docker run --rm ${{ env.IMAGE_NAME }}:latest python -c "
          import pandas as pd, matplotlib, seaborn, json, os
          print('all imports working fine')
          "

  push:
    name: push image to docker hub
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    steps:
      - name: checkout code
        uses: actions/checkout@v4

      - name: setup docker buildx
        uses: docker/setup-buildx-action@v3

      - name: login to docker hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    name: simulate deployment
    runs-on: ubuntu-latest
    needs: push
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    steps:
      - name: checkout code
        uses: actions/checkout@v4

      - name: pull the image and run it
        run: |
          docker pull ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:latest

          cat > /tmp/All_Diets.csv << 'EOF'
          Diet_type,Recipe_name,Cuisine_type,Protein(g),Carbs(g),Fat(g),Extraction_day
          Paleo,Bone Broth,american,5.22,1.29,3.2,10/16/2022
          Paleo,Pumpkin Pie,american,30.91,302.59,96.76,10/16/2022
          Keto,Keto Bread,american,8.0,2.0,20.0,10/16/2022
          Keto,Bacon Eggs,american,25.0,1.0,30.0,10/16/2022
          Vegan,Lentil Soup,indian,12.0,35.0,4.0,10/16/2022
          EOF

          docker run --rm \
            -v /tmp/All_Diets.csv:/app/All_Diets.csv \
            -e CSV_PATH=/app/All_Diets.csv \
            ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:latest \
            python data_analysis.py

      - name: done
        run: echo "deployment simulation finished at $(date)"
```

---

## Part 4 — Get a Docker Hub Access Token

You need this so GitHub can push to Docker Hub on your behalf.

1. Log in to [https://hub.docker.com](https://hub.docker.com)
2. Click your profile icon (top right) → **Account Settings**
3. Click **Security** in the left sidebar
4. Click **New Access Token**
5. Give it a name like `github-actions`
6. Set permissions to **Read, Write, Delete**
7. Click **Generate**
8. **Copy the token immediately** — you won't see it again
9. Paste it somewhere safe temporarily (like Notepad)

---

## Part 5 — Add Secrets to GitHub

This is how you securely give GitHub your Docker Hub credentials without hardcoding them in the code.

1. Go to your `diet-analysis` repository on GitHub
2. Click **Settings** (the tab at the top of the repo)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** and add these two secrets:

**Secret 1:**
- Name: `DOCKERHUB_USERNAME`
- Value: your Docker Hub username (e.g. `johndoe`)

**Secret 2:**
- Name: `DOCKERHUB_TOKEN`
- Value: the access token you copied in Part 4

---

## Part 6 — Push Your Code to GitHub

Back in your terminal inside the `diet-analysis` folder:

### 6.1 Install git if needed
```bash
sudo apt install git -y
```

### 6.2 Set up git (first time only)
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### 6.3 Initialize git and push
```bash
git init
git add .
git commit -m "initial commit - add data analysis and cicd pipeline"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/diet-analysis.git
git push -u origin main
```

> Replace `YOUR_USERNAME` with your actual GitHub username.

When it asks for credentials, use your GitHub username and a **Personal Access Token** (not your password). To get one: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token → tick `repo` → generate.

---

## Part 7 — Watch the Pipeline Run

1. Go to your repository on GitHub
2. Click the **Actions** tab at the top
3. You should see a workflow run called **"diet analysis pipeline"** already running
4. Click on it to see each stage
5. Wait for all stages to go green ✅

The stages run in order:
- `check code style` → `run unit tests` → `build docker image` → `push image to docker hub` → `simulate deployment`

**This is what you screenshot for your deliverable.** Make sure the date/time is visible in your screenshots (it shows in the GitHub Actions run timestamp).

---

## Part 8 — Screenshots to Take (for Submission)

Take these screenshots with **date and time visible**:

1. **GitHub Actions overview** — the Actions tab showing the workflow run with green checkmarks ✅
2. **Individual job logs** — click into "run unit tests" and screenshot the pytest output showing tests passed
3. **Docker Hub** — go to hub.docker.com → your repositories → you should see `diet-analysis` was pushed there
4. **Deploy stage log** — screenshot the "simulate deployment" job showing the container ran and printed output

---

## Troubleshooting

**Push fails with authentication error:**
- Make sure you're using a Personal Access Token, not your GitHub password

**Pipeline fails on "push image to docker hub":**
- Double-check your secrets are named exactly `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`
- Make sure the Docker Hub token has write permissions

**Tests fail:**
- Make sure the file is saved as `tests/test_data_analysis.py` (note the `tests/` folder)
- Make sure `data_analysis.py` is in the root folder, not inside `tests/`

**flake8 fails:**
- This usually means a syntax error in `data_analysis.py`, check you copied the code correctly
