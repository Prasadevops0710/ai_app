from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import tempfile
import shutil
from pathlib import Path
import tabula
import pandas as pd
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import PyPDF2
import pdfplumber

app = FastAPI(
    title="PDF ↔ Excel Converter API",
    description="Convert PDF files to Excel and Excel files to PDF",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create temporary directory for file processing
TEMP_DIR = Path("/tmp/conversions")
TEMP_DIR.mkdir(exist_ok=True)


@app.get("/")
async def home(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "PDF ↔ Excel Converter API",
        "endpoints": {
            "/pdf-to-excel": "POST - Convert PDF to Excel",
            "/excel-to-pdf": "POST - Convert Excel to PDF",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pdf-excel-converter"}


@app.post("/pdf-to-excel")
async def pdf_to_excel(file: UploadFile = File(...)):
    """
    Convert PDF file to Excel format
    
    Args:
        file: PDF file to convert
        
    Returns:
        Excel file
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create temporary files
    temp_pdf = TEMP_DIR / f"input_{file.filename}"
    temp_excel = TEMP_DIR / f"output_{file.filename.rsplit('.', 1)[0]}.xlsx"
    
    try:
        # Save uploaded PDF
        with open(temp_pdf, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # First, try to extract tables using tabula
        tables = None
        try:
            tables = tabula.read_pdf(
                str(temp_pdf), 
                pages='all', 
                multiple_tables=True,
                silent=True
            )
            # Filter out empty tables
            if tables:
                tables = [t for t in tables if not t.empty]
        except Exception:
            pass
        
        # If tabula found tables, use them
        if tables and len(tables) > 0:
            with pd.ExcelWriter(temp_excel, engine='openpyxl') as writer:
                for i, table in enumerate(tables):
                    sheet_name = f"Table_{i+1}" if len(tables) > 1 else "Sheet1"
                    table.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # Otherwise, extract text content using pdfplumber
            try:
                with pdfplumber.open(temp_pdf) as pdf:
                    all_data = []
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        # Try to extract table first
                        page_tables = page.extract_tables()
                        
                        if page_tables:
                            # If tables found on this page, add them
                            for table in page_tables:
                                if table:
                                    # Clean up table data
                                    cleaned_table = [[cell if cell else '' for cell in row] for row in table]
                                    df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0] if cleaned_table else None)
                                    all_data.append(('Table', df))
                        else:
                            # Otherwise extract text content
                            text = page.extract_text()
                            if text:
                                lines = [line.strip() for line in text.split('\n') if line.strip()]
                                if lines:
                                    df = pd.DataFrame({'Content': lines})
                                    all_data.append((f'Page_{page_num}', df))
                    
                    if not all_data:
                        raise HTTPException(
                            status_code=400, 
                            detail="No content found in PDF. The PDF might be empty or contain only images."
                        )
                    
                    # Write all data to Excel
                    with pd.ExcelWriter(temp_excel, engine='openpyxl') as writer:
                        for i, (name, df) in enumerate(all_data):
                            sheet_name = name if len(all_data) == 1 else f"{name}_{i+1}"
                            # Limit sheet name to 31 characters (Excel limitation)
                            sheet_name = sheet_name[:31]
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                            
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error extracting PDF content: {str(e)}"
                )
        
        # Return the Excel file
        return FileResponse(
            path=temp_excel,
            filename=f"{file.filename.rsplit('.', 1)[0]}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Cleanup
        if temp_pdf.exists():
            temp_pdf.unlink()
        # Keep temp_excel for download, will be cleaned up later


@app.post("/excel-to-pdf")
async def excel_to_pdf(file: UploadFile = File(...)):
    """
    Convert Excel file to PDF format
    
    Args:
        file: Excel file to convert
        
    Returns:
        PDF file
    """
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
    
    # Create temporary files
    temp_excel = TEMP_DIR / f"input_{file.filename}"
    temp_pdf = TEMP_DIR / f"output_{file.filename.rsplit('.', 1)[0]}.pdf"
    
    try:
        # Save uploaded Excel
        with open(temp_excel, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Read Excel file
        try:
            df = pd.read_excel(temp_excel, sheet_name=0)
            
            # Convert DataFrame to PDF
            pdf_doc = SimpleDocTemplate(str(temp_pdf), pagesize=letter)
            
            # Prepare data for table
            data = [df.columns.tolist()] + df.values.tolist()
            
            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            # Build PDF
            pdf_doc.build([table])
            
            # Return the PDF file
            return FileResponse(
                path=temp_pdf,
                filename=f"{file.filename.rsplit('.', 1)[0]}.pdf",
                media_type="application/pdf"
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error converting Excel: {str(e)}")
            
    finally:
        # Cleanup
        if temp_excel.exists():
            temp_excel.unlink()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
