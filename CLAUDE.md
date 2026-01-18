# CLAUDE.md

## Project Overview

Weight challenge app where users log daily weights and view a shared Plotly graph of all participants. Built with Django 5.2, HTMX, and Plotly.

**Stack:** Python 3.13, Django 5.2, HTMX, Plotly, Bootstrap 5, django-allauth, UV package manager

## Development Approach

**Test-Driven Development (TDD):** Write tests before implementing features. For each new feature:
1. Write failing tests first
2. Implement the minimum code to pass
3. Refactor as needed

## Common Commands

```bash
uv sync --locked              # Install dependencies
uv run pytest                 # Run all tests
uv run pytest path/to/test.py # Run specific test file
uv run mypy weightmelters     # Type checking
uv run pre-commit run --all-files  # Linting/formatting
uv run python manage.py runserver  # Dev server
uv run python manage.py makemigrations
uv run python manage.py migrate
```

## Project Structure

```
config/
├── settings/          # Environment-based settings (base, local, test, production)
└── urls.py            # Root URL routing

weightmelters/
├── weights/           # Core weight tracking app
│   ├── models.py      # WeightEntry model
│   ├── views.py       # HTMX views (log, graph, delete, entries)
│   ├── home_views.py  # Homepage view with form prefilling
│   ├── forms.py       # WeightEntryForm with validation
│   ├── urls.py        # /weights/ routes
│   └── tests/         # Model, form, view tests
├── users/             # Custom User model with name field
├── templates/
│   ├── pages/home.html           # Main page with form + graph
│   └── weights/partials/         # HTMX partials (form, graph, entries)
└── conftest.py        # Shared pytest fixtures
```

## Key Files

- `weightmelters/weights/models.py` - WeightEntry (user, date, weight) with unique_together constraint
- `weightmelters/weights/views.py` - HTMX endpoints returning partials, triggers graph refresh
- `weightmelters/templates/pages/home.html` - Homepage with HTMX attributes for dynamic updates
- `config/settings/test.py` - Uses SQLite for testing

## URL Routes

- `/` - Homepage (form + graph for authenticated users)
- `/weights/log/` - POST weight entry (HTMX)
- `/weights/graph/` - GET Plotly graph partial
- `/weights/entries/` - GET user's entries list
- `/weights/<pk>/delete/` - DELETE entry (HTMX)

## Code Quality

- **Ruff** - Linting and formatting
- **MyPy** - Type checking with django-stubs
- **djLint** - Template linting
- **Pre-commit** - Runs all checks automatically

## HTMX + JavaScript Libraries

When using JavaScript libraries (like Plotly) in HTMX partials:

- **Load libraries globally** in the parent template (e.g., `home.html`), not in HTMX partials
- When HTMX swaps in HTML containing `<script>` tags, external scripts load asynchronously but inline scripts execute immediately, causing "X is not defined" errors
- For Plotly: use `fig.to_html(full_html=False, include_plotlyjs=False)` since Plotly.js is loaded in `home.html`
- All scripts in templates should use the `defer` attribute to match the pattern in `base.html`

## Git Commits

- Do not include AI model attribution or "Co-Authored-By" lines in commit messages
- Keep commit messages concise and focused on the "why"
