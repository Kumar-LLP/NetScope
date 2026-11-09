# Contributing to NetScope

Thank you for your interest in contributing to **NetScope**! We welcome bug reports, feature suggestions, documentation enhancements, and pull requests.

## Development Guidelines

1. **Environment Setup**:
   - Python 3.10+ with `virtualenv`.
   - Node.js 18+ with `npm`.
   - Windows 11 or Linux operating system.

2. **Backend Development**:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pytest tests/
   ```

3. **Frontend Development**:
   ```powershell
   cd frontend
   npm.cmd install
   npm.cmd run dev
   npm.cmd run build
   ```

4. **Code Quality**:
   - Maintain type safety across all React components and TypeScript definitions.
   - Pydantic models must strictly validate all incoming API payloads.
   - External command execution must never use `shell=True`.
   - Write tests for any new network diagnostic capabilities.

5. **Submitting a Pull Request**:
   - Create a feature branch (`git checkout -b feature/awesome-diagnostic`).
   - Run existing unit tests (`pytest tests/`).
   - Run frontend build checks (`npm run build`).
   - Commit with clear, descriptive commit messages.
   - Open a PR against the `main` branch.
