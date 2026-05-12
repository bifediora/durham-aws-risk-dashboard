#!/bin/bash

source durham-risk-aws-env/bin/activate

uvicorn app.main:app --host 0.0.0.0 --port 8000
