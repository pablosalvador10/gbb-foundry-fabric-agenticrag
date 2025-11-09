"""
Dynamic Agent Configuration Loader.

This module provides utilities to load agent configurations from YAML files
(locally or from URLs) and dynamically create agents based on those configurations.
"""

import os
import yaml
import requests
from typing import Dict, Any, List, Callable, Optional
from utils.ml_logging import get_logger

logger = get_logger("agent_registry.config_loader")


def load_yaml_config(config_source: str) -> Dict[str, Any]:
    """
    Load YAML configuration from a file path or URL.

    :param config_source: Local file path or HTTP(S) URL to YAML config
    :return: Parsed YAML configuration as dictionary
    :raises: Exception if loading or parsing fails
    """
    try:
        # Check if source is a URL
        if config_source.startswith(("http://", "https://")):
            logger.info(f"Loading agent config from URL: {config_source}")
            response = requests.get(config_source, timeout=10)
            response.raise_for_status()
            config = yaml.safe_load(response.text)
            logger.info("Agent config loaded successfully from URL")
        else:
            # Load from local file
            logger.info(f"Loading agent config from file: {config_source}")
            with open(config_source, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info("Agent config loaded successfully from file")

        return config

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to load config from URL: {str(e)}")
        raise
    except FileNotFoundError as e:
        logger.error(f"Config file not found: {str(e)}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML config: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading config: {str(e)}")
        raise


def validate_agent_config(config: Dict[str, Any]) -> bool:
    """
    Validate that agent configuration contains required fields.

    :param config: Agent configuration dictionary
    :return: True if valid, raises exception if invalid
    :raises: ValueError if configuration is invalid
    """
    required_fields = ["name", "description", "instructions", "azure_openai"]

    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field in agent config: {field}")

    # Validate azure_openai section
    azure_config = config["azure_openai"]
    required_azure_fields = ["endpoint_env", "api_key_env", "deployment_env"]

    for field in required_azure_fields:
        if field not in azure_config:
            raise ValueError(f"Missing required Azure OpenAI field: {field}")

    logger.info("Agent configuration validated successfully")
    return True


def resolve_env_variables(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve environment variable references in configuration.

    :param config: Agent configuration with env variable references
    :return: Configuration with resolved values
    """
    resolved_config = config.copy()

    # Resolve Azure OpenAI environment variables
    azure_config = resolved_config["azure_openai"]
    azure_config["endpoint"] = os.getenv(azure_config["endpoint_env"])
    azure_config["api_key"] = os.getenv(azure_config["api_key_env"])
    azure_config["deployment"] = os.getenv(azure_config["deployment_env"])

    # Log missing environment variables
    if not azure_config["endpoint"]:
        logger.warning(f"Environment variable not set: {azure_config['endpoint_env']}")
    if not azure_config["api_key"]:
        logger.warning(f"Environment variable not set: {azure_config['api_key_env']}")
    if not azure_config["deployment"]:
        logger.warning(
            f"Environment variable not set: {azure_config['deployment_env']}"
        )

    return resolved_config


def get_config_location_from_env(agent_name: str) -> str:
    """
    Get agent configuration file location from environment variable.

    The environment variable should be named: {AGENT_NAME}_CONFIG
    For example: AIRLINE_OPS_CONTEXT_CONFIG

    :param agent_name: Name of the agent (will be uppercased)
    :return: Configuration file path or URL
    :raises: ValueError if environment variable is not set
    """
    env_var_name = f"{agent_name.upper()}_CONFIG"
    config_location = os.getenv(env_var_name)

    if not config_location:
        raise ValueError(
            f"Configuration location not found in environment variable: {env_var_name}"
        )

    logger.info(f"Found config location for {agent_name}: {config_location}")
    return config_location


def load_agent_config(
    agent_name: str, config_source: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load and validate agent configuration.

    If config_source is not provided, will look for environment variable
    {AGENT_NAME}_CONFIG to get the location.

    :param agent_name: Name of the agent
    :param config_source: Optional path or URL to config file
    :return: Validated and resolved agent configuration
    :raises: Exception if loading, validation, or resolution fails
    """
    try:
        # Get config source from environment if not provided
        if not config_source:
            config_source = get_config_location_from_env(agent_name)

        # Load YAML configuration
        config = load_yaml_config(config_source)

        # Validate configuration structure
        validate_agent_config(config)

        # Resolve environment variables
        resolved_config = resolve_env_variables(config)

        logger.info(f"Agent config loaded successfully for: {agent_name}")
        return resolved_config

    except Exception as e:
        logger.error(f"Failed to load agent config for {agent_name}: {str(e)}")
        raise
