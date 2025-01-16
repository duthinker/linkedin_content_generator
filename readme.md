# LinkedIn Content Generator Documentation

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Core Components](#core-components)
- [Usage](#usage)
- [Content Types](#content-types)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)

## Overview

The LinkedIn Content Generator automates the creation of various LinkedIn content types. It supports multiple formats, ensures consistent brand voice, and includes robust error handling and logging.

### Key Features

- Multiple content type generation (text, carousel, polls, etc.)
- Brand voice consistency
- Configurable templates
- Robust error handling and logging
- Backup and recovery system
- Content validation
- Format-specific optimization

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key

### Dependencies

```bash
pip install openai loguru pyyaml click python-dotenv
```

### Environment Setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
```

## Project Structure

```
project/
├── src/
│   ├── linkedin_generator.py    # Main content generation logic
│   ├── output_manager.py        # Output handling and formatting
│   ├── main.py                  # CLI interface
│   ├── log_config.py            # Logging configuration
│   └── utilities.py             # Utility functions
├── logs/                
│  ├── info/             # Information logs
│  ├── error/            # Error logs
│  └── debug/            # Debug logs
├── output/
│  ├── carousel/                 # Carousel content
│  ├── document/                 # Document content
│  ├── newsletter/               # Newsletter content
│  ├── poll/                     # Poll content
│  ├── text/                     # Text content
│  └── video_script/             # Video script content
├── README.md            # Main documentation
├── config.yaml          # Configuration file
├── requirements.txt     # Dependencies file
├── .env                 # Environment variables file
├── .gitignore           # Git ignore file
```

## Configuration

### Config File Structure

The `config.yaml` file contains all necessary configurations:

```yaml
content_types:            # Supported content types
brand_voice:              # Brand voice characteristics
content_config:           # Content generation settings
templates:                # Content templates
formatting:               # Format-specific settings
```

### Brand Voice Configuration

```yaml
brand_voice:
   tone:
      - professional
      - authoritative
   style:
      - conversational
      - storytelling
   personality:
      - authentic
      - trustworthy
```

## Core Components

### ContentGenerator

Main class responsible for content generation:

```python
generator = ContentGenerator(api_key="your_api_key", config_path="config.yaml")
content = generator.generate(
      content_type="text",
      topic="AI in Healthcare"
)
```

### OutputManager

Handles content saving and formatting:

```python
output_manager = OutputManager(backup_dir="backups")
paths = output_manager.save_content(content, "text")
```

## Usage

### Command Line Interface

The LinkedIn Content Generator can be used via the command line interface (CLI).

#### Basic Command

To generate content, use the following command:

```bash
python src/main.py --config config.yaml --topic "AI Trends" --content-type text
```

#### Options

- `--config, -c`: Path to the configuration file.
- `--topic, -t`: Topic for the content generation.
- `--content-type, -ct`: Type of content to generate (e.g., text, carousel, poll, etc.).
- `--slides, -s`: Number of slides for carousel content (default: 8).
- `--duration, -d`: Duration for video scripts (in seconds).
- `--backup-dir, -b`: Directory path for saving backups.

#### Examples

1. **Generate a Text Post:**

```bash
python src/main.py --config config.yaml --topic "AI in Healthcare" --content-type text
```

2. **Generate a Carousel with Custom Slides:**

```bash
python src/main.py --config config.yaml --topic "AI in Healthcare" --content-type carousel --slides 10
```

3. **Generate a Video Script with Specific Duration:**

```bash
python src/main.py --config config.yaml --topic "AI in Healthcare" --content-type video_script --duration 120
```

4. **Generate a Poll:**

```bash
python src/main.py --config config.yaml --topic "AI in Healthcare" --content-type poll
```

5. **Generate a Newsletter:**

```bash
python src/main.py --config config.yaml --topic "AI in Healthcare" --content-type newsletter
```

### Programmatic Usage

The LinkedIn Content Generator can also be used programmatically within your Python code.

#### Example

```python
from linkedin_generator import ContentGenerator, OutputManager

# Initialize the content generator
generator = ContentGenerator(api_key="your_api_key", config_path="config.yaml")

# Generate content
content = generator.generate(
    content_type="text",
    topic="AI in Healthcare"
)

# Initialize the output manager
output_manager = OutputManager(backup_dir="backups")

# Save the generated content
paths = output_manager.save_content(content, "text")
```

### Advanced Configuration

#### Using Custom Templates

Specify custom templates for content generation in the `config.yaml` file:

```yaml
templates:
   text: "templates/text_template.md"
   carousel: "templates/carousel_template.md"
   poll: "templates/poll_template.md"
   newsletter: "templates/newsletter_template.md"
   video_script: "templates/video_script_template.md"
```

#### Setting Brand Voice

Customize the brand voice to ensure consistency across all generated content:

```yaml
brand_voice:
   tone:
    - professional
    - authoritative
   style:
    - conversational
    - storytelling
   personality:
    - authentic
    - trustworthy
```

### Debugging and Logging

Enable detailed logging for debugging purposes:

```python
import logging
from linkedin_generator import logger

logger.setLevel(logging.DEBUG)
```

### Backup and Recovery

Ensure that all generated content is backed up and can be recovered in case of failures:

```python
output_manager = OutputManager(backup_dir="backups")
paths = output_manager.save_content(content, "text")
```

### Error Handling

Handle errors gracefully by implementing robust error handling mechanisms:

```python
try:
    content = generator.generate(content_type="text", topic="AI in Healthcare")
except ValidationError as e:
    print(f"Validation error: {e}")
except OutputError as e:
    print(f"Output error: {e}")
```

## Content Types

### Supported Types

1. Text Posts
    - Regular LinkedIn posts
    - Character limit: 3000
    - Supports formatting and emoji

2. Carousels
    - Multi-slide presentations
    - Configurable slides (default: 8)
    - Template-based structure

3. Polls
    - Interactive polls
    - 2-4 options
    - Custom poll structures

4. Newsletters
    - Structured content
    - Multiple sections
    - Template-based

5. Video Scripts
    - Timed sections
    - Hook and CTA
    - Duration-based formatting

6. Documents
    - Whitepapers
    - Case studies
    - Research reports

## Error Handling

### Exception Hierarchy

```python
class OutputError(Exception):
      pass

class FileError(OutputError):
      pass

class SerializationError(OutputError):
      pass

class ValidationError(OutputError):
      pass
```

### Content Validation

Content is validated at multiple levels:
- Configuration validation
- Input validation
- Output validation
- Format-specific validation

## Logging

### Log Configuration

Three log levels with separate files:
- INFO: General operation logs
- ERROR: Error tracking with tracebacks
- DEBUG: Detailed debugging information

### Log Directory Structure

```
logs/
├── info/
│   └── info_YYYY-MM-DD.log
├── error/
│   └── error_YYYY-MM-DD.log
└── debug/
      └── debug_YYYY-MM-DD.log
```

## Best Practices

1. Configuration Management
    - Keep sensitive data in .env
    - Regular config validation
    - Version control for configs

2. Content Generation
    - Use templates for consistency
    - Validate inputs
    - Include error handling
    - Implement rate limiting

3. Output Management
    - Regular backups
    - File validation
    - Atomic operations
    - Clean up temporary files

## Troubleshooting

### Common Issues

1. Configuration Errors
    ```
    Solution: Verify config.yaml structure and required fields
    ```

2. API Rate Limits
    ```
    Solution: Implement exponential backoff
    ```

3. File Permission Issues
    ```
    Solution: Check directory permissions and ownership
    ```

4. Memory Issues
    ```
    Solution: Implement chunked processing for large content
    ```

### Debug Mode

Enable debug logging:

```python
logger.level = "DEBUG"
```

## Performance Optimization

1. Content Generation
    - Template caching
    - Rate limit handling
    - Batch processing

2. File Operations
    - Chunked processing
    - Atomic operations
    - Cleanup routines

3. Memory Management
    - Stream large files
    - Clean temporary files
    - Regular garbage collection

## Security Considerations

1. API Key Management
    - Use environment variables
    - Regular key rotation
    - Access logging

2. File Operations
    - Secure file permissions
    - Path validation
    - Sanitize inputs

3. Content Validation
    - Input sanitization
    - Output validation
    - Format verification

## Contributing

1. Code Style
    - Follow PEP 8
    - Type hints
    - Documentation strings

2. Testing
    - Unit tests
    - Integration tests
    - Coverage reports

3. Version Control
    - Feature branches
    - Pull requests
    - Version tagging