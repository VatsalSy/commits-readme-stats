# Contributing to GitHub Commit Stats

Thank you for your interest in contributing! This document outlines the process and guidelines for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a welcoming, inclusive, and harassment-free environment. Be kind and respectful to others.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/commits-readme-stats.git
   cd commits-readme-stats
   ```

3. Set up development environment:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows

   # Install dependencies
   pip install -r requirements.txt

   # Install pre-commit hooks
   pre-commit install
   ```

## Development Process

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests and checks:
   ```bash
   # Run security checks
   safety check -r requirements.txt
   bandit -r . -ll -ii -x ./tests,./venv
   pip-audit -r requirements.txt

   # Run pre-commit hooks
   pre-commit run --all-files
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: your descriptive commit message"
   ```

## Commit Message Guidelines

We follow conventional commits. Format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding/modifying tests
- `chore`: Maintenance tasks

## Pull Request Process

1. Update documentation if needed
2. Ensure all checks pass
3. Update CHANGELOG.md with your changes
4. Create a Pull Request with:
   - Clear title following commit message format
   - Detailed description of changes
   - Reference to related issues

## Security Vulnerabilities

If you find a security vulnerability:
1. **DO NOT** create a public GitHub issue
2. Email vatsalsanjay@gmail.com with details
3. Include steps to reproduce if possible
4. We aim to respond asap

## Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings for functions and classes
- Keep functions focused and small
- Write descriptive variable names

## Testing

- Add tests for new features
- Ensure existing tests pass
- Include both positive and negative test cases
- Document test scenarios

## Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Include example usage where appropriate
- Keep documentation in sync with code

## License

By contributing, you agree that your contributions will be licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Questions?

Feel free to open an issue for:
- Feature proposals
- Bug reports
- Documentation improvements
- General questions

Thank you for contributing! 🎉

