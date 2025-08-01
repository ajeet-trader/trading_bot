import os
import re
import yaml
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv

# This pattern will look for ${VAR_NAME} or $VAR_NAME
ENV_VAR_PATTERN = re.compile(r'\$\{(\w+)\}|\$(\w+)')

def substitute_env_vars(config):
    """
    Recursively substitutes environment variables in the config dictionary.
    """
    for key, value in config.items():
        if isinstance(value, dict):
            substitute_env_vars(value)
        elif isinstance(value, str):
            def replace_match(match):
                # Handles both ${VAR} and $VAR formats
                var_name = match.group(1) or match.group(2)
                env_var = os.getenv(var_name)
                if env_var is None:
                    raise ValueError(
                        f"Configuration Error: Environment variable '{var_name}' "
                        "is referenced in config.yaml but not set."
                    )
                return env_var
            
            config[key] = ENV_VAR_PATTERN.sub(replace_match, value)
    return config

@lru_cache(maxsize=None)
def load_config(config_path: str = 'config.yaml') -> dict:
    """
    Loads the application configuration from a YAML file and environment variables.

    The function performs the following steps:
    1. Loads the .env file to populate environment variables.
    2. Finds and loads the specified YAML configuration file.
    3. Recursively substitutes any placeholders like `${VAR_NAME}` or `$VAR_NAME`
       with the corresponding environment variable's value.
    4. Caches the resulting configuration dictionary to ensure it's loaded only once.

    Args:
        config_path (str): The path to the configuration file relative to the project root.

    Returns:
        dict: A dictionary containing the fully resolved configuration.

    Raises:
        FileNotFoundError: If the specified config_path does not exist.
        ValueError: If an environment variable referenced in the YAML is not set.
        yaml.YAMLError: If the YAML file is malformed.
    """
    print("Attempting to load configuration...")
    
    # Load .env file from the project root
    project_root = Path(__file__).parent.parent
    dotenv_path = project_root / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Loaded environment variables from: {dotenv_path}")

    # Load the main YAML configuration file
    config_file = project_root / config_path
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found at: {config_file}")

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        print(f"Loaded configuration from: {config_file}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        raise

    # Substitute environment variables and return
    resolved_config = substitute_env_vars(config)
    print("Configuration loaded and resolved successfully.")
    return resolved_config

# You can create a global config object for easy access across modules
# This will be loaded the first time it's imported.
config = load_config()

if __name__ == '__main__':
    # Example of how to use the loader
    # Running this file directly will test the loading process.
    print("\n--- Configuration Data ---")
    import json
    print(json.dumps(config, indent=2))
    print("\n--- Testing Cache ---")
    # This second call should not print the "loading" messages
    # because the result is cached.
    cached_config = load_config()
    assert id(config) == id(cached_config), "Cache test failed: Config was reloaded."
    print("Cache test passed: Configuration was loaded only once.")