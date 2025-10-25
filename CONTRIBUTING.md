# Contributing to InfraMind

Thank you for your interest! We welcome contributions of all kinds.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/youruser/inframind.git`
3. **Create a branch**: `git checkout -b feature/my-feature`
4. **Make changes** and commit
5. **Push** to your fork: `git push origin feature/my-feature`
6. **Open a Pull Request** against `main`

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- C++20 compiler (GCC 13 or Clang 17)
- CMake 3.20+

### Local Environment

```bash
# Start services
make up

# Run tests
make test

# Lint
make lint
```

### Python Development

```bash
cd services/api
pip install -e ".[dev]"

# Run API locally
uvicorn app.main:app --reload

# Run tests
pytest -v

# Format
ruff check --fix .
```

### C++ Development

```bash
cd agents/cpp_agent
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build .

# Run tests
ctest --output-on-failure

# Run agent
./inframind_agent
```

## Code Style

### Python

- Use **Ruff** for linting and formatting
- Type hints required for all functions
- Max line length: 100
- Follow PEP 8

### C++

- Use **C++20** features
- Follow [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- Use `clang-format` with provided config
- RAII, no raw pointers

### Groovy (Jenkins)

- Follow Jenkins best practices
- Use `try/catch` for all HTTP requests
- Log all InfraMind operations with `[InfraMind]` prefix

## Testing

### Unit Tests

**Python**:
```bash
cd services/api
pytest tests/ -v --cov=app
```

**C++**:
```bash
cd agents/cpp_agent/build
ctest --output-on-failure
```

### Integration Tests

```bash
# Start services
make up

# Run integration tests
pytest tests/integration/ -v
```

### E2E Tests

```bash
# Requires K3d
make test-e2e
```

## Documentation

- Update `docs/` for new features
- Add docstrings to all Python functions
- Use Doxygen comments for C++ classes
- Update `README.md` if adding major features

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass (`make test`)
- [ ] Code is formatted (`make lint`)
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No merge conflicts

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Changelog updated
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Thompson Sampling for exploration
fix: correct memory safety guard calculation
docs: update API reference for /optimize
refactor: simplify feature engineering pipeline
test: add integration tests for optimizer
```

## Issue Reporting

Use GitHub Issues for:
- **Bugs**: Include logs, reproduction steps, environment
- **Features**: Describe use case and expected behavior
- **Questions**: Tag with `question`

## Code Review

All PRs require:
- At least 1 approval
- All CI checks passing
- No unresolved comments

## License

By contributing, you agree your code is licensed under MIT License.

## Community

- **Discussions**: [GitHub Discussions](https://github.com/yourorg/inframind/discussions)
- **Chat**: [Discord](https://discord.gg/inframind)
- **Twitter**: [@inframind_dev](https://twitter.com/inframind_dev)

## Questions?

Open an issue or reach out on Discord!
