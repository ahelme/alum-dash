import pandas as pd
import asyncio
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from database.connection import Alumni, ImportLog, DegreeProgram, AsyncSessionLocal
import logging
import json
from io import StringIO

logger = logging.getLogger(__name__)

class CSVImportService:
    """Service for handling CSV imports of alumni data"""
    
    @staticmethod
    def validate_csv_format(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate CSV format and return validation results
        
        Expected columns:
        - name (required): Full name of alumni
        - graduation_year (required): Year of graduation (1970-2030)
        - degree_program (required): One of the valid degree programs
        - email (optional): Email address
        - linkedin_url (optional): LinkedIn profile URL
        - imdb_url (optional): IMDb profile URL
        - website (optional): Personal website URL
        """
        
        required_columns = ['name', 'graduation_year', 'degree_program']
        optional_columns = ['email', 'linkedin_url', 'imdb_url', 'website']
        all_valid_columns = required_columns + optional_columns
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'summary': {
                'total_rows': len(df),
                'valid_rows': 0,
                'invalid_rows': 0
            }
        }
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
            return validation_result
        
        # Check for unexpected columns
        unexpected_columns = [col for col in df.columns if col not in all_valid_columns]
        if unexpected_columns:
            validation_result['warnings'].append(f"Unexpected columns will be ignored: {', '.join(unexpected_columns)}")
        
        # Validate data in each row
        valid_degree_programs = [dp.value for dp in DegreeProgram]
        
        for index, row in df.iterrows():
            row_errors = []
            
            # Validate name
            if pd.isna(row['name']) or str(row['name']).strip() == '':
                row_errors.append(f"Row {index + 2}: Name is required")
            elif len(str(row['name'])) > 100:
                row_errors.append(f"Row {index + 2}: Name too long (max 100 characters)")
            
            # Validate graduation year
            try:
                year = int(row['graduation_year'])
                if year < 1970 or year > 2030:
                    row_errors.append(f"Row {index + 2}: Graduation year must be between 1970 and 2030")
            except (ValueError, TypeError):
                row_errors.append(f"Row {index + 2}: Invalid graduation year")
            
            # Validate degree program
            if str(row['degree_program']) not in valid_degree_programs:
                row_errors.append(f"Row {index + 2}: Invalid degree program. Must be one of: {', '.join(valid_degree_programs)}")
            
            # Validate email format (if provided)
            if not pd.isna(row.get('email', '')) and str(row.get('email', '')).strip():
                email = str(row['email']).strip()
                if '@' not in email or '.' not in email.split('@')[-1]:
                    row_errors.append(f"Row {index + 2}: Invalid email format")
            
            # Validate URLs (if provided)
            for url_field in ['linkedin_url', 'imdb_url', 'website']:
                if not pd.isna(row.get(url_field, '')) and str(row.get(url_field, '')).strip():
                    url = str(row[url_field]).strip()
                    if not (url.startswith('http://') or url.startswith('https://')):
                        row_errors.append(f"Row {index + 2}: {url_field} must start with http:// or https://")
            
            if row_errors:
                validation_result['errors'].extend(row_errors)
                validation_result['summary']['invalid_rows'] += 1
            else:
                validation_result['summary']['valid_rows'] += 1
        
        if validation_result['errors']:
            validation_result['valid'] = False
        
        return validation_result
    
    @staticmethod
    async def import_alumni_csv(
        session: AsyncSession,
        csv_content: str,
        filename: str,
        imported_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Import alumni data from CSV content
        
        Returns import result with statistics and any errors
        """
        
        # Create import log entry
        import_log = ImportLog(
            filename=filename,
            import_type="alumni_csv",
            status="processing",
            imported_by=imported_by
        )
        session.add(import_log)
        await session.flush()  # Get the ID
        
        try:
            # Parse CSV
            df = pd.read_csv(StringIO(csv_content))
            df = df.fillna('')  # Replace NaN with empty strings
            
            # Validate format
            validation_result = CSVImportService.validate_csv_format(df)
            
            if not validation_result['valid']:
                # Update import log with validation errors
                import_log.status = "failed"
                import_log.error_details = {"validation_errors": validation_result['errors']}
                import_log.completed_at = datetime.utcnow()
                await session.commit()
                
                return {
                    'success': False,
                    'message': 'CSV validation failed',
                    'validation_result': validation_result,
                    'import_log_id': import_log.id
                }
            
            # Process valid rows
            successful_imports = 0
            failed_imports = 0
            import_errors = []
            
            for index, row in df.iterrows():
                try:
                    # Use a fresh session for each row to avoid rollback issues
                    async with AsyncSessionLocal() as row_session:
                        # Prepare alumni data
                        alumni_data = {
                            'name': str(row['name']).strip(),
                            'graduation_year': int(row['graduation_year']),
                            'degree_program': str(row['degree_program']).strip(),
                            'email': str(row.get('email', '')).strip() if row.get('email', '') else None,
                            'linkedin_url': str(row.get('linkedin_url', '')).strip() if row.get('linkedin_url', '') else None,
                            'imdb_url': str(row.get('imdb_url', '')).strip() if row.get('imdb_url', '') else None,
                            'website': str(row.get('website', '')).strip() if row.get('website', '') else None,
                        }
                        
                        # Remove empty string values
                        alumni_data = {k: v for k, v in alumni_data.items() if v is not None and v != ''}
                        
                        # Check if alumni already exists (by name and graduation year)
                        existing_query = select(Alumni).where(
                            Alumni.name == alumni_data['name'],
                            Alumni.graduation_year == alumni_data['graduation_year']
                        )
                        existing_alumni = await row_session.execute(existing_query)
                        existing_alumni = existing_alumni.scalar_one_or_none()
                        
                        if existing_alumni:
                            import_errors.append(f"Row {index + 2}: Alumni '{alumni_data['name']}' (graduation year {alumni_data['graduation_year']}) already exists")
                            failed_imports += 1
                            continue
                        
                        # Convert degree_program string to enum
                        degree_program_enum = None
                        for dp in DegreeProgram:
                            if dp.value == alumni_data['degree_program']:
                                degree_program_enum = dp
                                break
                        
                        if degree_program_enum is None:
                            raise ValueError(f"Invalid degree program: {alumni_data['degree_program']}")
                        
                        # Create new alumni record
                        new_alumni = Alumni(
                            name=alumni_data['name'],
                            graduation_year=alumni_data['graduation_year'],
                            degree_program=degree_program_enum,
                            email=alumni_data.get('email'),
                            linkedin_url=alumni_data.get('linkedin_url'),
                            imdb_url=alumni_data.get('imdb_url'),
                            website=alumni_data.get('website')
                        )
                        
                        row_session.add(new_alumni)
                        await row_session.commit()
                        successful_imports += 1
                        
                except Exception as e:
                    import_errors.append(f"Row {index + 2}: {str(e)}")
                    failed_imports += 1
                    logger.error(f"Error importing row {index + 2}: {str(e)}")
            
            # Update import log
            import_log.status = "completed" if failed_imports == 0 else "partial"
            import_log.total_records = len(df)
            import_log.successful_records = successful_imports
            import_log.failed_records = failed_imports
            import_log.error_details = {"import_errors": import_errors} if import_errors else None
            import_log.completed_at = datetime.utcnow()
            
            await session.commit()
            
            return {
                'success': True,
                'message': f'Import completed: {successful_imports} successful, {failed_imports} failed',
                'statistics': {
                    'total_records': len(df),
                    'successful_imports': successful_imports,
                    'failed_imports': failed_imports,
                    'validation_warnings': validation_result.get('warnings', [])
                },
                'errors': import_errors,
                'import_log_id': import_log.id
            }
            
        except Exception as e:
            # Update import log with error
            import_log.status = "failed"
            import_log.error_details = {"system_error": str(e)}
            import_log.completed_at = datetime.utcnow()
            await session.commit()
            
            logger.error(f"CSV import failed: {str(e)}")
            return {
                'success': False,
                'message': f'Import failed: {str(e)}',
                'import_log_id': import_log.id
            }
    
    @staticmethod
    def generate_csv_template() -> str:
        """Generate a CSV template with sample data for alumni import"""
        
        template_data = [
            {
                'name': 'John Smith',
                'graduation_year': 2020,
                'degree_program': 'Film Production',
                'email': 'john.smith@example.com',
                'linkedin_url': 'https://linkedin.com/in/johnsmith',
                'imdb_url': 'https://www.imdb.com/name/nm1234567',
                'website': 'https://johnsmithfilms.com'
            },
            {
                'name': 'Jane Doe',
                'graduation_year': 2021,
                'degree_program': 'Documentary',
                'email': 'jane.doe@example.com',
                'linkedin_url': '',
                'imdb_url': '',
                'website': ''
            }
        ]
        
        df = pd.DataFrame(template_data)
        return df.to_csv(index=False)
    
    @staticmethod
    async def get_import_history(session: AsyncSession, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history of CSV imports"""
        
        query = select(ImportLog).order_by(ImportLog.created_at.desc()).limit(limit)
        result = await session.execute(query)
        import_logs = result.scalars().all()
        
        return [
            {
                'id': log.id,
                'filename': log.filename,
                'import_type': log.import_type,
                'status': log.status,
                'total_records': log.total_records,
                'successful_records': log.successful_records,
                'failed_records': log.failed_records,
                'imported_by': log.imported_by,
                'created_at': log.created_at.isoformat() if log.created_at else None,
                'completed_at': log.completed_at.isoformat() if log.completed_at else None
            }
            for log in import_logs
        ]
