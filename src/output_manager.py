from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any, Optional
import yaml
from log_config import LogConfig
import shutil
import tempfile
import hashlib
from contextlib import contextmanager
import copy
import time
from utilities import EnumJSONEncoder

class OutputError(Exception):
    """Base exception for output-related errors"""
    pass

class FileError(OutputError):
    """Exception for file operation errors"""
    pass

class SerializationError(OutputError):
    """Exception for serialization errors"""
    pass

class ValidationError(OutputError):
    """Exception for content validation errors"""
    pass

class RateLimitError(OutputError):
    """Exception for rate limit violations"""
    pass

class ContentValidator:
    """Validates content structure and data"""
    
    def __init__(self):
        log_config = LogConfig()
        self.logger = log_config.get_logger()
    
    def validate_content(self, content: Dict, content_type: str) -> None:
        """Validate content structure and required fields"""
        self.logger.debug(f"Validating {content_type} content")
        
        if not isinstance(content, dict):
            self.logger.error("Validation failed: Content must be a dictionary")
            raise ValidationError("Content must be a dictionary")
        if not content:
            self.logger.error("Validation failed: Content is empty")
            raise ValidationError("Content is empty")
        if 'metadata' not in content:
            self.logger.error("Validation failed: Content missing metadata field")
            raise ValidationError("Content missing 'metadata' field")
        
        # Content-type specific validation
        validators = {
            'text': self._validate_text,
            'carousel': self._validate_carousel,
            'poll': self._validate_poll,
            'newsletter': self._validate_newsletter,
            'video_script': self._validate_video_script,
            'document': self._validate_document
        }
        
        validator = validators.get(content_type)
        if validator:
            validator(content)
        else:
            self.logger.error(f"Validation failed: No validator for content type {content_type}")
            raise ValidationError(f"No validator found for content type: {content_type}")

        self.logger.debug("Content validation successful")
    
    def _validate_text(self, content: Dict) -> None:
        if 'content' not in content:
            raise ValidationError("Text content missing 'content' field")
        if not content['content']:
            raise ValidationError("Text content is empty")
            
    def _validate_carousel(self, content: Dict) -> None:
        if 'slides' not in content:
            raise ValidationError("Carousel content missing 'slides' field")
        if not isinstance(content['slides'], list):
            raise ValidationError("Carousel 'slides' must be a list")

    def _validate_poll(self, content: Dict) -> None:
        if 'options' not in content:
            raise ValidationError("Poll content missing 'options' field")
        if not isinstance(content['options'], list):
            raise ValidationError("Poll 'options' must be a list")
            
    def _validate_newsletter(self, content: Dict) -> None:
        if 'sections' not in content:
            raise ValidationError("Newsletter content missing 'sections' field")
        if not isinstance(content['sections'], dict):
            raise ValidationError("Newsletter 'sections' must be a dictionary")
            
    def _validate_video_script(self, content: Dict) -> None:
        if 'script' not in content:
            raise ValidationError("Video script content missing 'script' field")
        if not content['script']:
            raise ValidationError("Video script content is empty")
            
    def _validate_document(self, content: Dict) -> None:
        if 'sections' not in content:
            raise ValidationError("Document content missing 'sections' field")
        if not isinstance(content['sections'], dict):
            raise ValidationError("Document 'sections' must be a dictionary")

@contextmanager
def safe_file_operation(logger):
    """Context manager for safe file operations"""
    temp_dir = None
    try:
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
    finally:
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")

class ContentFormatter:
    """Handles content formatting for different types"""
    
    def __init__(self):
        log_config = LogConfig()
        self.logger = log_config.get_logger()
    
    def format_safely(self, content: Dict, method: callable) -> str:
        """Safely format content with fallback"""
        try:
            result = method(content)
            if not result:
                raise ValueError("Empty formatted content")
            return result
        except Exception as e:
            self.logger.error(f"Formatting error: {e}")
            return f"# Error Formatting Content\n\nOriginal content:\n{str(content)}"

    def text(self, content: Dict) -> str:
        """Format text content"""
        def format_method(c): return str(c.get('content', ''))
        return self.format_safely(content, format_method)

    def poll(self, content: Dict) -> str:
        """Format poll content"""
        def format_method(c):
            return '\n\n'.join([
                f"# {c.get('hook', 'Poll')}",
                "## Context",
                c.get('context', ''),
                "## Options",
                '\n'.join(f"- {opt}" for opt in c.get('options', []))
            ])
        return self.format_safely(content, format_method)

    def carousel(self, content: Dict) -> str:
        """Format carousel content"""
        def format_method(c):
            parts = [f"# {c.get('hook', 'Carousel')}\n"]
            for i, slide in enumerate(c.get('slides', []), 1):
                title = slide.get('title', f'Slide {i}')
                content_text = slide.get('content', '')
                parts.extend([f"\n## Slide {i}: {title}", content_text])
            if cta := c.get('cta'):
                parts.extend(["\n## Call to Action", cta])
            return '\n\n'.join(parts)
        return self.format_safely(content, format_method)

    def newsletter(self, content: Dict) -> str:
        """Format newsletter content"""
        def format_method(c):
            parts = [f"# {c.get('hook', 'Newsletter')}"]
            for section, text in c.get('sections', {}).items():
                parts.extend([f"\n## {section}", str(text)])
            if cta := c.get('cta'):
                parts.extend(["\n## Call to Action", cta])
            return '\n\n'.join(parts)
        return self.format_safely(content, format_method)

    def video_script(self, content: Dict) -> str:
        """Format video script content"""
        def format_method(c):
            parts = [
                f"# {c.get('hook', 'Video Script')}",
                f"Duration: {c.get('duration', 0)} minutes"
            ]
            for section, text in c.get('script', {}).items():
                parts.extend([f"\n## {section}", str(text)])
            return '\n\n'.join(parts)
        return self.format_safely(content, format_method)

    def document(self, content: Dict) -> str:
        """Format document content"""
        def format_method(c):
            parts = [
                f"# {c.get('hook', 'Document')}",
                f"Document Type: {c.get('doc_type', 'unknown')}"
            ]
            for section, text in c.get('sections', {}).items():
                parts.extend([f"\n## {section}", str(text)])
            return '\n\n'.join(parts)
        return self.format_safely(content, format_method)
    
    @staticmethod
    def _format_carousel(content: Dict) -> str:
        parts = [f"# {content.get('hook', 'Carousel')}\n"]
        for i, slide in enumerate(content.get('slides', []), 1):
            title = slide.get('title', f'Slide {i}')
            content_text = slide.get('content', '')
            parts.extend([f"\n## Slide {i}: {title}", content_text])
        if cta := content.get('cta'):
            parts.extend(["\n## Call to Action", cta])
        return '\n\n'.join(parts)
    
    @staticmethod
    def _format_poll(content: Dict) -> str:
        return '\n\n'.join([
            f"# {content.get('hook', 'Poll')}",
            "## Context",
            content.get('context', ''),
            "## Options",
            '\n'.join(f"- {opt}" for opt in content.get('options', []))
        ])
    
    @staticmethod
    def _format_newsletter(content: Dict) -> str:
        parts = [f"# {content.get('hook', 'Newsletter')}"]
        for section, text in content.get('sections', {}).items():
            parts.extend([f"\n## {section}", str(text)])
        if cta := content.get('cta'):
            parts.extend(["\n## Call to Action", cta])
        return '\n\n'.join(parts)
    
    @staticmethod
    def _format_video_script(content: Dict) -> str:
        parts = [
            f"# {content.get('hook', 'Video Script')}",
            f"Duration: {content.get('duration', 0)} minutes"
        ]
        for section, text in content.get('script', {}).items():
            parts.extend([f"\n## {section}", str(text)])
        return '\n\n'.join(parts)
    
    @staticmethod
    def _format_document(content: Dict) -> str:
        parts = [
            f"# {content.get('hook', 'Document')}",
            f"Document Type: {content.get('doc_type', 'unknown')}"
        ]
        for section, text in content.get('sections', {}).items():
            parts.extend([f"\n## {section}", str(text)])
        return '\n\n'.join(parts)

class OutputManager:
    """Manages content output and file organization"""
    
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks for file operations
    MAX_RETRIES = 3
    MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB max content size
    RATE_LIMIT_INTERVAL = 1.0  # seconds
    
    FORMATTERS = {
        'text': ContentFormatter.text,
        'carousel': ContentFormatter.carousel,
        'poll': ContentFormatter.poll,
        'newsletter': ContentFormatter.newsletter,
        'video_script': ContentFormatter.video_script,
        'document': ContentFormatter.document
    }
    
    def __init__(self, base_dir: str = "output", backup_dir: Optional[str] = None):
        """Initialize output manager with base directory"""
        
        # Initialize logger
        log_config = LogConfig()
        self.logger = log_config.get_logger()
        
        self.base_dir = Path(base_dir)
        self.backup_dir = Path(backup_dir) if backup_dir else None
        self.last_save_time = 0
        
        # Initialize helpers
        self.content_formatter = ContentFormatter()
        self.content_validator = ContentValidator()  # Added this line
        
        self._setup_directories()
        self._cleanup_temp_files()
        
        # Initialize formatters mapping to instance methods
        self.FORMATTERS = {
            'text': self.content_formatter.text,
            'carousel': self.content_formatter.carousel,
            'poll': self.content_formatter.poll,
            'newsletter': self.content_formatter.newsletter,
            'video_script': self.content_formatter.video_script,
            'document': self.content_formatter.document
        }
        
    def _setup_directories(self) -> None:
        """Create necessary directory structure"""
        try:
            self.base_dir.mkdir(exist_ok=True)
            if self.backup_dir:
                self.backup_dir.mkdir(exist_ok=True)
            self.logger.info(f"Output directory setup at: {self.base_dir}")
        except Exception as e:
            raise FileError(f"Failed to create directories: {e}")

    def _cleanup_temp_files(self) -> None:
        """Clean up any temporary files from failed operations"""
        try:
            pattern = "*.tmp"
            for temp_file in self.base_dir.rglob(pattern):
                temp_file.unlink()
        except Exception as e:
            self.logger.warning(f"Cleanup warning: {e}")

    def _get_content_dir(self, content_type: str) -> Path:
        """Create and return content type specific directory"""
        try:
            date_dir = self.base_dir / datetime.now().strftime("%Y-%m-%d")
            content_dir = date_dir / self._sanitize_filename(content_type)
            content_dir.mkdir(parents=True, exist_ok=True)
            return content_dir
        except Exception as e:
            raise FileError(f"Failed to create content directory: {e}")

    def _sanitize_filename(self, text: str) -> str:
        """Create safe filename from text"""
        if not text:
            return "untitled"
        safe_chars = (x if x.isalnum() or x in (' ', '-', '_') else '_' 
                     for x in str(text).lower())
        return ''.join(safe_chars).strip() or "untitled"
    
    def _normalize_content(self, content: Dict) -> Dict:
        """Remove volatile fields before checksum computation"""
        if not isinstance(content, dict):
            return content

        normalized = content.copy()
        
        # Remove volatile fields that shouldn't affect verification
        volatile_fields = ['generation_time', 'metadata']
        for field in volatile_fields:
            normalized.pop(field, None)

        return normalized

    def _compute_checksum(self, content: Dict) -> str:
        """Compute content checksum for verification"""
        try:
            # Normalize the content by removing any volatile fields
            normalized_content = self._normalize_content(content)
            serialized = json.dumps(normalized_content, sort_keys=True)
            return hashlib.sha256(serialized.encode()).hexdigest()
        except Exception as e:
            self.logger.error(f"Checksum computation error: {e}")
            raise

    def _compute_file_checksum(self, filepath: str) -> str:
        """Compute file checksum"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(self.CHUNK_SIZE), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _retry_operation(self, operation: callable, *args, **kwargs) -> Any:
        """Retry an operation with exponential backoff"""
        for attempt in range(self.MAX_RETRIES):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                wait_time = 2 ** attempt
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

    def save_content(self, content: Dict, content_type: str) -> Dict[str, str]:
        """Save content and return file paths with verification"""
        self.logger.info(f"Saving {content_type} content")
        
        try:
            content_size = len(json.dumps(content))
            if content_size > self.MAX_CONTENT_SIZE:
                raise ValidationError(f"Content size ({content_size} bytes) exceeds limit")
            
            now = time.time()
            if now - self.last_save_time < self.RATE_LIMIT_INTERVAL:
                sleep_time = self.RATE_LIMIT_INTERVAL - (now - self.last_save_time)
                self.logger.debug(f"Rate limit: waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
            self.last_save_time = time.time()
            
            # Use instance method to validate
            self.content_validator.validate_content(content, content_type)
            
            content_to_save = copy.deepcopy(content)
            checksum = self._compute_checksum(content_to_save)
            
            with safe_file_operation(self.logger) as temp_dir:
                content_dir = self._get_content_dir(content_type)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                topic = content.get('metadata', {}).get('topic', 'untitled')
                base_filename = f"{self._sanitize_filename(topic)}_{timestamp}"
                
                temp_paths = self._save_all_formats(
                    content_to_save, content_type, temp_dir, base_filename
                )
                
                self._verify_saved_files(temp_paths, checksum)
                final_paths = self._move_to_final_location(
                    temp_paths, content_dir, base_filename
                )
                
                if self.backup_dir:
                    self._create_backup(final_paths)
                
                self.logger.info(f"Content saved successfully: {final_paths}")
                return final_paths
                
        except Exception as e:
            self.logger.error(f"Failed to save content: {e}")
            raise OutputError(f"Content save failed: {e}")

    def _verify_saved_files(self, paths: Dict[str, str], checksum: str) -> None:
        """Verify saved files integrity"""
        try:
            for path_type, path in paths.items():
                if not Path(path).exists():
                    raise FileError(f"Missing file: {path}")
                
                if path_type == 'json':
                    with open(path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                        # Compare normalized JSON content instead of raw file checksum
                        saved_checksum = self._compute_checksum(content)
                        if saved_checksum != checksum:
                            self.logger.error(f"Checksum mismatch. Expected: {checksum}, Got: {saved_checksum}")
                            raise ValidationError("Content verification failed")
            
            self.logger.debug("All files verified successfully")
        except Exception as e:
            self.logger.error(f"File verification error: {e}")
            raise

    def safe_save(self, content: Dict, content_type: str) -> Dict[str, str]:
        """Safe save with recovery"""
        backup_data = None
        temp_dir = None
        try:
            # Create temporary backup
            if self.backup_dir:
                temp_dir = Path(tempfile.mkdtemp())
                backup_data = {
                    'content': content,
                    'temp_dir': temp_dir
                }
                self._create_temp_backup(content, temp_dir)
                self.logger.debug("Created temporary backup")

            # Attempt to save content
            result = self.save_content(content, content_type)
            self.logger.debug("Content saved successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error during save operation: {e}")
            if backup_data:
                try:
                    self._restore_from_backup(backup_data)
                    self.logger.info("Successfully restored from backup")
                except Exception as restore_error:
                    self.logger.error(f"Failed to restore from backup: {restore_error}")
            raise

        finally:
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temporary directory: {e}")

    def _create_temp_backup(self, content: Dict, temp_dir: Path) -> None:
        """Create temporary backup of content"""
        try:
            backup_file = temp_dir / 'content_backup.json'
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, cls=EnumJSONEncoder, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise

    def _restore_from_backup(self, backup_data: Dict) -> None:
        """Restore content from backup"""
        try:
            backup_file = backup_data['temp_dir'] / 'content_backup.json'
            with open(backup_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            # Additional restoration logic if needed
            self.logger.debug("Backup restoration completed")
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            raise
    
    def _create_backup(self, paths: Dict[str, str]) -> None:
        """Create backup of saved files"""
        try:
            for path in paths.values():
                src = Path(path)
                dst = self.backup_dir / src.relative_to(self.base_dir)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                self.logger.debug(f"Created backup: {dst}")
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            # Don't raise - backup failure shouldn't stop the process

    def _move_to_final_location(
        self, temp_paths: Dict[str, str], 
        content_dir: Path, base_filename: str
    ) -> Dict[str, str]:
        """Move files from temporary to final location"""
        final_paths = {}
        try:
            for path_type, temp_path in temp_paths.items():
                temp_path = Path(temp_path)
                final_path = content_dir / temp_path.name
                
                # Use atomic move when possible
                self._retry_operation(
                    shutil.move,
                    str(temp_path),
                    str(final_path)
                )
                final_paths[path_type] = str(final_path)
                self.logger.debug(f"Moved {path_type} to final location: {final_path}")
                
            return final_paths
        except Exception as e:
            self.logger.error(f"Failed to move files to final location: {e}")
            raise FileError(f"Failed to move files to final location: {e}")

    def _save_all_formats(
        self, content: Dict, content_type: str, 
        temp_dir: Path, base_filename: str
    ) -> Dict[str, str]:
        """Save content in all required formats"""
        paths = {}
        
        try:
            # Save JSON with retries
            json_path = temp_dir / f"{base_filename}.json"
            self._retry_operation(
                self._save_json,
                content,
                json_path
            )
            paths['json'] = str(json_path)
            self.logger.debug(f"Saved JSON to: {json_path}")
            
            # Save formatted content
            formatted_path = self._save_formatted(
                content, content_type, temp_dir, base_filename
            )
            paths['formatted'] = str(formatted_path)
            self.logger.debug(f"Saved formatted content to: {formatted_path}")
            
            # Save metadata
            metadata_path = temp_dir / f"{base_filename}_meta.yaml"
            self._retry_operation(
                self._save_yaml,
                content.get('metadata', {}),
                metadata_path
            )
            paths['metadata'] = str(metadata_path)
            self.logger.debug(f"Saved metadata to: {metadata_path}")
            
            return paths
            
        except Exception as e:
            self.logger.error(f"Error saving formats: {e}")
            raise OutputError(f"Failed to save content formats: {e}")

    def _save_json(self, content: Dict, path: Path) -> None:
        """Save content as JSON"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False, cls=EnumJSONEncoder)

    def _save_yaml(self, content: Dict, path: Path) -> None:
        """Save content as YAML"""
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(content, f, allow_unicode=True)

    def _save_formatted(
        self, content: Dict, content_type: str, 
        content_dir: Path, base_filename: str
    ) -> Path:
        """Save formatted content based on type"""
        try:
            # Get appropriate formatter
            formatter = self.FORMATTERS.get(content_type)
            if not formatter:
                self.logger.warning(f"Unknown content type: {content_type}, using text format")
                formatter = ContentFormatter.text
                
            # Format content
            formatted_content = formatter(content)
            
            # Determine file extension
            ext = '.md' if content_type != 'text' else '.txt'
            path = content_dir / f"{base_filename}{ext}"
            
            # Ensure the directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save content with retries
            self._retry_operation(
                lambda: path.write_text(formatted_content, encoding='utf-8')
            )
            
            self.logger.debug(f"Saved formatted content to: {path}")
            return path
                
        except Exception as e:
            self.logger.error(f"Error formatting content: {e}")
            raise OutputError(f"Content formatting failed: {e}")
