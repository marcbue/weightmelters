# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Weight tracking Django web application built from Cookiecutter Django template. Uses Python 3.13, Django 5.2.10, and UV for package management.

## Common Commands

All commands use UV as the package manager:

```bash
# Install dependencies
uv sync --locked

# Run development server
uv run python manage.py runserver

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/path/to/test_file.py

# Run a specific test
uv run pytest tests/path/to/test_file.py::test_function_name

# Run tests with coverage
uv run coverage run -m pytest && uv run coverage html

# Type checking
uv run mypy weightmelters

# Linting and formatting (via pre-commit)
uv run pre-commit run --all-files

# Database migrations
uv run python manage.py migrate
uv run python manage.py makemigrations

# Create superuser
uv run python manage.py createsuperuser

# Build documentation with live reload
cd docs && uv run make livehtml
```

## Architecture

### Settings Structure
Django settings are environment-based in `config/settings/`:
- `base.py` - Shared settings
- `local.py` - Development (DEBUG=True, console email, debug toolbar)
- `test.py` - Testing (fast password hasher, in-memory email)
- `production.py` - Production (Redis cache, S3 storage, Sentry)

Settings module is controlled by `DJANGO_SETTINGS_MODULE` env var (defaults to `config.settings.local`).

### Application Structure
- `config/` - Django configuration, URLs, WSGI
- `weightmelters/users/` - Custom User model with `name` field (replaces first_name/last_name)
- `weightmelters/templates/` - Django templates with Bootstrap 5 + crispy-forms
- `weightmelters/static/` - CSS, JS, images
- `tests/` - Root-level tests
- `docs/` - Sphinx RST documentation

### Custom User Model
Located at `weightmelters/users/models.py`. Extends `AbstractUser` with a unified `name` field. User-related views use login-required mixins.

### URL Routing
Root URLs in `config/urls.py`. User URLs namespaced under `/users/`:
- `~redirect/` - Redirect to current user's profile
- `~update/` - Update current user
- `<username>/` - View user by username

### Testing
Uses pytest with pytest-django. Test settings in `config/settings/test`. Factories use factory-boy in `weightmelters/users/tests/factories.py`. Fixtures defined in `weightmelters/conftest.py`.

### Code Quality Tools
- **Ruff** - Linting and formatting (config in pyproject.toml)
- **MyPy** - Type checking with django-stubs
- **djLint** - Template linting (profile: django)
- **Pre-commit** - Runs all checks automatically

### Authentication
Uses django-allauth with MFA support. Account templates in `weightmelters/templates/account/`.
