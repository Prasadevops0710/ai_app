let currentTool = null;
let selectedFile = null;

// Tool selection
function selectTool(tool) {
    currentTool = tool;
    
    // Update UI
    document.getElementById('upload-section').style.display = 'block';
    document.querySelector('.tools-grid').style.display = 'none';
    document.querySelector('.hero').style.display = 'none';
    
    // Update title and file input accept
    const fileInput = document.getElementById('fileInput');
    const uploadTitle = document.getElementById('upload-title');
    const fileInfo = document.getElementById('fileInfo');
    
    if (tool === 'pdf-to-excel') {
        uploadTitle.textContent = 'PDF to Excel';
        fileInput.accept = '.pdf';
        fileInfo.textContent = 'Supported format: PDF';
    } else {
        uploadTitle.textContent = 'Excel to PDF';
        fileInput.accept = '.xlsx,.xls';
        fileInfo.textContent = 'Supported formats: XLSX, XLS';
    }
    
    // Reset upload state
    resetUpload();
}

// Reset to home
function resetTool() {
    currentTool = null;
    selectedFile = null;
    
    document.getElementById('upload-section').style.display = 'none';
    document.querySelector('.tools-grid').style.display = 'grid';
    document.querySelector('.hero').style.display = 'block';
    
    resetUpload();
}

// Reset upload area
function resetUpload() {
    selectedFile = null;
    document.getElementById('dropZone').style.display = 'block';
    document.getElementById('filePreview').style.display = 'none';
    document.getElementById('progressContainer').style.display = 'none';
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('errorContainer').style.display = 'none';
    document.getElementById('fileInput').value = '';
}

// Drag and drop functionality
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

// Handle file selection
function handleFileSelect(file) {
    // Validate file type
    const validTypes = currentTool === 'pdf-to-excel' 
        ? ['application/pdf']
        : ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'];
    
    if (!validTypes.includes(file.type) && !isValidExtension(file.name)) {
        alert('Please select a valid file type');
        return;
    }
    
    selectedFile = file;
    displayFilePreview(file);
}

function isValidExtension(filename) {
    const ext = filename.toLowerCase().split('.').pop();
    if (currentTool === 'pdf-to-excel') {
        return ext === 'pdf';
    } else {
        return ext === 'xlsx' || ext === 'xls';
    }
}

// Display file preview
function displayFilePreview(file) {
    document.getElementById('dropZone').style.display = 'none';
    document.getElementById('filePreview').style.display = 'block';
    
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
}

// Remove file
function removeFile() {
    selectedFile = null;
    resetUpload();
}

// Convert file
async function convertFile() {
    if (!selectedFile) return;
    
    // Show progress
    document.getElementById('filePreview').style.display = 'none';
    document.getElementById('progressContainer').style.display = 'block';
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    const endpoint = currentTool === 'pdf-to-excel' 
        ? '/pdf-to-excel'
        : '/excel-to-pdf';
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Conversion failed');
        }
        
        // Get the blob
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const outputFileName = getOutputFileName(selectedFile.name);
        
        // Show success
        document.getElementById('progressContainer').style.display = 'none';
        document.getElementById('resultContainer').style.display = 'block';
        
        const downloadLink = document.getElementById('downloadLink');
        downloadLink.href = url;
        downloadLink.download = outputFileName;
        
    } catch (error) {
        console.error('Conversion error:', error);
        
        // Show error
        document.getElementById('progressContainer').style.display = 'none';
        document.getElementById('errorContainer').style.display = 'block';
        document.getElementById('errorMessage').textContent = error.message || 'Something went wrong. Please try again.';
    }
}

// Get output file name
function getOutputFileName(inputFileName) {
    const nameWithoutExt = inputFileName.substring(0, inputFileName.lastIndexOf('.'));
    const newExt = currentTool === 'pdf-to-excel' ? '.xlsx' : '.pdf';
    return nameWithoutExt + newExt;
}

// Convert another file
function convertAnother() {
    resetUpload();
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && currentTool) {
        if (document.getElementById('resultContainer').style.display === 'block' ||
            document.getElementById('errorContainer').style.display === 'block') {
            resetUpload();
        } else {
            resetTool();
        }
    }
});
