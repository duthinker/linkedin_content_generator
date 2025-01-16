from typing import List, Dict, Union
import openai
from dataclasses import dataclass, field
from enum import Enum
import yaml
from datetime import datetime
import random
from time import sleep
from log_config import LogConfig
from output_manager import OutputManager
from utilities import serialize_config

class ContentType(Enum):
    TEXT = "text"
    CAROUSEL = "carousel"
    POLL = "poll"
    NEWSLETTER = "newsletter"
    VIDEO_SCRIPT = "video_script"
    DOCUMENT = "document"

class ContentGoal(Enum):
    THOUGHT_LEADERSHIP = "thought_leadership"
    ENGAGEMENT = "engagement"
    LEAD_GENERATION = "lead_generation"
    BRAND_AWARENESS = "brand_awareness"
    RECRUITMENT = "recruitment"

@dataclass
class BrandVoice:
    """Brand voice characteristics"""
    tone: List[str] = field(default_factory=lambda: ["professional"])
    style: List[str] = field(default_factory=lambda: ["conversational"])
    personality: List[str] = field(default_factory=lambda: ["authentic"])
    key_phrases: List[str] = field(default_factory=list)
    emoji_style: str = "minimal"
    industry_hashtags: List[str] = field(default_factory=list)

@dataclass
class ContentConfig:
    """Configuration for content generation"""
    primary_goal: ContentGoal
    target_audience: List[str]
    brand_voice: BrandVoice
    industry_context: str
    custom_parameters: Dict = field(default_factory=dict)
    logger = LogConfig().get_logger()  # Add logger as class variable
    
    @classmethod
    def from_yaml(cls, file_path: str) -> 'ContentConfig':
        """Load configuration from YAML file"""
        cls.logger.debug(f"Loading configuration from YAML file: {file_path}")
        with open(file_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        content_config = config_data.get('content_config', {})
        brand_voice_data = config_data.get('brand_voice', {})
        
        brand_voice = BrandVoice(
            tone=brand_voice_data.get('tone', []),
            style=brand_voice_data.get('style', []),
            personality=brand_voice_data.get('personality', []),
            key_phrases=brand_voice_data.get('key_phrases', []),
            emoji_style=brand_voice_data.get('emoji_style', 'minimal'),
            industry_hashtags=brand_voice_data.get('industry_hashtags', [])
        )
        
        return cls(
            primary_goal=ContentGoal(content_config.get('primary_goal')),
            target_audience=content_config.get('target_audience', []),
            brand_voice=brand_voice,
            industry_context=content_config.get('industry_context', ''),
            custom_parameters=content_config.get('custom_parameters', {})
        )

    def validate(self) -> None:
        """Validate configuration"""
        self.logger.debug("Validating configuration")
        if not self.target_audience:
            self.logger.error("Validation failed: Target audience cannot be empty")
            raise ValueError("Target audience cannot be empty")
        if not self.industry_context:
            self.logger.error("Validation failed: Industry context cannot be empty")
            raise ValueError("Industry context cannot be empty")
        if not self.brand_voice.tone:
            self.logger.error("Validation failed: Brand voice tone cannot be empty")
            raise ValueError("Brand voice tone cannot be empty")

class ContentGenerator:
    """Content generator with support for multiple content types"""
    
    def __init__(self, api_key: str, config_path: str):
        # Initialize logger
        log_config = LogConfig()
        self.logger = log_config.get_logger()
        
        self.logger.info("Initializing Content Generator")
        
        self.api_key = api_key
        
        # Load and validate configuration
        try:
            self.config = ContentConfig.from_yaml(config_path)
            self.config.validate()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
        
        # Load templates
        try:
            self.templates = self._load_templates(config_path)
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
            raise
        
        # Initialize output manager
        self.output_manager = OutputManager()
        self.logger.debug("Output manager initialized")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        self.logger.debug(f"Loading configuration from YAML file: {config_path}")
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing configuration file: {e}")
            raise

    def _load_templates(self, config_path: str) -> Dict:
        """Load templates from YAML"""
        self.logger.debug(f"Loading templates from YAML file: {config_path}")
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('templates', {})
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
            raise

    def generate(self, content_type: Union[ContentType, str], topic: str, **kwargs) -> Dict:
        """Generate content based on type"""
        try:
            if isinstance(content_type, str):
                content_type = ContentType(content_type)
            
            # Generate the content
            if content_type == ContentType.TEXT:
                content = self._generate_text_post(topic, **kwargs)
            elif content_type == ContentType.CAROUSEL:
                content = self._generate_carousel(topic, **kwargs)
            elif content_type == ContentType.POLL:
                content = self._generate_poll(topic, **kwargs)
            elif content_type == ContentType.NEWSLETTER:
                content = self._generate_newsletter(topic, **kwargs)
            elif content_type == ContentType.VIDEO_SCRIPT:
                content = self._generate_video_script(topic, **kwargs)
            elif content_type == ContentType.DOCUMENT:
                content = self._generate_document(topic, **kwargs)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")

            # Save the content using output manager
            try:
                saved_paths = self.output_manager.save_content(content, content_type.value)
                content['output_paths'] = saved_paths
                self.logger.info(f"Content saved successfully at: {saved_paths}")
            except Exception as e:
                self.logger.error(f"Failed to save content: {e}")
                raise

            return content
        except Exception as e:
            self.logger.error(f"Error generating content: {e}")
            raise

    def _get_completion(self, prompt: str) -> str:
        """Get completion from OpenAI with retry logic"""
        max_retries = 3
        client = openai.OpenAI(api_key=self.api_key)  # Create client instance
        
        for attempt in range(max_retries):
            try:
                # Use the new API format
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",  # or "gpt-4" if available
                    messages=[
                        {
                            "role": "system",
                            "content": f"""You are a professional LinkedIn content writer.
                                Brand Voice:
                                - Tone: {', '.join(self.config.brand_voice.tone)}
                                - Style: {', '.join(self.config.brand_voice.style)}
                                - Personality: {', '.join(self.config.brand_voice.personality)}
                                Write in a way that resonates with: {', '.join(self.config.target_audience)}"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    # max_tokens=500
                )
                # Access the response content using the new API format
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                self.logger.error(f"Error getting completion (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    def _generate_text_post(self, topic: str, **kwargs) -> Dict:
        """Generate a text post"""
        try:
            hook = self._generate_hook(topic, ContentType.TEXT)
            main_content = self._generate_main_content(topic, hook)
            cta = self._generate_cta(topic)
            formatted_post = self._format_post(hook, main_content, cta, **kwargs)
            metadata = self._generate_metadata(topic, hook, cta)
            
            return {
                "type": "text",
                "content": formatted_post,
                "metadata": metadata,
                "raw_components": {
                    "hook": hook,
                    "main_content": main_content,
                    "cta": cta
                }
            }
        except Exception as e:
            self.logger.error(f"Error generating text post: {e}")
            raise

    def _generate_carousel(self, topic: str, **kwargs) -> Dict:
        """Generate a carousel post"""
        try:
            self.logger.debug(f"Generating carousel for topic: {topic}")

            num_slides = kwargs.get('num_slides', 
                                  self.config.custom_parameters.get('carousel_slides', 8))
            
            hook = self._generate_hook(topic, ContentType.CAROUSEL)
            self.logger.debug("Hook generated successfully")

            sections = self.templates.get('carousel_sections', [])[:num_slides]
            
            slides = []
            for section in sections:
                slide_content = self._generate_slide_content(topic, section)
                slides.append({
                    "title": section,
                    "content": slide_content
                })
            self.logger.debug("Carousel sections generated successfully")
            
            cta = self._generate_cta(topic)
            self.logger.debug("CTA generated successfully")

            self.logger.info(f"Successfully generated carousel about {topic}")
            return {
                "type": "carousel",
                "hook": hook,
                "slides": slides,
                "cta": cta,
                "metadata": self._generate_metadata(topic, hook, cta)
            }
        except Exception as e:
            self.logger.error(f"Error generating carousel: {str(e)}")
            raise

    def _generate_poll(self, topic: str, **kwargs) -> Dict:
        """Generate a poll"""
        try:
            self.logger.debug(f"Generating poll for topic: {topic}")

            poll_type = kwargs.get('poll_type', 'implementation')
            num_options = kwargs.get('num_options', 
                                   self.config.custom_parameters.get('poll_options', 4))
            
            hook = self._generate_hook(topic, ContentType.POLL)
            self.logger.debug("Hook generated successfully")

            options = self.templates.get('poll_structures', {}).get(poll_type, [])[:num_options]
            
            # Format options with topic
            formatted_options = [
                opt.format(
                    topic=topic,
                    choice_a=f"{topic} Solution A",
                    choice_b=f"{topic} Solution B",
                    choice_c=f"{topic} Solution C"
                ) for opt in options
            ]
            self.logger.debug("Poll options formatted successfully")
            
            context = self._generate_poll_context(topic)
            self.logger.debug("Poll context generated successfully")
            
            self.logger.info(f"Successfully generated poll about {topic}")
            return {
                "type": "poll",
                "hook": hook,
                "context": context,
                "options": formatted_options,
                "metadata": self._generate_metadata(topic, hook, "")
            }
        except Exception as e:
            self.logger.error(f"Error generating poll: {str(e)}")
            raise

    def _generate_newsletter(self, topic: str, **kwargs) -> Dict:
        """Generate a newsletter"""
        try:
            self.logger.debug(f"Generating newsletter for topic: {topic}")

            sections = self.templates.get('newsletter_sections', [])
            hook = self._generate_hook(topic, ContentType.NEWSLETTER)
            self.logger.debug("Hook generated successfully")
            
            content = {}
            for section in sections:
                content[section] = self._generate_section_content(topic, section)
            self.logger.debug("Newsletter sections generated successfully")
            
            cta = self._generate_cta(topic)
            self.logger.debug("CTA generated successfully")
            
            self.logger.info(f"Successfully generated newsletter about {topic}")
            return {
                "type": "newsletter",
                "hook": hook,
                "sections": content,
                "cta": cta,
                "metadata": self._generate_metadata(topic, hook, cta)
            }
        except Exception as e:
            self.logger.error(f"Error generating newsletter: {str(e)}")
            raise

    def _generate_video_script(self, topic: str, **kwargs) -> Dict:
        """Generate a video script"""
        try:
            self.logger.debug(f"Generating video script for topic: {topic}")

            duration = kwargs.get('duration', 
                                self.config.custom_parameters.get('video_length_minutes', 3))
            sections = self.templates.get('video_script_sections', [])
            
            hook = self._generate_hook(topic, ContentType.VIDEO_SCRIPT)
            self.logger.debug("Hook generated successfully")

            script_sections = {}
            
            for section in sections:
                script_sections[section] = self._generate_script_section(topic, section, duration)
            self.logger.debug("Video script sections generated successfully")
            
            self.logger.info(f"Successfully generated video script about {topic}")
            return {
                "type": "video_script",
                "hook": hook,
                "script": script_sections,
                "duration": duration,
                "metadata": self._generate_metadata(topic, hook, "")
            }
        except Exception as e:
            self.logger.error(f"Error generating video script: {str(e)}")
            raise

    def _generate_document(self, topic: str, **kwargs) -> Dict:
        """Generate a document (whitepaper/case study)"""
        try:
            self.logger.debug(f"Generating document for topic: {topic}")
            
            doc_type = kwargs.get('document_type', 'whitepaper')
            sections = self.templates.get('document_sections', {}).get(doc_type, [])
            
            hook = self._generate_hook(topic, ContentType.DOCUMENT)
            self.logger.debug("Hook generated successfully")
            
            content_sections = {}
            
            for section in sections:
                content_sections[section] = self._generate_document_section(topic, section, doc_type)
            self.logger.debug("Document sections generated successfully")
            
            self.logger.info(f"Successfully generated document about {topic}")
            return {
                "type": "document",
                "hook": hook,
                "sections": content_sections,
                "doc_type": doc_type,
                "metadata": self._generate_metadata(topic, hook, "")
            }
        except Exception as e:
            self.logger.error(f"Error generating document: {str(e)}")
            raise

    def _generate_hook(self, topic: str, content_type: ContentType) -> str:
        """Generate a hook for the content"""
        self.logger.debug(f"Generating hook for {content_type.value} content about {topic}")
        hooks = self.templates.get('hooks', {}).get(content_type.value, [])
        if hooks:
            template = random.choice(hooks)
            return template.format(
                topic=topic,
                duration="1 year",
                num_slides=self.config.custom_parameters.get('carousel_slides', 8)
            )
        
        prompt = self._create_prompt("hook", {
            "topic": topic,
            "content_type": content_type.value,
            "goal": self.config.primary_goal.value
        })
        
        return self._get_completion(prompt)

    def _generate_main_content(self, topic: str, hook: str) -> str:
        """Generate main content using PASS framework"""
        self.logger.debug(f"Generating main content for topic: {topic} with hook: {hook}")
        
        prompt = self._create_prompt("main_content", {
            "topic": topic,
            "hook": hook,
            "framework": "PASS"
        })
        
        try:
            content = self._get_completion(prompt)
            
            # Validate content length
            if len(content) < 50:  # Minimum content length
                self.logger.warning("Generated content too short, retrying...")
                content = self._get_completion(prompt)  # Retry once
                
            return content
        except Exception as e:
            self.logger.error(f"Error generating main content: {e}")
            raise

    def _generate_slide_content(self, topic: str, section: str) -> str:
        """Generate content for a carousel slide"""
        self.logger.debug(f"Generating slide content for section: {section} about topic: {topic}")
        prompt = self._create_prompt("slide", {
            "topic": topic,
            "section": section
        })
        
        return self._get_completion(prompt)

    def _generate_poll_context(self, topic: str) -> str:
        """Generate context for a poll"""
        self.logger.debug(f"Generating poll context for topic: {topic}")
        prompt = self._create_prompt("poll_context", {
            "topic": topic
        })
        
        return self._get_completion(prompt)

    def _generate_section_content(self, topic: str, section: str) -> str:
        """Generate content for a newsletter section"""
        self.logger.debug(f"Generating section content for section: {section} about topic: {topic}")
        prompt = self._create_prompt("newsletter_section", {
            "topic": topic,
            "section": section
        })
        
        return self._get_completion(prompt)

    def _generate_script_section(self, topic: str, section: str, duration: int) -> str:
        """Generate content for a video script section"""
        self.logger.debug(f"Generating script section for section: {section} about topic: {topic} with duration: {duration}")
        prompt = self._create_prompt("video_section", {
            "topic": topic,
            "section": section,
            "duration": duration
        })
        
        return self._get_completion(prompt)

    def _generate_document_section(self, topic: str, section: str, doc_type: str) -> str:
        """Generate content for a document section"""
        self.logger.debug(f"Generating document section for section: {section} about topic: {topic} with doc_type: {doc_type}")
        prompt = self._create_prompt("document_section", {
            "topic": topic,
            "section": section,
            "doc_type": doc_type
        })
        
        return self._get_completion(prompt)

    def _generate_cta(self, topic: str) -> str:
        """Generate a call-to-action"""
        self.logger.debug(f"Generating CTA for topic: {topic}")
        ctas = self.templates.get('cta', {}).get(self.config.primary_goal.value, [])
        if ctas:
            template = random.choice(ctas)
            return template.format(topic=topic)
        
        prompt = self._create_prompt("cta", {
            "topic": topic,
            "goal": self.config.primary_goal.value
        })
        
        return self._get_completion(prompt)

    def _format_post(self, hook: str, content: str, cta: str, **kwargs) -> str:
        """Format the post with custom formatting"""
        self.logger.debug("Formatting post")
        
        # Get formatting preferences from config
        custom_params = self.config.custom_parameters
        formatting = kwargs.get('custom_formatting', {})
        
        # Determine line breaks (default to 2)
        line_breaks = "\n" * formatting.get('line_breaks', 2)
        
        # Process content paragraphs
        content_lines = content.split('\n')
        processed_lines = []
        
        for line in content_lines:
            if not line.strip():
                continue
                
            # Apply emoji prefix if configured
            if emoji_prefix := formatting.get('emoji_prefix'):
                line = f"{emoji_prefix} {line}"
            
            processed_lines.append(line.strip())
        
        # Join processed content
        processed_content = line_breaks.join(processed_lines)
        
        # Assemble the post
        parts = []
        if hook:
            parts.append(hook.strip())
        if processed_content:
            parts.append(processed_content)
        if cta:
            parts.append(cta.strip())
            
        formatted_content = line_breaks.join(parts)
        
        # Add hashtags if configured
        num_hashtags = kwargs.get('num_hashtags', 
                                custom_params.get('num_hashtags', 3))
        
        if hashtags := self._generate_hashtags(num_hashtags):
            if custom_params.get('hashtag_style') == 'integrated':
                formatted_content += f"\n\n{' '.join(hashtags)}"
            else:
                formatted_content += f"{line_breaks}{' '.join(hashtags)}"
        
        self.logger.debug("Post formatted successfully")
        return formatted_content

    def _generate_hashtags(self, num_hashtags: int) -> List[str]:
        """Generate relevant hashtags"""
        self.logger.debug(f"Generating {num_hashtags} hashtags")
        all_hashtags = [
            f"#{tag}" for tag in self.config.brand_voice.industry_hashtags
        ]
        hashtags = random.sample(all_hashtags, min(num_hashtags, len(all_hashtags)))
        self.logger.debug(f"Generated hashtags: {hashtags}")
        return hashtags

    def _generate_metadata(self, topic: str, hook: str, cta: str) -> Dict:
        """Generate metadata for content"""
        self.logger.debug(f"Generating metadata for topic: {topic}")
        
        try:
            metadata = {
                "topic": topic,
                "hook": hook,
                "cta": cta,
                "generation_time": datetime.now().isoformat(),
                "config": serialize_config(self.config)
            }
            self.logger.debug(f"Generated metadata: {metadata}")
            return metadata
        
        except Exception as e:
            self.logger.error(f"Error generating metadata: {str(e)}")
            # Return minimal metadata if serialization fails
            return {
                "topic": topic,
                "generation_time": datetime.now().isoformat()
            }

    def _create_prompt(self, prompt_type: str, params: Dict) -> str:
        """Create a prompt for OpenAI"""
        self.logger.debug(f"Creating prompt of type: {prompt_type} with params: {params}")
        
        # Get brand voice components
        brand_voice = self.config.brand_voice
        tone = ", ".join(brand_voice.tone)
        style = ", ".join(brand_voice.style)
        personality = ", ".join(brand_voice.personality)
        industry_context = self.config.industry_context
        target_audience = ", ".join(self.config.target_audience)

        prompts = {
            "hook": f"""
                Create an attention-grabbing hook for a {params.get('content_type', 'post')} about {params['topic']}.
                
                Goal: {self.config.primary_goal.value}
                Target Audience: {target_audience}
                Industry Context: {industry_context}
                
                Brand Voice Guidelines:
                - Tone: {tone}
                - Style: {style}
                - Personality: {personality}
                
                The hook should:
                1. Be attention-grabbing but professional
                2. Create curiosity without clickbait
                3. Be relevant to the target audience
                4. Stay under 100 characters
                5. Align with the industry context
            """,
            
            "main_content": f"""
                Create the main content for a LinkedIn post about {params['topic']}.
                Starting Hook: "{params.get('hook', '')}"
                
                Target Audience: {target_audience}
                Industry Context: {industry_context}
                
                Use the PASS framework:
                1. Problem: Clearly articulate a specific challenge in {params['topic']}
                2. Amplify: Explain why this matters now and its business impact
                3. Solution: Provide unique, actionable insights or approaches
                4. Success: Demonstrate impact with specific examples or data
                
                Brand Voice Requirements:
                - Tone: {tone}
                - Style: {style}
                - Personality: {personality}
                
                Content Guidelines:
                - Keep paragraphs short (2-3 lines)
                - Include at least one specific statistic or example
                - Make it valuable for {target_audience}
                - Focus on professional insights
                - Total length: 1000-1300 characters
            """,
            
            "cta": f"""
                Create a compelling call-to-action for a LinkedIn post about {params['topic']}.
                Goal: {self.config.primary_goal.value}
                Target Audience: {target_audience}
                
                Requirements:
                - Be natural and conversational
                - Encourage meaningful engagement
                - Align with {self.config.primary_goal.value} goal
                - Stay under 100 characters
                - Match the professional tone while being engaging
                
                Brand Voice:
                - Tone: {tone}
                - Style: {style}
                - Personality: {personality}
            """,

            "slide": """
                Create content for a carousel slide about {topic}.
                Section: {section}
                
                Include:
                - Main point
                - Supporting details
                - Example or statistic
                
                Keep it concise and visual.
            """,

            "poll_context": """
                Create a brief context for a poll about {topic}.
                
                Include:
                - Why this matters now
                - What insights voters will gain
                - How results will be valuable
            """,

            "newsletter_section": """
                Create content for the "{section}" section of a newsletter about {topic}.
                
                Make it:
                - Informative
                - Current
                - Actionable
            """,

            "video_section": """
                Create a script for the "{section}" section of a {duration}-minute video about {topic}.
                
                Focus on:
                - Clear delivery
                - Engaging content
                - Visual descriptions
            """,

            "document_section": """
                Create content for the "{section}" section of a {doc_type} about {topic}.
                
                Include:
                - Main points
                - Supporting evidence
                - Industry context
                - Actionable insights
            """
        }
        
        base_prompt = prompts.get(prompt_type, "")
        if not base_prompt:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
            
        # Format with any additional parameters
        try:
            prompt = base_prompt.format(**params)
            self.logger.debug(f"Created prompt: {prompt}")
            return prompt
        except KeyError as e:
            self.logger.error(f"Missing required parameter for prompt: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error formatting prompt: {e}")
            raise
