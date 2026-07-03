from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yaml
import os
from dotenv import dotenv_values

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


def convert_value(key, value):
    if key in ["port", "workers"]:
        return int(value)
    if key == "debug":
        return str(value).lower() in ["true", "1", "yes", "on"]
    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):

    # 1 defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    # 2 yaml
    with open("config.development.yaml", "r") as f:
        yaml_config = yaml.safe_load(f)
        config.update(yaml_config)

    # 3 .env layer (read separately)
    env_file = dotenv_values(".env")

    env_mapping = {
        "APP_PORT": "port",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "NUM_WORKERS": "workers"
    }

    for env_key, config_key in env_mapping.items():
        if env_key in env_file:
            config[config_key] = convert_value(config_key, env_file[env_key])

    # 4 OS env vars (real shell env only)
    os_mapping = {
        "APP_DEBUG": "debug",
        "APP_API_KEY": "api_key"
    }

    for env_key, config_key in os_mapping.items():
        value = os.environ.get(env_key)
        if value is not None:
            config[config_key] = convert_value(config_key, value)

    # 5 CLI overrides
    for item in set:
        if "=" in item:
            key, value = item.split("=", 1)
            config[key] = convert_value(key, value)

    # mask secret
    config["api_key"] = "****"

    return config

@app.get("/check-env")
def check_env():
    return {
        "APP_DEBUG": os.environ.get("APP_DEBUG"),
        "APP_API_KEY": os.environ.get("APP_API_KEY")
    }
