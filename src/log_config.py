from pathlib import Path
import sys
from loguru import logger
from datetime import datetime

class LogConfig:
    """Manages logging configuration and setup"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self._setup_log_directory()
        
    def _setup_log_directory(self):
        """Create log directory structure"""
        # Create main log directory
        self.log_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different log types
        (self.log_dir / "info").mkdir(exist_ok=True)
        (self.log_dir / "error").mkdir(exist_ok=True)
        (self.log_dir / "debug").mkdir(exist_ok=True)
        
    def setup_logger(self):
        """Configure logging settings"""
        # Remove default logger
        logger.remove()
        
        # Get current date for log files
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Add INFO level logger
        logger.add(
            self.log_dir / "info" / f"info_{current_date}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO",
            rotation="1 day",
            retention="30 days",
            filter=lambda record: record["level"].name == "INFO"
        )
        
        # Add ERROR level logger with traceback
        logger.add(
            self.log_dir / "error" / f"error_{current_date}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}\n{exception}",
            level="ERROR",
            rotation="1 day",
            retention="30 days",
            backtrace=True,
            diagnose=True,
            filter=lambda record: record["level"].name == "ERROR"
        )
        
        # Add DEBUG level logger
        logger.add(
            self.log_dir / "debug" / f"debug_{current_date}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {function}:{line} | {message}",
            level="DEBUG",
            rotation="1 day",
            retention="15 days",
            filter=lambda record: record["level"].name == "DEBUG"
        )
        
        # Add console logger for development (can be disabled in production)
        if "pytest" not in sys.modules:  # Don't show logs during tests
            logger.add(
                sys.stderr,
                format="<level>{level: <8}</level> | {message}",
                level="INFO",
                colorize=True,
                filter=lambda record: record["level"].name in ["INFO", "ERROR"]
            )
        
    def get_logger(self):
        """Return configured logger"""
        return logger