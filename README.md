# Time Tracker CLI

Simple CLI time tracking tool for freelancers.

## Problem
Losing billable hours due to forgetting to track time.

## Solution
Minimal CLI: `track start/stop/status/report`

## Installation
```bash
pip install -r requirements.txt
pip install -e .
```

## Usage
```bash
track start "coding homework"
track status
track stop
track report
```

## Development
```bash
pytest tests/ -v --cov=src
```