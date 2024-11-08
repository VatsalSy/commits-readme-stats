# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2024-11-07

### Added
- GitHub Action support with customizable inputs:
  - Toggle commit timing patterns display
  - Toggle most productive days display
  - Custom commit messages
- Secure token management with validation and encryption
- Automated security audits and dependency updates
- Commit pattern analysis features:
  - Early bird vs Night owl detection
  - Most productive day of the week analysis
  - Commit frequency by time of day
- Language statistics per repository
- Caching system for improved performance
- Multi-language support through translation system
- Error handling with token masking
- Local development support with debug mode
- Comprehensive logging system

## [1.0.0] - 2024-11-07

### Added
- GitHub Action support with customizable inputs:
  - Toggle commit timing patterns display
  - Toggle most productive days display
  - Custom commit messages
- Secure token management with validation and encryption
- Automated security audits and dependency updates
- Commit pattern analysis features:
  - Early bird vs Night owl detection
  - Most productive day of the week analysis
  - Commit frequency by time of day
- Language statistics per repository
- Caching system for improved performance
- Multi-language support through translation system
- Error handling with token masking
- Local development support with debug mode
- Comprehensive logging system

### Security
- Secure token handling with validation and hashing
- Token masking in error messages
- Rate limiting implementation
- Input validation
- Encrypted caching
- Regular security audits via GitHub Actions
- Dependabot integration for dependency updates
- Pre-commit hooks for security checks

### Dependencies
- Python 3.x support
- Core dependencies:
  - PyGithub 2.5.0
  - GitPython 3.1.43
  - httpx 0.27.2
  - python-dotenv 1.0.1
  - cryptography 43.0.3
  - pytz 2024.2

### Documentation
- Comprehensive README with setup instructions
- Security policy and vulnerability reporting
- License information (MIT)
- Example workflows
- API documentation

For detailed code changes and implementation details, see the [GitHub repository](https://github.com/VatsalSy/commits-readme-stats). 