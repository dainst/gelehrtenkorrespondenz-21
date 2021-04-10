FROM python:3

WORKDIR /app
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

ENV PATH="$PATH:/home/app/.local/bin"
COPY --chown=app requirements.txt .
RUN pip install -r requirements.txt \
    && python -c "import nltk; nltk.download('punkt')"

COPY --chown=app . .
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--notebook-dir=src"]
