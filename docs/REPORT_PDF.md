# Convert the project report to PDF

From the project root, install Pandoc and a supported PDF engine such as XeLaTeX, then run:

```bash
pandoc docs/PROJECT_REPORT.md -o outputs/PROJECT_REPORT.pdf --toc --number-sections --pdf-engine=xelatex
```

If you do not have Pandoc/LaTeX, open `docs/PROJECT_REPORT.md` in VS Code or a Markdown editor with PDF export, or use a browser-based Markdown preview and print to PDF. Review page breaks, title-page placeholders, Mermaid diagram rendering, and references before submission. The PDF is not generated automatically by the source project.
