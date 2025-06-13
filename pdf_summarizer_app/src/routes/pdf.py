import os
import tempfile
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from src.models.pdf_summary import PDFSummary, db
from src.services.google_drive import GoogleDriveService
from src.services.pdf_processor import PDFProcessor
from datetime import datetime

pdf_bp = Blueprint('pdf', __name__)

@pdf_bp.route('/summaries', methods=['GET'])
@login_required
def get_summaries():
    summaries = PDFSummary.query.filter_by(user_id=current_user.id).order_by(PDFSummary.date_added.desc()).all()
    return jsonify([summary.to_dict() for summary in summaries])

@pdf_bp.route('/summaries/<int:summary_id>', methods=['GET'])
@login_required
def get_summary(summary_id):
    summary = PDFSummary.query.filter_by(id=summary_id, user_id=current_user.id).first_or_404()
    return jsonify(summary.to_dict())

@pdf_bp.route('/summaries/<int:summary_id>', methods=['DELETE'])
@login_required
def delete_summary(summary_id):
    summary = PDFSummary.query.filter_by(id=summary_id, user_id=current_user.id).first_or_404()
    db.session.delete(summary)
    db.session.commit()
    return '', 204

@pdf_bp.route('/scan-drive', methods=['POST'])
@login_required
def scan_google_drive():
    """Scan Google Drive for new PDF files and process them."""
    try:
        # Initialize services
        drive_service = GoogleDriveService()
        pdf_processor = PDFProcessor()
        
        # Get user's Google Drive folder ID (if specified)
        folder_id = current_user.google_drive_folder_id
        
        # List new PDF files from the last week
        files = drive_service.list_files(folder_id=folder_id, days_back=7)
        
        processed_files = []
        errors = []
        
        for file in files:
            try:
                # Check if we've already processed this file
                existing_summary = PDFSummary.query.filter_by(
                    user_id=current_user.id,
                    google_drive_link=file['webViewLink']
                ).first()
                
                if existing_summary:
                    continue  # Skip already processed files
                
                # Download the file to a temporary location
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                if drive_service.download_file(file['id'], temp_path):
                    # Process the PDF
                    result = pdf_processor.process_pdf(temp_path, file['name'])
                    
                    # Create summary record
                    summary = PDFSummary(
                        user_id=current_user.id,
                        title=result['title'],
                        file_path=file['name'],
                        google_drive_link=file['webViewLink'],
                        summary=result['summary'],
                        key_messages='\n'.join(result['key_messages']) if result['key_messages'] else '',
                        date_added=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')),
                        date_processed=datetime.utcnow()
                    )
                    
                    db.session.add(summary)
                    processed_files.append(result['title'])
                
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
            except Exception as e:
                errors.append(f"Error processing {file['name']}: {str(e)}")
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'message': f'Processed {len(processed_files)} new files',
            'processed_files': processed_files,
            'errors': errors
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to scan Google Drive: {str(e)}'}), 500

@pdf_bp.route('/upload', methods=['POST'])
@login_required
def upload_pdf():
    """Upload a PDF file to Google Drive and process it."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Initialize services
            drive_service = GoogleDriveService()
            pdf_processor = PDFProcessor()
            
            # Upload to Google Drive
            folder_id = current_user.google_drive_folder_id
            uploaded_file = drive_service.upload_file(temp_path, file.filename, folder_id)
            
            if not uploaded_file:
                return jsonify({'error': 'Failed to upload file to Google Drive'}), 500
            
            # Process the PDF
            result = pdf_processor.process_pdf(temp_path, file.filename)
            
            # Create summary record
            summary = PDFSummary(
                user_id=current_user.id,
                title=result['title'],
                file_path=file.filename,
                google_drive_link=uploaded_file['webViewLink'],
                summary=result['summary'],
                key_messages='\n'.join(result['key_messages']) if result['key_messages'] else '',
                date_added=datetime.utcnow(),
                date_processed=datetime.utcnow()
            )
            
            db.session.add(summary)
            db.session.commit()
            
            return jsonify({
                'message': 'File uploaded and processed successfully',
                'summary': summary.to_dict()
            }), 201
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        return jsonify({'error': f'Failed to upload and process file: {str(e)}'}), 500

