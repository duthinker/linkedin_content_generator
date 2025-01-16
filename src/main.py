import click
from pathlib import Path
import sys
from typing import Optional
from dotenv import load_dotenv
import os
from log_config import LogConfig
from linkedin_generator import ContentGenerator, ContentType
import yaml
from output_manager import OutputManager

class LinkedInContentCLI:
    def __init__(self):
        # Initialize logging
        log_config = LogConfig()
        self.logger = log_config.get_logger()
        log_config.setup_logger()

    def validate_env(self):
        """Validate required environment variables"""
        if not os.getenv("OPENAI_API_KEY"):
            self.logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")

    def validate_config(self, config: dict) -> None:
        """Validate configuration completeness"""
        self.logger.debug("Validating configuration")
        required_sections = [
            'content_config',
            'brand_voice',
            'templates'
        ]
        
        # Check required sections
        for section in required_sections:
            if section not in config:
                self.logger.error(f"Validation failed: Missing required section: {section}")
                raise ValueError(f"Missing required section: {section}")
        
        # Validate content_config section
        content_config = config.get('content_config', {})
        if not content_config.get('primary_goal'):
            self.logger.error("Validation failed: Missing primary_goal in content_config")
            raise ValueError("Missing primary_goal in content_config")
        if not content_config.get('target_audience'):
            self.logger.error("Validation failed: Missing target_audience in content_config")
            raise ValueError("Missing target_audience in content_config")
        
        # Validate brand_voice section
        brand_voice = config.get('brand_voice', {})
        if not brand_voice.get('tone'):
            self.logger.error("Validation failed: Missing tone in brand_voice")
            raise ValueError("Missing tone in brand_voice")
        if not brand_voice.get('style'):
            self.logger.error("Validation failed: Missing style in brand_voice")
            raise ValueError("Missing style in brand_voice")
        
        self.logger.debug("Configuration validation successful")

    def validate_components(
        self,
        generator: ContentGenerator,
        output_manager: OutputManager
    ) -> None:
        """Validate component integration"""
        self.logger.debug("Validating component integration")
        # Verify matching content types
        generator_types = set(t.value for t in ContentType)
        output_types = set(output_manager.FORMATTERS.keys())
        if not generator_types.issubset(output_types):
            missing = generator_types - output_types
            self.logger.error(f"Validation failed: Missing formatters for types: {missing}")
            raise ValueError(f"Missing formatters for types: {missing}")
        self.logger.debug("Component validation successful")

    def initialize_components(self, config_path: str, api_key: str, backup_dir: Optional[str] = None):
        """Initialize all components with validation"""
        try:
            # Load config first
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.validate_config(config)
            
            # Initialize components
            generator = ContentGenerator(api_key=api_key, config_path=config_path)
            output_manager = OutputManager(backup_dir=backup_dir)
            
            # Validate components
            self.validate_components(generator, output_manager)
            
            return generator, output_manager
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            raise

    def load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            self.logger.debug(f"Loading configuration from: {config_path}")
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing configuration file: {e}")
            raise

    def cleanup_temp_files(self):
        """Cleanup temporary files on exit"""
        try:
            temp_pattern = "*.tmp"
            for temp_file in Path("output").rglob(temp_pattern):
                temp_file.unlink()
        except Exception as e:
            self.logger.warning(f"Cleanup warning: {e}")

    def run(self, config: str, topic: str, content_type: str, slides: Optional[int], 
            duration: Optional[int], backup_dir: Optional[str]):
        """Run the content generation process"""
        try:
            self.logger.info("Starting LinkedIn Content Generator")
            
            # Create output directory if it doesn't exist
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # Load environment variables
            load_dotenv()
            self.validate_env()
            self.logger.info("Environment variables loaded successfully")
            
            # Initialize generator
            try:
                generator, output_manager = self.initialize_components(
                    config_path=config,
                    api_key=os.getenv("OPENAI_API_KEY"),
                    backup_dir=backup_dir
                )
                self.logger.info("Components initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize components: {str(e)}")
                raise
            
            # Prepare generation parameters
            kwargs = {}
            if slides and content_type == ContentType.CAROUSEL.value:
                kwargs['num_slides'] = slides
            if duration and content_type == ContentType.VIDEO_SCRIPT.value:
                kwargs['duration'] = duration
                
            # Generate content
            self.logger.info(f"Generating {content_type} content for topic: {topic}")
            try:
                content = generator.generate(
                    content_type=content_type,
                    topic=topic,
                    **kwargs
                )
                self.logger.info("Content generated successfully")
                
                # Display output paths
                if 'output_paths' in content:
                    click.echo("\nFiles generated:")
                    for file_type, path in content['output_paths'].items():
                        click.echo(f"- {file_type}: {path}")
                
                # Display preview of the content
                if 'content' in content:
                    click.echo("\nContent Preview:")
                    click.echo("-" * 40)
                    preview = content['content']
                    if isinstance(preview, str):
                        click.echo(preview[:500] + "..." if len(preview) > 500 else preview)
                    else:
                        click.echo(str(preview)[:500] + "...")
                    click.echo("-" * 40)
                
            except Exception as e:
                self.logger.error(f"Content generation failed: {str(e)}")
                raise
            
            click.echo("\nContent generated successfully!")
            click.echo(f"Check the output folder for generated files.")
            self.logger.info("Process completed successfully")
            
        except Exception as e:
            self.logger.exception("An error occurred during content generation")
            click.echo(f"\nError: {str(e)}", err=True)
            sys.exit(1)
        finally:
            self.cleanup_temp_files()
            self.logger.info("Generator session ended")

@click.command()
@click.option('--config', '-c', default='config.yaml', help='Path to configuration file')
@click.option('--topic', '-t', prompt='Enter the content topic', help='Content topic')
@click.option(
    '--content-type', '-ct',
    type=click.Choice([t.value for t in ContentType]),
    prompt='Select content type',
    help='Type of content to generate'
)
@click.option('--slides', '-s', default=None, help='Number of slides for carousel')
@click.option('--duration', '-d', default=None, help='Duration for video script (minutes)')
@click.option('--backup-dir', '-b', default=None, help='Backup directory path')
def main(config: str, topic: str, content_type: str, slides: Optional[int], duration: Optional[int], backup_dir: Optional[str]):
    """LinkedIn Content Generator CLI"""
    cli = LinkedInContentCLI()
    cli.run(config, topic, content_type, slides, duration, backup_dir)

if __name__ == "__main__":
    main()