## Github action with dockerhub along with cicd and unit test

### activate the conda environment :(e.g.,)

`conda activate /Users/baqirrizvi/Desktop/MLOps/github-action-with-dockerhub/action`

---

# CI/CD with github action :

[![CI status](https://img.shields.io/badge/ci-github--actions-blue.svg)](#)
![CI/CD](https://github.com/264Gaurav/githubAction-with-dockerHub/actions/workflows/ci.yml/badge.svg)

## Purpose

This README explains the CI/CD setup used with this repository: GitHub Actions workflows that run linting and tests, build Docker images, and push them to Docker Hub. It also documents how the `cicd.yml` pipeline works, how tags are generated, and how to configure repository secrets.

---

## Quick summary

- **CI**: Linting (flake8) and testing (pytest) run on push and pull requests to `main`.
- **CD**: When a push happens on `main`, the pipeline builds a Docker image and pushes it to Docker Hub (requires secrets).
- **Files**: `/.github/workflows/cicd.yml` (this workflow) and `Dockerfile` at repo root.

---

## What is CI/CD (brief)

**Continuous Integration (CI)** means automatically verifying code changes (lint, tests) every time code is pushed or a PR is opened. This catches regressions early.

**Continuous Delivery / Deployment (CD)** means automatically building artifacts (Docker images) and delivering them to a registry or environment when changes land on the main branch.

Using GitHub Actions we implement CI/CD by defining workflows that run jobs on GitHub-hosted runners.

---

## GitHub Actions in this repo — high level

The workflow `cicd.yml` contains two main jobs:

1. **build-and-test** (runs on push and PRs to `main`)

   - Checks out code
   - Sets up Python (3.10)
   - Installs deps (`pip install -r requirements.txt` when present)
   - Runs `flake8` (two passes: error fail and warnings)
   - Runs `pytest`

2. **deploy** (runs only on pushes to `main`, depends on `build-and-test`)

   - Checks out code
   - Sets up QEMU and Buildx (for multi-arch builds)
   - Logs in to Docker Hub using secrets
   - Builds & pushes Docker image(s) using `docker/build-push-action@v4`

This layout prevents deployment when tests or linting fail.

---

## `cicd.yml` understanding — pipeline created & executed

The pipeline (`.github/workflows/cicd.yml`) is configured to run automatically when:

- A push is made to `main` (CI + possible CD), or
- A pull request targets `main` (CI only).

When you push to `main`:

- GitHub Actions starts the workflow. The `build-and-test` job runs first and must succeed.
- If it passes and the event is a push to `main`, the `deploy` job runs. `deploy` builds and **pushes** the Docker image(s) to Docker Hub.

Execution evidence:

- Each workflow run is visible in the repository's **Actions** tab, showing job start/end times, logs for every step, and whether each job succeeded or failed. Successful runs show green checks and include the pushed Docker tags in the build logs.

---

## Docker images & tagging

The workflow tags images with a combination of tags for traceability. Typical tags used:

- `:latest` — the most recent build from `main`.
- `:${VERSION}` — optional semantic version read from a `VERSION` file (if present).
- `:${SHORT_SHA}` — short 7-character commit SHA for quick referencing.
- `:${FULL_SHA}` (or `${{ github.sha }}`) — full 40-character commit SHA for exact reproducibility.

**IMAGE_NAME** should be set to a value like `myuser/my-app`. The recommended pattern is to store the full name in a single secret (e.g. `DOCKER_IMAGE` = `myuser/my-app`) and use it in the workflow.

---

## Required repository secrets

Set these in **Settings → Secrets and variables → Actions**:

- `DOCKER_USERNAME` — Docker Hub username or org
- `DOCKER_PASSWORD` — Docker Hub password or access token
- `DOCKER_IMAGE` — full image name, e.g. `myuser/my-app` (recommended)

Alternative (less recommended): store username and image repo separately and compose them in the workflow.

---

## Example `cicd.yml` (one-file reference)

> The actual workflow file lives at `.github/workflows/cicd.yml` in this repo. Below is the structure and important parts (already created and used by the project). Use this as a quick reference to what runs and why.

```yaml
name: githubAction with dockerhub

on:
  push:
    branches: ['main']
  pull_request:
    branches: ['main']

permissions:
  contents: read

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.10
        uses: actions/setup-python@v3
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 pytest
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      - name: Lint with flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
      - name: Test with pytest
        run: |
          pytest

  deploy:
    name: Build and push Docker image to Docker Hub
    needs: build-and-test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      IMAGE_NAME: ${{ secrets.DOCKER_IMAGE }}
    steps:
      - uses: actions/checkout@v4
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v2
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      - name: Log in to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - name: Set tags
        id: set-tags
        run: |
          SHORT_SHA=$(echo "$GITHUB_SHA" | cut -c1-7)
          echo "SHORT_SHA=$SHORT_SHA" >> $GITHUB_ENV
          if [ -f VERSION ]; then echo "VERSION=$(cat VERSION)" >> $GITHUB_ENV; else echo "VERSION=$SHORT_SHA" >> $GITHUB_ENV; fi
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          file: ./Dockerfile
          push: true
          platforms: linux/amd64,linux/arm64
          tags: |
            ${{ env.IMAGE_NAME }}:latest
            ${{ env.IMAGE_NAME }}:${{ env.VERSION }}
            ${{ env.IMAGE_NAME }}:${{ env.SHORT_SHA }}
            ${{ env.IMAGE_NAME }}:${{ github.sha }}
```

---

## How to test locally

- Run unit tests:

  ```bash
  pip install -r requirements.txt
  pytest
  ```

- Build and push Docker image locally (example):

  ```bash
  docker buildx build -t myuser/my-app:latest -t myuser/my-app:1.2.3 --push .
  ```

---

## Troubleshooting (common errors)

- **`tag is needed when pushing to registry`**: Occurs when `push: true` is set but no `tags:` are provided. Fix: add at least one tag.
- **`IMAGE_NAME is empty`**: Ensure `DOCKER_IMAGE` secret exists and is referenced correctly.
- **Docker login fails**: Verify `DOCKER_USERNAME` and `DOCKER_PASSWORD` (or token) are correct and have push permission.
- **Dockerfile not found**: Confirm `file: ./Dockerfile` path relative to the repo root.

---

## Where to view pipeline runs and logs

Visit the **Actions** tab in the GitHub repository. Select the workflow run, open a job, and expand steps to view detailed logs. The deploy job logs contain the `docker/build-push-action` output showing tags and push status.

---

## FAQ / Tips

- Prefer storing full image name in a single secret (`DOCKER_IMAGE`) to avoid composition errors.
- Use Git tags + `on: push: tags:` to create release images matching semantic versions.
- Consider adding image scanning or signing steps for production deployments.
