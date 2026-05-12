#!/bin/bash

source durham-risk-aws-env/bin/activate

uvicorn app.main:app --reload
