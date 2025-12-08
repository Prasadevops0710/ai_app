# PDF ↔ Excel Converter API

A FastAPI application that converts PDF files to Excel and Excel files to PDF, containerized with Docker.

## Features

- **PDF to Excel**: Extract tables from PDF files and convert to Excel format
- **Excel to PDF**: Convert Excel spreadsheets to PDF documents
- **Dockerized**: Easy deployment with Docker and Docker Compose
- **REST API**: Simple HTTP endpoints for file conversion

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Using Docker

```bash
# Build the image
docker build -t pdf-excel-converter .

# Run the container
docker run -d -p 8000:8000 --name pdf-excel-converter pdf-excel-converter
```

## API Endpoints

### Root Endpoint
- **GET** `/` - API information and available endpoints

### Health Check
- **GET** `/health` - Check if the service is running

### Convert PDF to Excel
- **POST** `/pdf-to-excel`
- Upload a PDF file and receive an Excel file
- Content-Type: `multipart/form-data`

Example using curl:
```bash
curl -X POST "http://localhost:8000/pdf-to-excel" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-file.pdf" \
  --output converted.xlsx
```

### Convert Excel to PDF
- **POST** `/excel-to-pdf`
- Upload an Excel file and receive a PDF file
- Content-Type: `multipart/form-data`

Example using curl:
```bash
curl -X POST "http://localhost:8000/excel-to-pdf" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-file.xlsx" \
  --output converted.pdf
```

## API Documentation

Once the service is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Technical Stack

- **FastAPI**: Modern Python web framework
- **tabula-py**: PDF table extraction
- **pandas**: Data manipulation
- **openpyxl**: Excel file handling
- **reportlab**: PDF generation
- **Docker**: Containerization

## Requirements

- Docker and Docker Compose
- Or Python 3.11+ with Java (for tabula-py)

## Development

To run locally without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

The API will be available at `http://localhost:8000`

## Notes

- PDF to Excel conversion works best with PDFs containing tables
- Large files may take longer to process
- Temporary files are automatically cleaned up after conversion
