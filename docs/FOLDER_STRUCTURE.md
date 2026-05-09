# Folder Structure

```text
Stock-Market-Data-Analyzer/
|-- backend/             Backend application files
|   |-- api/             FastAPI backend endpoints
|   |-- db/              SQLite database files
|   |-- src/             Core Python modules
|   |-- main.py          CLI analysis/report runner
|   `-- requirements.txt Python dependencies
|-- frontend/            Frontend dashboard files
|   |-- streamlit/       Streamlit dashboard
|   `-- nextjs/          Optional Next.js dashboard scaffold
|-- docs/                Project guides and interview notes
|-- images/              Generated charts and dashboard screenshots
|-- logs/                Runtime logs, ignored by Git
|-- outputs/             Generated CSV analysis outputs
|-- reports/             Generated Markdown reports
|-- README.md            Main GitHub documentation
`-- .gitignore           Files excluded from Git
```

## What To Commit

- Source code in `backend/` and `frontend/`
- Documentation in `README.md` and `docs/`
- Selected sample outputs, screenshots, and reports for proof of work

## What Not To Commit

- `__pycache__/`
- `.pyc` files
- `venv/` or `.venv/`
- `.env`
- runtime `logs/`
- `node_modules/`
- local database files if they become large or private
