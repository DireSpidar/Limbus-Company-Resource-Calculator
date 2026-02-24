# GitHub Actions Workflow Summary

This document provides a brief overview of the automated workflows (CI/CD) configured for this repository. These workflows ensure code quality and security by running on every push and pull request across all branches.

---

## 1. Lint Workflow (`lint.yml`)

The **Lint** workflow focuses on code style, formatting, and correctness. It's designed to be fast and provide immediate feedback.

### Tools Used:
*   **Actionlint**: Automatically checks GitHub Actions workflow files (`.yml` files in `.github/workflows/`) for syntax errors and best practices.
*   **Ruff**: An extremely fast Python linter and formatter. It replaces multiple tools like Flake8, Isort, and Black, ensuring Python code adheres to PEP 8 and other standards.
*   **Mypy**: Performs static type checking on Python source code, helping to catch "NoneType" errors and other logic issues early.
*   **Yamllint**: Validates all YAML files in the repository (e.g., `.github/dependabot.yml`, workflow files) for correct syntax and formatting.

---

## 2. Security Workflow (`security.yml`)

The **Security** workflow is dedicated to identifying vulnerabilities and protecting sensitive information. It includes scheduled scans as well as push/PR triggers.

### Tools Used:
*   **CodeQL (SAST)**: GitHub's Static Analysis Security Testing tool. It analyzes the codebase to find potential security vulnerabilities like SQL injection, cross-site scripting (XSS), and more.
*   **Gitleaks**: A secret detection tool that scans the repository's history and current files for accidentally committed API keys, passwords, or other sensitive credentials.
*   **Bandit**: A security linter specifically for Python. It scans Python source code for common security issues, such as the use of insecure functions or modules.
*   **Pip-audit (SCA)**: A dependency vulnerability scanner that checks Python packages listed in `requirements.txt` against known CVEs.

---

## 3. Dependabot (`dependabot.yml`)

**Dependabot** automates the process of keeping dependencies up-to-date by monitoring for new releases and creating pull requests.

### Ecosystems Monitored:
*   **Pip**: Monitors Python dependencies for updates and security vulnerabilities.
*   **GitHub Actions**: Ensures that the GitHub Actions used in workflows are running on the latest stable versions.

---

## Trigger Summary

*   **Pushes**: Triggers on every push to any branch.
*   **Pull Requests**: Triggers on every PR targeting any branch.
*   **Scheduled**: 
    *   **Security Workflow**: Runs every Monday at 09:00 UTC.
    *   **Dependabot**: Runs weekly to check for updates and security vulnerabilities in dependencies.
