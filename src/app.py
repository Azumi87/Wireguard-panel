from flask import Flask, render_template, jsonify, request, redirect, session, flash, send_file, send_from_directory, make_response
import os
import subprocess
import gunicorn.app.base
import secrets
from gunicorn.app.base import BaseApplication
from ipaddress import ip_network
import psutil
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.base import ConflictingIdError
import threading
from warp import install_fullwarp, install_progress
from threading import Thread
import time
import shlex
import requests
import tempfile
import base64
import nacl.bindings
import json
from queue import Queue
from threading import Thread, Event
import shutil
import logging
import yaml
import shutil
from datetime import datetime, timedelta, timezone
import pytz
from threading import Event
from threading import Lock
from fasteners import InterProcessLock
import fcntl
from werkzeug.security import generate_password_hash, check_password_hash
from flask import make_response
from flask import Response
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from flask_bcrypt import Bcrypt
from jsonschema import validate, ValidationError
from ipaddress import ip_address
import re
from jinja2 import select_autoescape
from flask_caching import Cache
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.executors.pool import ProcessPoolExecutor
from flask_caching import Cache
from warp import install_warp
from warp import install_fullwarp
from cryptography.fernet import Fernet
import qrcode
from io import BytesIO
from flask_session import Session
from PIL import Image, ImageDraw, ImageFont
from flask import url_for
import time


def load_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.yaml") 

    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        config.setdefault("wireguard", {}).setdefault("config_dir", "/etc/wireguard")
        config.setdefault("flask", {}).setdefault("port", 5000)
        config.setdefault("flask", {}).setdefault("tls", False)
        config.setdefault("flask", {}).setdefault("cert_path", "")
        config.setdefault("flask", {}).setdefault("key_path", "")
        config.setdefault("flask", {}).setdefault("secret_key", "azumiisinyourarea")
        config.setdefault("flask", {}).setdefault("debug", False)

        return config
    except FileNotFoundError:
        print(f"ERROR: config.yaml is missing. Expected at {config_path}. Please create it with the required settings.")
        raise
    except yaml.YAMLError as e:
        print(f"ERROR: Wrong YAML format in config.yaml. Details: {e}")
        raise
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        raise

     
config = load_config()


app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['SESSION_TYPE'] = 'filesystem'  
app.config['SESSION_PERMANENT'] = True  
app.config['SESSION_USE_SIGNER'] = True  
app.config['SESSION_COOKIE_NAME'] = 'session'  
app.secret_key = config["flask"]["secret_key"]
Session(app)
app.debug = config["flask"]["debug"]
app.jinja_env.autoescape = select_autoescape(['html', 'htm', 'xml', 'xhtml'])
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"Base Directory: {BASE_DIR}")
API_FILE = os.path.join(BASE_DIR, "api.json")
SECRET_KEY_FILE = os.path.join(BASE_DIR, "secret.key")
TELEGRAM_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "telegram/telegram.yaml")
TELEGRAM_CONFIG_JSON = os.path.join(os.path.dirname(__file__), "telegram/config.json")
INSTALL_PROGRESS_FILE = os.path.join(BASE_DIR, "install_progress.json")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
DB_FILE = os.path.join(BASE_DIR, "db.json")
DB_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "db") 
os.makedirs(DB_DIR, exist_ok=True)  
SHORT_LINKS_FILE = os.path.join(BASE_DIR, "short_links.json")
WIREGUARD_CONFIG_DIR = config["wireguard"]["config_dir"]
PEERS = []  
print(f"BASE_DIR: {BASE_DIR}")
print(f"Config Path: {os.path.join(BASE_DIR, 'config.yaml')}")
print(f"DB_DIR: {DB_DIR}")
print(f"DB_FILE: {DB_FILE}")
print(f"API_FILE: {API_FILE}")
print(f"SECRET_KEY_FILE: {SECRET_KEY_FILE}")
print(f"INSTALL_PROGRESS_FILE: {INSTALL_PROGRESS_FILE}")
print(f"BACKUP_DIR: {BACKUP_DIR}")
print(f"TELEGRAM_CONFIG_FILE: {TELEGRAM_CONFIG_FILE}")
print(f"TELEGRAM_CONFIG_JSON: {TELEGRAM_CONFIG_JSON}")
print(f"Static Folder: {os.path.join(BASE_DIR, 'static')}")
print(f"Template Folder: {os.path.join(BASE_DIR, 'templates')}")

redis_client = Redis(host="localhost", port=6379, db=0)
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="redis://localhost:6379"  
)
bcrypt = Bcrypt(app)
countdown_event = Event()
json_lock = Lock()
metrics_queue = Queue(maxsize=1)
stop_event = Event()
cache = Cache(app, config={
    "CACHE_TYPE": "SimpleCache", 
    "CACHE_DEFAULT_TIMEOUT": 300 
})
app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_HOST"] = "localhost"
app.config["CACHE_REDIS_PORT"] = 6379
app.config["CACHE_REDIS_DB"] = 0
cache = Cache(app)


def get_system_timezone():
    try:
        with open("/etc/timezone", "r") as tz_file:
            etc_timezone = tz_file.read().strip()
        
        localtime_symlink = os.readlink("/etc/localtime")
        expected_symlink = f"/usr/share/zoneinfo/{etc_timezone}"

        if localtime_symlink != expected_symlink:
            print("[WARNING] Mismatch detected between /etc/timezone and /etc/localtime.")
            print(f"/etc/timezone: {etc_timezone}")
            print(f"/etc/localtime points to: {localtime_symlink}")

            print("[INFO] Fixing the time zone configuration...")
            subprocess.run(["sudo", "echo", etc_timezone, "|", "tee", "/etc/timezone"], check=True, shell=True)
            subprocess.run(["sudo", "dpkg-reconfigure", "-f", "noninteractive", "tzdata"], check=True)
            print("[INFO] Time zone configuration synchronized.")

            with open("/etc/timezone", "r") as tz_file:
                etc_timezone = tz_file.read().strip()
        
        return etc_timezone

    except Exception as e:
        print(f"[ERROR] Could not detect or fix system timezone: {e}")
        return "UTC"

system_timezone = pytz.timezone(get_system_timezone())
print(f"[INFO] Detected System Timezone: {system_timezone}")


@app.route("/set-language", methods=["POST"])
def set_language():
    selected_language = request.form.get("language")
    if selected_language in ["en", "fa"]:
        session["language"] = selected_language
        response = make_response(redirect(request.referrer or url_for("home")))
        response.set_cookie("language", selected_language, max_age=30*24*60*60)  
        return response
    return redirect(request.referrer or url_for("home"))



@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400

        try:
            with open(DB_FILE, "r") as f:
                users = json.load(f)
        except FileNotFoundError:
            app.logger.error(f"{DB_FILE} file not found.")
            return jsonify({"error": "Internal server error: User database missing."}), 500

        hashed_password = users.get(username)
        if not hashed_password:
            app.logger.warning(f"Username '{username}' not found in database.")
            return jsonify({"error": "Wrong username or password."}), 401

        if not bcrypt.check_password_hash(hashed_password, password):
            app.logger.warning(f"Password mismatch for username '{username}'.")
            return jsonify({"error": "Wrong username or password."}), 401

        session['username'] = username
        app.logger.info(f"User '{username}' logged in successfully.")
        return jsonify({"message": "Login successful!"}), 200

    except Exception as e:
        app.logger.error(f"Unexpected error during login: {e}")
        return jsonify({"error": "Internal server error."}), 500


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out successfully!"}), 200


@app.route('/api/wireguard-interfaces', methods=['GET'])
def obtain_wireguard_interfaces():

    try:
        config_dir = "/etc/wireguard"
        interfaces = [
            f for f in os.listdir(config_dir)
            if f.endswith(".conf")
        ]

        if not interfaces:
            return jsonify({"interfaces": []}), 200

        return jsonify({"interfaces": interfaces}), 200
    except FileNotFoundError:
        return jsonify({"error": "Wireguard config directory not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
def validate_json(schema=None):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:  
                return jsonify({"error": "Wrong content type. JSON required."}), 400
            try:
                data = request.get_json()
                if schema:
                    validate(instance=data, schema=schema)  
            except ValidationError as e:
                return jsonify({"error": f"Wrong JSON input: {e.message}"}), 400
            except Exception as e:
                return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
            return f(*args, **kwargs)
        return decorated_function
    return decorator

peer_schema = {
    "type": "object",
    "properties": {
        "peerName": {
            "type": "string",
            "pattern": r"^[a-zA-Z0-9_-]+$"
        },
        "peerIp": {
            "type": "string",
            "format": "ipv4"
        },
        "limit": {  
            "type": "string",
            "pattern": r"^\d+(MiB|GiB)$"
        },
        "configFile": {
            "type": "string",
            "pattern": r"^[a-zA-Z0-9_-]+\.conf$"
        },
        "dns": {"type": "string"},
        "expiryMonths": {"type": "integer", "minimum": 0},
        "expiryDays": {"type": "integer", "minimum": 0},
        "expiryHours": {"type": "integer", "minimum": 0},
        "expiryMinutes": {"type": "integer", "minimum": 0},
        "firstUsage": {"type": "boolean"},
        "mtu": {"type": "integer", "minimum": 0},
        "persistentKeepalive": {"type": "integer", "minimum": 0}
    },
    "required": ["peerName", "peerIp", "limit"],  
    "additionalProperties": False
}

edit_peer_schema = {
    "type": "object",
    "properties": {
        "peerName": {
            "type": "string",
            "pattern": r"^[a-zA-Z0-9_-]+$"
        },
        "dataLimit": {
            "type": ["string", "null"],
            "pattern": r"^\d+(MiB|GiB)$"
        },
        "dns": {"type": ["string", "null"]},
        "expiryDays": {"type": ["integer", "null"], "minimum": 0},
        "expiryMonths": {"type": ["integer", "null"], "minimum": 0},
        "expiryHours": {"type": ["integer", "null"], "minimum": 0},
        "expiryMinutes": {"type": ["integer", "null"], "minimum": 0},
        "configFile": {
            "type": "string",
            "pattern": r"^[a-zA-Z0-9_-]+\.conf$"
        }
    },
    "required": ["peerName"],
    "additionalProperties": False
}


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "running"}), 200

@app.route('/get-api-keys', methods=['GET'])
def obtain_api_keys():
    api_data = load_file(API_FILE)
    if "api_keys" in api_data:
        decrypted_keys = [cipher.decrypt(key.encode()).decode() for key in api_data["api_keys"]]
        return jsonify({"api_keys": decrypted_keys})
    return jsonify({"api_keys": []})


def create_secret_key():
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        secret_key = Fernet.generate_key()
        with open(SECRET_KEY_FILE, "wb") as key_file:
            key_file.write(secret_key)
        return secret_key
    
SECRET_KEY = create_secret_key()
cipher = Fernet(SECRET_KEY)


def load_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    return {}


def save_file(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file)


@app.route("/get-telegram-config", methods=["GET"])
def obtain_telegram_config():
    try:
        default_config = {
    "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "api_base_url": "http://localhost:8080",
    "api_key": "YOUR_API_KEY"
    }

        config_dir = os.path.dirname(TELEGRAM_CONFIG_JSON)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            print(f"Created directory for config: {config_dir}")

        if not os.path.exists(TELEGRAM_CONFIG_JSON) or os.stat(TELEGRAM_CONFIG_JSON).st_size == 0:
            with open(TELEGRAM_CONFIG_JSON, "w") as json_file:
                json.dump(default_config, json_file, indent=4)
                os.chmod(TELEGRAM_CONFIG_JSON, 0o644)
            print(f"Config file created with default values at {TELEGRAM_CONFIG_JSON}.")

        with open(TELEGRAM_CONFIG_JSON, "r") as json_file:
            json_config = json.load(json_file)
            bot_token = json_config.get("bot_token", "")
            base_url = json_config.get("base_url", "")
            api_key = json_config.get("api_key", "")

        return jsonify({
            "bot_token": bot_token,
            "base_url": base_url,
            "api_key": api_key
        })

    except json.JSONDecodeError as e:
        print(f"JSON decoding error in {TELEGRAM_CONFIG_JSON}: {e}")
        with open(TELEGRAM_CONFIG_JSON, "w") as json_file:
            json.dump(default_config, json_file, indent=4)
            os.chmod(TELEGRAM_CONFIG_JSON, 0o644)
        return jsonify({"error": "Config file was invalid and has been reset.", "details": str(e)}), 500

    except Exception as e:
        print(f"error in loading config.json: {e}")
        return jsonify({"error": "Couldn't load bot config.", "details": str(e)}), 500



telegram_install_progress = 0
telegram_installing = False    
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_telegram.json")

def update_progress(progress, message):
    global telegram_installing
    progress_data = {
        "progress": progress,
        "message": message,
        "installing": telegram_installing
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress_data, f)

def run_telegram_install_script(language="en"):
    global telegram_installing
    telegram_installing = True
    update_progress(0, "Starting installation.")

    base_path = os.path.dirname(os.path.abspath(__file__))
    script_name = "install_telegram.sh" if language == "en" else "install_telegram-fa.sh"
    script_path = os.path.join(base_path, script_name)

    try:
        if not os.path.exists(script_path):
            update_progress(0, f"Script not found: {script_path}")
            raise FileNotFoundError(f"Script not found: {script_path}")

        if not re.match(r'^[a-zA-Z0-9_-]+\.sh$', script_name):
            raise ValueError(f"Wrong script name detected: {script_name}")

        if not script_path.startswith(base_path):
            raise ValueError("Wrong script path detected.")

        if not os.path.isfile(script_path):
            raise ValueError(f"Path is not a file: {script_path}")

        resolved_script_path = os.path.abspath(script_path)

        os.chmod(resolved_script_path, 0o700)

        result = subprocess.run([resolved_script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            update_progress(0, f"Script failed: {result.stderr}")
            raise Exception(f"Script failed with error: {result.stderr}")

        update_progress(100, "Installation completed successfully.")

    except Exception as e:
        update_progress(0, f"Installation failed: {e}")
    finally:
        telegram_installing = False
        update_progress(100, "Installation process finalized.")

@app.route("/install-telegram-fa", methods=["POST"])
def install_telegram_fa():
    threading.Thread(target=run_telegram_install_script, args=("fa",)).start()
    return jsonify({"message": "Persian installation started.", "status": "installing"})


@app.route("/telegram-install-progress", methods=["GET"])
def telegram_install_progress():
    try:
        with open(PROGRESS_FILE, "r") as f:
            progress_data = json.load(f)
            return jsonify(progress_data)
    except FileNotFoundError:
        return jsonify({"progress": 0, "message": "No progress data found.", "installing": False})

@app.route("/install-telegram-en", methods=["POST"])
def install_telegram_en():
    threading.Thread(target=run_telegram_install_script, args=("en",)).start()
    return jsonify({"message": "English installation started.", "status": "installing"})


@app.route("/start-telegram", methods=["POST"])
def start_telegram():
    language = session.get("language", "en")
    service_name = "telegram-bot-en.service" if language == "en" else "telegram-bot-fa.service"

    try:
        sanitized_service_name = sanitize_service_name(service_name)
        if not sanitized_service_name.startswith("telegram-bot-"):
            raise ValueError("Wrong service name. Must start with 'telegram-bot-'.")
        
        subprocess.run(
            ["systemctl", "start", sanitized_service_name],  
            check=True, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        return jsonify({"message": f"{sanitized_service_name} started successfully.", "status": "running"})

    except subprocess.CalledProcessError as e:
        return jsonify({
            "message": "Start failed.",
            "error": str(e),
            "stderr": e.stderr
        }), 500
    except ValueError as e:
        return jsonify({"message": "Wrong service name.", "error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "message": "Start failed.",
            "error": str(e)
        }), 500

@app.route("/stop-telegram", methods=["POST"])
def stop_telegram():
    language = session.get("language", "en")
    service_name = "telegram-bot-en.service" if language == "en" else "telegram-bot-fa.service"

    try:
        sanitized_service_name = sanitize_service_name(service_name)
        if not sanitized_service_name.startswith("telegram-bot-"):
            raise ValueError("Wrong service name. Must start with 'telegram-bot-'.")
        
        subprocess.run(
            ["systemctl", "stop", sanitized_service_name],  
            check=True,  
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        return jsonify({"message": f"{sanitized_service_name} stopped successfully.", "status": "stopped"})

    except subprocess.CalledProcessError as e:
        return jsonify({
            "message": "Stop failed.",
            "error": str(e),
            "stderr": e.stderr
        }), 500
    except ValueError as e:
        return jsonify({"message": "Wrong service name.", "error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "message": "Stop failed.",
            "error": str(e)
        }), 500



def sanitize_service_name(service_name):

    service_name = re.sub(r'[^a-zA-Z0-9_.-]', '', service_name)
    return service_name


@app.route("/uninstall-telegram", methods=["POST"])
def uninstall_telegram():
    language = session.get("language", "en")
    service_name = "telegram-bot-en.service" if language == "en" else "telegram-bot-fa.service"
    service_file = f"/etc/systemd/system/{service_name}"

    try:
        sanitized_service_name = sanitize_service_name(service_name)
        print(f"Sanitized service name: {sanitized_service_name}")  

        if not sanitized_service_name.startswith("telegram-bot-"):
            raise ValueError("Wrong service name. Must start with 'telegram-bot-'.")
        
        subprocess.run(
            ["systemctl", "stop", sanitized_service_name], 
            check=True,  
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        subprocess.run(
            ["systemctl", "disable", sanitized_service_name],  
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if os.path.exists(service_file):
            os.remove(service_file)
            print(f"Service file {service_file} removed successfully.")
        else:
            print(f"Service file {service_file} does not exist.")

        subprocess.run(
            ["systemctl", "daemon-reload"],  
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        return jsonify({"message": f"{sanitized_service_name} uninstalled successfully.", "status": "uninstalled"})

    except subprocess.CalledProcessError as e:
        return jsonify({
            "message": "Uninstallation failed.",
            "error": str(e),
            "stderr": e.stderr
        }), 500
    except ValueError as e:
        return jsonify({"message": "Wrong service name.", "error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "message": "Uninstallation failed.",
            "error": str(e)
        }), 500
    
@app.route("/get-admin-chat-ids", methods=["GET"])
def get_admin_chat_ids():
    try:
        if not os.path.exists(TELEGRAM_CONFIG_FILE):
            return jsonify({"error": "Config file not found"}), 404

        with open(TELEGRAM_CONFIG_FILE, "r") as yaml_file:
            yaml_config = yaml.safe_load(yaml_file) or {}
            encrypted_chat_ids = yaml_config.get("admin_chat_ids", [])
            admin_chat_ids = [cipher.decrypt(chat_id.encode()).decode() for chat_id in encrypted_chat_ids]

        return jsonify({"admin_chat_ids": admin_chat_ids})
    except Exception as e:
        print(f"Error loading telegram.yaml: {e}")
        return jsonify({"error": "Couldn't load admin chat IDs.", "details": str(e)}), 500


    
@app.route("/bot-status", methods=["GET"])
def bot_status():
    try:
        language = session.get("language", "en")
        service_name = "telegram-bot-en.service" if language == "en" else "telegram-bot-fa.service"
        service_file = f"/etc/systemd/system/{service_name}"

        if not os.path.exists(service_file):
            return jsonify({"status": "uninstalled"})

        sanitized_service_name = sanitize_service_name(service_name)

        if not sanitized_service_name.startswith("telegram-bot-"):
            raise ValueError("Wrong service name detected.")

        safe_service_name = sanitized_service_name

        command = ["systemctl", "is-active", safe_service_name]  
        result = run_command(command)  

        
        if result.strip() == "active":
            return jsonify({"status": "running"})
        else:
            return jsonify({"status": "stopped"})
    except FileNotFoundError:
        return jsonify({"status": "error", "error": "systemctl not found"}), 500
    except subprocess.CalledProcessError as e:
       
        return jsonify({
            "status": "error",
            "error": "systemctl error",
            "stderr": e.stderr  
        }), 500
    except ValueError as e:
        return jsonify({"status": "error", "error": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500



    
@app.route('/create-api-key', methods=['POST'])
def create_api_key():
    api_data = load_file(API_FILE)
    api_key = os.urandom(16).hex() 
    encrypted_key = cipher.encrypt(api_key.encode()).decode() 

    if "api_keys" not in api_data:
        api_data["api_keys"] = []
    
    api_data["api_keys"].append(encrypted_key)  
    save_file(API_FILE, api_data)  

    return jsonify({"api_key": api_key}) 


@app.route('/delete-api-key/<int:index>', methods=['DELETE'])
def delete_api_key(index):
    api_data = load_file(API_FILE)
    if "api_keys" in api_data and 0 <= index < len(api_data["api_keys"]):
        del api_data["api_keys"][index] 
        save_file(API_FILE, api_data)  
        return jsonify({"message": "API Key deleted successfully"})
    return jsonify({"error": "API Key not found"}), 404


@app.route("/save-telegram-config", methods=["POST"])
def save_telegram_config():
    try:
        data = request.json

        bot_token = data.get("bot_token")
        base_url = data.get("base_url")
        api_key = data.get("api_key")
        admin_chat_ids = data.get("admin_chat_ids")  

        if not bot_token or not base_url or not api_key or not admin_chat_ids:
            return jsonify({"message": "All fields are required!"}), 400

        encrypted_chat_ids = [cipher.encrypt(chat_id.encode()).decode() for chat_id in admin_chat_ids]

        json_config = {
            "bot_token": bot_token,
            "base_url": base_url,
            "api_key": api_key,
        }
        with open(TELEGRAM_CONFIG_JSON, "w") as json_file:
            json.dump(json_config, json_file, indent=4)

        yaml_config = {"admin_chat_ids": encrypted_chat_ids}
        with open(TELEGRAM_CONFIG_FILE, "w") as yaml_file:
            yaml.safe_dump(yaml_config, yaml_file)

        return jsonify({"message": "Telegram config saved successfully!"})

    except Exception as e:
        return jsonify({"message": "Couldn't save config.", "error": str(e)}), 500




new_backup_created = False

def delete_old_backup(backup_dir: str, backup_prefix: str):
    try:
        backups = [f for f in os.listdir(backup_dir) if f.startswith(backup_prefix)]
        if backups:
            oldest_backup_path = os.path.join(backup_dir, backups[0])
            os.remove(oldest_backup_path)
            logging.info(f"Deleted old backup: {oldest_backup_path}")
    except Exception as e:
        logging.error(f"Couldn't delete old backup: {e}")


def create_automated_backup():
    global new_backup_created
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        logging.info(f"Creating backup with timestamp: {timestamp}")

        wireguard_backup_dir = os.path.join(BACKUP_DIR, "wireguard")
        os.makedirs(wireguard_backup_dir, exist_ok=True)
        if os.path.exists(WIREGUARD_CONFIG_DIR):
            for file in os.listdir(WIREGUARD_CONFIG_DIR):
                if file.endswith(".conf"): 
                    src_path = os.path.join(WIREGUARD_CONFIG_DIR, file)
                    dest_path = os.path.join(wireguard_backup_dir, f"{file}_{timestamp}")
                    
                    delete_old_backup(wireguard_backup_dir, file)
                    
                    shutil.copy2(src_path, dest_path)
            logging.info(f"Wireguard configs backed up to {wireguard_backup_dir}")

        db_backup_dir = os.path.join(BACKUP_DIR, "db")
        os.makedirs(db_backup_dir, exist_ok=True)
        for file in os.listdir(DB_DIR):
            if file.endswith(".json"):
                src_path = os.path.join(DB_DIR, file)
                dest_path = os.path.join(db_backup_dir, f"{file}_{timestamp}")
                
                delete_old_backup(db_backup_dir, file)
                
                shutil.copy2(src_path, dest_path)
        logging.info(f"Database files backed up to {db_backup_dir}")

        new_backup_created = True
        logging.info("Automated backup created and notification flag set.")

    except Exception as e:
        logging.error(f"Couldn't create automated backup: {e}")


@app.route("/api/backup-status", methods=["GET"])
def check_backup_status():
    global new_backup_created
    if new_backup_created:
        new_backup_created = False 
        return jsonify({"new_backup": True})
    return jsonify({"new_backup": False})


def obtain_peers_file(config_name: str) -> str:
    base_name = config_name.split(".")[0] 
    return os.path.join(DB_DIR, f"{base_name}.json") 


def setup_logging(debug_mode):

    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wireguard.log")

    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    log_format = "%(asctime)s [%(levelname)s] %(message)s"

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(logging.Formatter(log_format))

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(log_format))

    logger = logging.getLogger()
    logger.handlers.clear()  

    if debug_mode:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    else:
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)

        logging.getLogger("werkzeug").setLevel(logging.ERROR)


def load_users():
    with open(db_file, "r") as file:
        return json.load(file)

def save_users(users):
    with open(db_file, "w") as file:
        json.dump(users, file, indent=4)

@app.route('/api/stuff', methods=['GET'])
def track_statuses():
    def check_xray_status():
        try:
            command = ["sudo", "systemctl", "is-active", "xray"]

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip() == 'active'
        except subprocess.CalledProcessError:
            return False
        except Exception:
            return False

    def check_warp_status():
        try:
            interfaces = psutil.net_if_addrs()
            for interface in interfaces:
                if "wgcf" in interface:
                    return True
            return False
        except Exception:
            return False

    xray_status = check_xray_status()
    warp_status = check_warp_status()

    return jsonify({"warp": warp_status, "xray": xray_status})


@app.route("/api/web-config", methods=["GET"])
def obtain_web_config():
    try:
        print("Returning web config:", config["flask"])  
        return jsonify({
            "port": config["flask"]["port"],
            "tls": config["flask"]["tls"]
        }), 200
    except Exception as e:
        print(f"error in /api/web-config: {e}")  
        return jsonify({"error": f"Couldn't load web config: {str(e)}"}), 500

@app.before_request
def set_default_language():
    if "language" not in session:
        language = request.cookies.get("language", "en")
        session["language"] = language

@app.route("/")
def index():
    if "username" not in session:
        return redirect("/login")
    return redirect("/home")

@app.route("/home")
def home():
    if "username" not in session or session["username"] not in load_users():
        flash("Please log in to access the dashboard.", "error")
        return redirect("/login")

    language = session.get('language', 'en')
    template_name = "index-fa.html" if language == "fa" else "index.html"
    return render_template(template_name, username=session["username"])



def load_username_from_db():
    try:
        with open(DB_FILE, 'r') as file:
            users = json.load(file)
            if users:
                return next(iter(users.keys()), "Guest")
    except (FileNotFoundError, json.JSONDecodeError):
        return "Guest"  

@app.route('/logout-user', methods=['GET'])
def logout_user():

    print("Session before logout:", session)  

    session.clear()
    print("Session after logout:", session)  

    response = make_response(redirect('/login'))
    response.delete_cookie('username')  

    return response


@app.context_processor
def inject_username():
    return {'username': load_username_from_db()}

@app.route("/peers")
def peers_list():
    if "username" not in session or session["username"] not in load_users():
        flash("Please log in to access peers.", "error")
        return redirect("/login")
    
    language = session.get('language', 'en')
    template_name = "peers-fa.html" if language == "fa" else "peers.html"
    return render_template(template_name)


@app.route("/telegram")
def api():
    if "username" not in session or session["username"] not in load_users():
        flash("Please log in to access peers.", "error")
        return redirect("/login")
    
    language = session.get('language', 'en')
    template_name = "telegram-fa.html" if language == "fa" else "telegram.html"
    return render_template(template_name)


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    language = session.get('language', 'en')
    template_name = "login-fa.html" if language == "fa" else "login.html"

    if request.method == "GET":
        if not os.path.exists(db_file):
            flash("User database not found. Please register.", "error")
            return redirect("/register")

        users = load_users()
        if not users:
            flash("No users found. Please register.", "error")
            return redirect("/register")

        username = request.cookies.get("username")
        if username and username in users:
            session["username"] = username
            flash("Welcome back!", "success")
            return redirect("/home")
        return render_template(template_name)

    username = request.form.get("username")
    password = request.form.get("password")
    remember = request.form.get("remember")  

    if not username or not password:
        flash("Username and password are required!", "error")
        return redirect("/login")

    users = load_users()

    if username in users and bcrypt.check_password_hash(users[username], password):
        session["username"] = username
        flash("Login successful!", "success")
        response = make_response(redirect("/home"))
        if remember == "yes":
            response.set_cookie("username", username, max_age=30 * 24 * 60 * 60) 
        return response

    flash("Wrong username or password!", "error")
    return redirect("/login")


@app.route("/settings")
def settings():
    if "username" not in session:
        flash("Please log in to access settings.", "error")
        return redirect("/login")
    
    language = session.get('language', 'en')
    template_name = "settings-fa.html" if language == "fa" else "settings.html"
    return render_template(template_name)


@app.route('/api/flask-config', methods=['GET'])
def obtain_flask_config():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.yaml")

        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        flask_config = config.get("flask", {})
        if not flask_config:
            return jsonify({"message": "Flask config not found in config.yaml"}), 404

        return jsonify({
            "port": flask_config.get("port", 5000),
            "tls": flask_config.get("tls", False)
        })
    except FileNotFoundError:
        return jsonify({"message": "config.yaml file not found."}), 404
    except Exception as e:
        return jsonify({"message": f"error in retrieving Flask config: {str(e)}"}), 500


@app.route("/api/update-flask-config", methods=["POST"])
def update_flask_config():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.yaml")

        data = request.json
        port = data.get("port")
        tls = data.get("tls")
        cert_path = data.get("cert_path")
        key_path = data.get("key_path")

        if port is None or tls is None:
            return jsonify({"message": "Both port and TLS settings are required."}), 400

        if not isinstance(port, int) or port < 1 or port > 65535:
            return jsonify({"message": "Port must be an integer between 1 and 65535."}), 400

        if not isinstance(tls, bool):
            return jsonify({"message": "TLS setting must be a boolean (true/false)."}), 400

        try:
            with open(config_path, "r") as file:
                config = yaml.safe_load(file)
                existing_port = config.get("flask", {}).get("port")
        except FileNotFoundError:
            config = {"flask": {}, "wireguard": {}}
            existing_port = None

        config["flask"]["port"] = port
        config["flask"]["tls"] = tls

        if tls:
            if not cert_path or not key_path:
                return jsonify({"message": "TLS is enabled but cert_path or key_path not provided."}), 400
            config["flask"]["cert_path"] = cert_path
            config["flask"]["key_path"] = key_path
        else:
            config["flask"]["cert_path"] = ""
            config["flask"]["key_path"] = ""

        with open(config_path, "w") as file:
            yaml.dump(config, file, default_flow_style=False)

        response = {
            "message": "Flask config updated successfully.",
            "port": port,
            "tls": tls
        }

        if existing_port != port:
            try:
                service_name = "wireguard-panel.service"

                subprocess.run(
                    ["systemctl", "restart", service_name],  
                    check=True, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True  
                )
                response["service_restart"] = "wireguard-panel.service restarted successfully."
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() if e.stderr else str(e)
                return jsonify({
                    "message": "Flask config updated, but failed to restart Wireguard-panel.service.",
                    "error": error_msg
                }), 500

        return jsonify(response), 200

    except yaml.YAMLError as yaml_error:
        return jsonify({"message": f"YAML error while updating config: {yaml_error}"}), 500
    except Exception as e:
        return jsonify({"message": f"error in updating Flask config: {e}"}), 500


@app.route('/api/update-user', methods=['POST'])
def update_user():

    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to update your account.'}), 403

    data = request.json
    new_username = data.get('username')
    new_password = data.get('password')

    if not new_username or not new_password:
        return jsonify({'error': 'Both username and password are required.'}), 400

    try:
        with open(DB_FILE, "r") as f:
            users = json.load(f)

        current_user = session['username']

        if new_username != current_user and new_username in users:
            return jsonify({'error': 'The new username already exists!'}), 400

        users.pop(current_user, None)

        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        users[new_username] = hashed_password

        with open(DB_FILE, "w") as f:
            json.dump(users, f, indent=4)

        session['username'] = new_username

        return jsonify({'message': 'Username and password updated successfully!'}), 200

    except Exception as e:
        app.logger.error(f"error in updating user: {e}")
        return jsonify({'error': 'An error occurred while updating the user.'}), 500


@app.route('/api/update-wireguard-config', methods=['POST'])
def update_wireguard_config():
    data = request.json
    config_name = data.get('config')
    port = data.get('port')
    mtu = data.get('mtu')
    dns = data.get('dns')

    if not config_name:
        return jsonify({"message": "Config name is required"}), 400

    config_path = f"/etc/wireguard/{config_name}"
    if not config_name.endswith(".conf"):
        config_path += ".conf"

    if not os.path.isfile(config_path):
        return jsonify({"message": f"Configuration file '{config_path}' not found"}), 404

    try:
        with open(config_path, "r") as file:
            config_data = file.readlines()

        updated_config = []
        for line in config_data:
            if port and line.startswith("ListenPort"):
                updated_config.append(f"ListenPort = {port}\n")
            elif port and "PostUp = iptables -I INPUT -p udp --dport" in line:
                updated_config.append(f"PostUp = iptables -I INPUT -p udp --dport {port} -j ACCEPT\n")
            elif port and "PostDown = iptables -D INPUT -p udp --dport" in line:
                updated_config.append(f"PostDown = iptables -D INPUT -p udp --dport {port} -j ACCEPT\n")
            elif mtu and line.startswith("MTU"):
                updated_config.append(f"MTU = {mtu}\n")
            elif dns and line.startswith("DNS"):
                updated_config.append(f"DNS = {dns}\n")
            else:
                updated_config.append(line)

        with open(config_path, "w") as file:
            file.writelines(updated_config)

        return jsonify({"message": "Wireguard config updated successfully!"})
    except Exception as e:
        return jsonify({"message": f"Couldn't update Wireguard config: {str(e)}"}), 500


@app.route('/api/user-info', methods=['GET'])
def obtain_user_info():
    try:
        current_user = session.get('username')
        if not current_user:
            return jsonify({"error": "User not logged in"}), 401
        return jsonify({"username": current_user})
    except Exception as e:
        return jsonify({"error": f"Couldn't load user info: {e}"}), 500

@app.route("/api/backups", methods=["GET"])
def list_manual_backups():
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backups = [
            f for f in os.listdir(BACKUP_DIR)
            if f.startswith("manual_") and f.endswith(".backup.zip")
        ]
        return jsonify(backups=backups)
    except Exception as e:
        logging.error(f"Couldn't list backups: {e}")
        return jsonify(error=f"Couldn't list backups: {e}"), 500
   

@app.route("/api/create-backup", methods=["POST"])
def create_backup():
    try:
        backup_name = f"manual_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.backup.zip"
        backup_path = os.path.join(BACKUP_DIR, backup_name)

        temp_dir = tempfile.mkdtemp()

        try:
            wireguard_backup_dir = os.path.join(temp_dir, "wireguard")
            os.makedirs(wireguard_backup_dir, exist_ok=True)
            if os.path.exists(WIREGUARD_CONFIG_DIR):
                for file in os.listdir(WIREGUARD_CONFIG_DIR):
                    if file.endswith(".conf"):
                        shutil.copy2(
                            os.path.join(WIREGUARD_CONFIG_DIR, file),
                            os.path.join(wireguard_backup_dir, file),
                        )

            db_backup_dir = os.path.join(temp_dir, "db")
            if os.path.exists(db_backup_dir):
                shutil.rmtree(db_backup_dir) 
            shutil.copytree(DB_DIR, db_backup_dir)
            shutil.make_archive(backup_path.replace(".zip", ""), 'zip', temp_dir)

        finally:
            shutil.rmtree(temp_dir)

        return jsonify(message=f"Backup created successfully as {backup_name}.")

    except Exception as e:
        logging.error(f"error in creating backup: {e}")
        return jsonify(error=f"Couldn't create backup: {e}"), 500


    
@app.route("/api/restore-automated-backup", methods=["POST"])
def restore_auto_backup():
    try:
        data = request.json
        folder = data.get("folder")  
        backup_name = data.get("backupName")
        if not folder or not backup_name:
            return jsonify(error="Folder and backup name are required."), 400

        backup_dir = os.path.join(BACKUP_DIR, folder)
        backup_path = os.path.join(backup_dir, backup_name)
        if not os.path.exists(backup_path):
            return jsonify(error="Backup not found."), 404

        if folder == "wireguard":
            base_name = os.path.splitext(backup_name.split("_")[0])[0]
            dest_path = os.path.join(WIREGUARD_CONFIG_DIR, f"{base_name}.conf")
            shutil.copy2(backup_path, dest_path)
        elif folder == "db":
            base_name = os.path.splitext(backup_name.split("_")[0])[0]
            dest_path = os.path.join(DB_DIR, f"{base_name}.json")
            shutil.copy2(backup_path, dest_path)
        else:
            return jsonify(error="Wrong folder specified."), 400

        return jsonify(message=f"Backup {backup_name} restored successfully.")
    except Exception as e:
        logging.error(f"Couldn't restore automated backup: {e}")
        return jsonify(error=f"Couldn't restore automated backup: {e}"), 500


@app.route("/api/delete-backup", methods=["DELETE"])
def delete_backup():
    try:
        backup_name = request.args.get("name")
        folder = request.args.get("folder") 

        print(f"Received backup_name: {backup_name}, folder: {folder}")

        if not backup_name:
            return jsonify(error="Backup name is required."), 400

        if folder == "wireguard":
            backup_dir = os.path.join(BACKUP_DIR, "wireguard")
        elif folder == "db":
            backup_dir = os.path.join(BACKUP_DIR, "db")
        elif folder == "root" or folder is None:  
            backup_dir = BACKUP_DIR
        else:
            return jsonify(error="Wrong folder specified."), 400

        backup_path = os.path.join(backup_dir, backup_name)

        if not os.path.exists(backup_path):
            return jsonify(error="Backup not found."), 404

        os.remove(backup_path)
        return jsonify(message=f"Backup {backup_name} deleted successfully.")
    except Exception as e:
        logging.error(f"error in deleting backup: {e}")
        return jsonify(error=f"Couldn't delete backup: {e}"), 500

@app.route("/api/restore-backup", methods=["POST"])
def restore_backup():
    try:
        data = request.json
        backup_name = data.get("backupName")
        if not backup_name:
            return jsonify(error="Backup name is required."), 400

        if not re.match(r"^[\w\-]+\.backup\.zip$", backup_name):
            return jsonify(error="Wrong backup name."), 400

        backup_path = os.path.join(BACKUP_DIR, backup_name)
        if not os.path.exists(backup_path):
            return jsonify(error="Backup not found."), 404

        temp_dir = tempfile.mkdtemp()
        try:
            logging.info(f"Extracting backup {backup_name} to temporary directory {temp_dir}")
            shutil.unpack_archive(backup_path, temp_dir, "zip")

            wireguard_dir = os.path.join(temp_dir, "wireguard")
            if os.path.exists(wireguard_dir):
                os.makedirs(WIREGUARD_CONFIG_DIR, exist_ok=True)
                for file in os.listdir(wireguard_dir):
                    if file.endswith(".conf"):  
                        src = os.path.join(wireguard_dir, file)
                        dest = os.path.join(WIREGUARD_CONFIG_DIR, file)
                        try:
                            shutil.copy2(src, dest)
                            logging.info(f"Restored Wireguard config: {file} -> {WIREGUARD_CONFIG_DIR}")
                        except Exception as e:
                            logging.error(f"error in restoring Wireguard config {file}: {e}")
                            return jsonify(error=f"Couldn't restore Wireguard config: {file}"), 500

            db_dir = os.path.join(temp_dir, "db")
            if os.path.exists(db_dir):
                for file in os.listdir(db_dir):
                    if file.endswith(".json"):  
                        src = os.path.join(db_dir, file)
                        dest = os.path.join(DB_DIR, file)
                        try:
                            shutil.copy2(src, dest)
                            logging.info(f"Restored database file: {file} -> {DB_DIR}")
                        except Exception as e:
                            logging.error(f"error in restoring database file {file}: {e}")
                            return jsonify(error=f"Couldn't restore database file: {file}"), 500

            return jsonify(message=f"Backup {backup_name} restored successfully.")
        except shutil.ReadError as e:
            logging.error(f"Backup file is not a valid archive: {e}")
            return jsonify(error="Backup file is not a valid archive."), 400
        except Exception as e:
            logging.error(f"Couldn't restore backup: {e}")
            return jsonify(error=f"Couldn't restore backup: {e}"), 500
        finally:
            shutil.rmtree(temp_dir)  
            logging.info(f"Temporary directory {temp_dir} removed after restore.")
    except Exception as e:
        logging.error(f"error in restoring backup: {e}")
        return jsonify(error=f"Couldn't restore backup: {e}"), 500

@app.route("/api/auto-backups", methods=["GET"])
def list_auto_backups():
    folder = request.args.get("folder")
    if folder not in ["wireguard", "db"]:
        return jsonify(error="Wrong folder specified."), 400

    backup_dir = os.path.join(BACKUP_DIR, folder)

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True) 
        logging.info(f"Created missing backup folder: {backup_dir}")

    backups = [f for f in os.listdir(backup_dir) if os.path.isfile(os.path.join(backup_dir, f))]

    if not backups:
        return jsonify(backups=[])

    backups.sort(reverse=True)  
    
    return jsonify(backups=backups)



@app.route("/backups", methods=["GET"])
def backups_page():
    if "username" not in session:
        flash("Please log in to access backups.", "error")
        return redirect("/login")

    language = session.get('language', 'en') 
    template_name = "backups-fa.html" if language == "fa" else "backups.html"
    return render_template(template_name)


@app.route("/api/download-backup", methods=["GET"])
def download_backup():
    backup_name = request.args.get("name")
    if not backup_name:
        return jsonify(error="Backup name is required."), 400

    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if not os.path.exists(backup_path):
        return jsonify(error="Backup not found."), 404

    try:
        return send_from_directory(BACKUP_DIR, backup_name, as_attachment=True)
    except Exception as e:
        return jsonify(error=f"Couldn't download backup: {e}"), 500

    
@app.route("/api/restore-automated-backup", methods=["POST"])
def restore_automated_backup():
    try:
        data = request.json
        folder = data.get("folder") 
        if folder not in ["wireguard", "db"]:
            return jsonify(error="Wrong folder specified. Use 'wireguard' or 'db'."), 400

        backup_dir = os.path.join(BACKUP_DIR, folder)
        if not os.path.exists(backup_dir):
            return jsonify(error=f"Backup folder {folder} does not exist."), 404

        if folder == "wireguard":
            for file in os.listdir(backup_dir):
                if file.endswith(".conf"):
                    src_path = os.path.join(backup_dir, file)
                    dest_path = os.path.join(WIREGUARD_CONFIG_DIR, file.split("_")[0])  
                    shutil.copy2(src_path, dest_path)
            logging.info(f"Restored Wireguard configs from {backup_dir}")

        elif folder == "db":
            for file in os.listdir(backup_dir):
                if file.endswith(".json"):
                    src_path = os.path.join(backup_dir, file)
                    dest_path = os.path.join(DB_DIR, file.split("_")[0])  
                    shutil.copy2(src_path, dest_path)
            logging.info(f"Restored database files from {backup_dir}")

        return jsonify(message=f"Backup from {folder} restored successfully.")
    except Exception as e:
        logging.error(f"Couldn't restore automated backup: {e}")
        return jsonify(error=f"Couldn't restore automated backup: {e}"), 500


@app.route("/register", methods=["GET", "POST"])
def register():
    language = session.get('language', 'en') 
    template_name = "register-fa.html" if language == "fa" else "register.html"

    try:
        with open(DB_FILE, "r") as file:
            users = json.load(file)
            if users:  
                flash("Registration is disabled because users already exist.", "error")
                return redirect("/login")
    except (FileNotFoundError, json.JSONDecodeError):
        users = {}

    if request.method == "GET":
        return render_template(template_name)

    username = request.form.get("username")
    password = request.form.get("password")

    if username in users:
        flash("Username already exists!", "error")
        return redirect("/register")

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    users[username] = hashed_password
    save_users(users)

    flash("Registration successful! Please log in.", "success")
    return redirect("/login")


@app.route("/logout")
def logout():
    session.pop("username", None)
    response = make_response(redirect("/login"))
    response.delete_cookie("username") 
    flash("You have been logged out.", "success")
    return response

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("wireguard.log"),  
        logging.StreamHandler()  
    ]
)

class SuppressNoDeviceFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        suppressed_patterns = [
            "No such device",
            "Non-critical error for interface",
            "Unable to access interface: No such device"
            
        ]
        return not any(pattern in message for pattern in suppressed_patterns)

def obtain_disk_usage():
    try:
        total, used, free = shutil.disk_usage("/")
        return {
            "total": f"{total // (1024**3)} GB",
            "used": f"{used // (1024**3)} GB",
            "free": f"{free // (1024**3)} GB",
            "percent": round((used / total) * 100, 2)
        }
    except Exception as e:
        print(f"error in fetching disk usage: {e}")
        return {"total": "N/A", "used": "N/A", "free": "N/A", "percent": "N/A"}

def obtain_system_uptime():

    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_days = int(uptime_seconds // (24 * 3600))
            uptime_hours = int((uptime_seconds % (24 * 3600)) // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)
            return f"{uptime_days}d {uptime_hours}h {uptime_minutes}m"
    except Exception as e:
        print(f"error in fetching uptime: {e}")
        return "N/A"

def calculate_cpu_usage():

    try:
        with open('/proc/stat', 'r') as f:
            lines = f.readlines()

        cpu_line = lines[0] 
        stats = list(map(int, cpu_line.split()[1:]))
        idle_time, total_time = stats[3], sum(stats)

        if not hasattr(calculate_cpu_usage, "last_idle"):
            calculate_cpu_usage.last_idle = idle_time
            calculate_cpu_usage.last_total = total_time

        idle_delta = idle_time - calculate_cpu_usage.last_idle
        total_delta = total_time - calculate_cpu_usage.last_total

        calculate_cpu_usage.last_idle = idle_time
        calculate_cpu_usage.last_total = total_time

        if total_delta == 0:
            return 0.0

        usage_percentage = (1 - idle_delta / total_delta) * 100

        if usage_percentage < 0.01:  
            return 0.01

        return round(usage_percentage, 2) 
    except Exception as e:
        print(f"error in calculating CPU usage: {e}")
        return None

def system_metrics_job():

    try:
        cpu = calculate_cpu_usage()
        ram = psutil.virtual_memory().percent
        disk_usage = obtain_disk_usage()
        uptime = obtain_system_uptime()

        if cpu is None:
            cpu = 0.01

        metrics = {
            "cpu": f"{cpu}%",
            "ram": f"{ram}%",
            "disk": disk_usage,
            "uptime": uptime
        }

        cache.set("metrics", metrics, timeout=9)
    except Exception as e:
        print(f"error in collecting metrics: {e}")


def valid_private_key(key: str) -> bool:
    try:
        decoded = base64.b64decode(key)
        is_valid = len(decoded) == 32
        print(f"Decoded Key Valid: {is_valid}, Length: {len(decoded)}")  
        return is_valid
    except Exception as e:
        print(f"error in validating PrivateKey: {e}")
        return False

@app.route('/api/interface-status', methods=['GET'])
def interface_status():
    try:
        wg_path = "wg"  

        if not os.path.isfile(wg_path) or not os.access(wg_path, os.X_OK):
            return jsonify({"error": f"wg command not found or not executable at {wg_path}"}), 500

        result = subprocess.run(
            [wg_path, "show"],  
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        if result.stdout:
            return jsonify({"status": "up"}), 200
        else:
            return jsonify({"status": "down"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "down", "error": e.stderr}), 200
    except Exception as e:

        print(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

    
def sanitize_input(input_value: str):
    if re.match(r"^[a-zA-Z0-9_-]+$", input_value):
        return input_value
    else:
        raise ValueError(f"Wrong input: {input_value}")

@app.route('/api/toggle-interface', methods=['POST'])
def toggle_interface():
    action = request.args.get('action')
    config_file = request.args.get('config', 'wg0.conf')

    if action not in ['up', 'down']:
        return jsonify(error="Wrong action. Must be 'up' or 'down'."), 400

    interface = config_file.split(".")[0] 
    sanitized_interface = sanitize_input(interface)  

    try:
        wg_quick_path = "wg-quick"  

        command_down = [wg_quick_path, "down", sanitized_interface]
        command_up = [wg_quick_path, "up", sanitized_interface]

        subprocess.run(command_down, check=True, stderr=subprocess.PIPE, text=True)

        subprocess.run(command_up, check=True, stderr=subprocess.PIPE, text=True)

        return jsonify(success=True, message=f"Interface '{sanitized_interface}' has been turned {action}.")

    except subprocess.CalledProcessError as e:
        print(f"error in toggling interface '{sanitized_interface}': {e}")
        return jsonify(success=False, error=e.stderr if e.stderr else str(e)), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500


def hash_out_peer(peer_ip, config_file="wg0.conf"):

    config_path = os.path.join(DB_DIR, config_file)

    try:
        with open(config_path, "r") as file:
            lines = file.readlines()

        updated_lines = []
        skip_block = False
        for line in lines:
            if line.startswith("[Peer]"):
                skip_block = False
            if peer_ip in line:
                skip_block = True  
            if not skip_block:
                updated_lines.append(line)
            else:
                updated_lines.append(f"# {line.strip()}\n")  

        with open(config_path, "w") as file:
            file.writelines(updated_lines)

        print(f"Hashed out peer {peer_ip} in {config_file}")
    except Exception as e:
        print(f"error in hashing out peer {peer_ip} in {config_file}: {e}")

def restart_wireguard_interface(interface="wg0"):
    try:
        sanitized_interface = sanitize_interface_name(interface)

        wg_quick_path = "wg-quick" 
        
        subprocess.run([wg_quick_path, "down", sanitized_interface], check=True)
        subprocess.run([wg_quick_path, "up", sanitized_interface], check=True)
        
        print(f"Restarted Wireguard interface: {sanitized_interface}")
    except subprocess.CalledProcessError as e:
        print(f"error in restarting Wireguard interface {sanitized_interface}: {e}")
    except ValueError as e:
        print(f"Error: {e}")


def recover_from_backup(config_name: str):
    backup_dir = "backups"
    base_name = config_name.split(".")[0]
    backups = [f for f in os.listdir(backup_dir) if f.startswith(base_name)]
    if not backups:
        print(f"No backups found for {config_name}.")
        return []

    backups.sort(reverse=True)
    latest_backup = os.path.join(backup_dir, backups[0])
    try:
        with open(latest_backup, "r") as f:
            print(f"Recovering from backup: {latest_backup}")
            return json.load(f)
    except Exception as e:
        print(f"Couldn't recover from backup {latest_backup}: {e}")
        return []


        
def load_peers_from_json(config_name: str):

    file_path = obtain_peers_file(config_name)
    with json_lock:
        try:
            with open(file_path, "r") as f:
                peers = json.load(f)

            fields_to_remove = ["blocked", "reset"]
            fields_to_add = {
                "last_received_bytes": 0,
                "last_sent_bytes": 0,
            }

            updated = False  

            for peer in peers:
                for field in fields_to_remove:
                    if field in peer:
                        del peer[field]
                        updated = True

                for field, default_value in fields_to_add.items():
                    if field not in peer:
                        peer[field] = default_value
                        updated = True

            if updated:
                save_peers_to_json(config_name, peers)
                print(f"Updated peers in {file_path} (removed fields and added missing fields).")

            return peers

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for {file_path}: {e}. Attempting recovery.")
            return recover_from_backup(config_name)
        except FileNotFoundError:
            return []



def save_peers_to_json(config_name: str, peers):
    file_path = obtain_peers_file(config_name)
    try:
        with open(file_path + '.tmp', "w") as temp_file:
            fcntl.flock(temp_file, fcntl.LOCK_EX)
            json.dump(peers, temp_file, indent=4)
            fcntl.flock(temp_file, fcntl.LOCK_UN)

        shutil.move(file_path + '.tmp', file_path)
        print(f"Successfully saved peers to {file_path}.")
        
    except Exception as e:
        print(f"Couldn't save peers to {file_path}: {e}")


monitor_lock = Lock()  

def monitor_traffic():
    if not monitor_lock.acquire(blocking=False):
        logging.info("monitor_traffic job is already running. Skipping this execution.")
        return  

    try:
        config_files = [f for f in os.listdir(WIREGUARD_CONFIG_DIR) if f.endswith(".conf")]
        interfaces = [config.split(".")[0] for config in config_files]

        def load_peers_with_lock(config_name: str):
            file_path = obtain_peers_file(config_name)
            try:
                with open(file_path, "r") as f:
                    fcntl.flock(f, fcntl.LOCK_SH)
                    peers_data = json.load(f)
                    fcntl.flock(f, fcntl.LOCK_UN)
                return peers_data
            except FileNotFoundError:
                return []
            except json.JSONDecodeError as e:
                logging.error(f"Couldn't decode JSON for {file_path}: {e}")
                return []

        def save_peers_with_lock(config_name: str, peers_data):
            file_path = obtain_peers_file(config_name)
            try:
                with open(file_path + '.tmp', "w") as temp_file:
                    fcntl.flock(temp_file, fcntl.LOCK_EX)
                    json.dump(peers_data, temp_file, indent=4)
                    fcntl.flock(temp_file, fcntl.LOCK_UN)
                
                os.rename(file_path + '.tmp', file_path)
                logging.info(f"Successfully saved peers to {file_path}.")
            except Exception as e:
                logging.error(f"Couldn't save peers to {file_path}: {e}")

        for interface in interfaces:
            try:
                wg_output = subprocess.check_output(["wg", "show", interface, "transfer"], text=True)

                peers = load_peers_with_lock(interface)

                for peer in peers:
                    if peer.get("config") != f"{interface}.conf":
                        continue

                    try:
                        ip_address(peer["peer_ip"])  
                    except ValueError:
                        logging.warning(f"Wrong IP address for peer: {peer['peer_name']} - {peer['peer_ip']}")
                        continue

                    peer_ip = peer["peer_ip"]
                    limit_bytes = convert_to_bytes(peer["limit"]) 

                    for line in wg_output.splitlines():
                        columns = line.split("\t")
                        if len(columns) >= 3 and columns[0] == peer["public_key"]:
                            try:
                                received_bytes = int(columns[1])
                                sent_bytes = int(columns[2])
                            except ValueError:
                                logging.error(f"Wrong transfer stats for peer {peer['peer_name']} in wg_output.")
                                continue

                            last_received = peer.get("last_received_bytes", 0)
                            last_sent = peer.get("last_sent_bytes", 0)

                            if received_bytes < last_received or sent_bytes < last_sent:
                                logging.info(f"Detected reset for peer {peer['peer_name']}.")
                                additional_bytes = received_bytes + sent_bytes
                            else:
                                additional_bytes = (received_bytes - last_received) + (sent_bytes - last_sent)

                            peer["used"] += max(0, additional_bytes)
                            peer["remaining"] = max(0, limit_bytes - peer["used"])
                            peer["last_received_bytes"] = received_bytes
                            peer["last_sent_bytes"] = sent_bytes

                            if peer["used"] >= limit_bytes and not peer.get("monitor_blocked", False):
                                logging.info(f"Blocking {peer['peer_name']} ({peer_ip}) - Exceeded Limit")
                                if add_blackhole_route(peer_ip):  
                                    peer["monitor_blocked"] = True
                                    logging.warning(f"Peer '{peer['peer_name']}' has been blocked due to usage limit.")
                                else:
                                    logging.error(f"Couldn't add blackhole route for peer '{peer['peer_name']}'.")

                save_peers_with_lock(interface, peers)

            except subprocess.CalledProcessError as e:
                if "No such device" in str(e):
                    logging.info(f"No such device for interface {interface}.")
                    continue
                else:
                    logging.warning(f"Non-critical error for interface {interface}: {e}")
            except Exception as e:
                logging.error(f"Unexpected error for interface {interface}: {e}")

    finally:
        monitor_lock.release()



def load_peers_with_lock(config_name):
    try:
        peers_file = obtain_peers_file(config_name)
        with open(peers_file, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH) 
            peers_data = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)  
        return peers_data
    except FileNotFoundError:
        print(f"INFO: {peers_file} not found. Initializing empty peer list.")
        return []  
    except Exception as e:
        print(f"ERROR: Couldn't load peers from {peers_file}: {e}")
        return []  

def save_peers_with_lock(config_name, peers_data):
    try:
        peers_file = obtain_peers_file(config_name)
        with open(peers_file + '.tmp', "w") as temp_file:
            fcntl.flock(temp_file, fcntl.LOCK_EX)  
            json.dump(peers_data, temp_file, indent=4)
            fcntl.flock(temp_file, fcntl.LOCK_UN)  

        os.rename(peers_file + '.tmp', peers_file)
        print(f"INFO: Successfully saved {peers_file} with lock.")
    except Exception as e:
        print(f"ERROR: Couldn't save peers to {peers_file}: {e}")

@app.route("/api/reset-traffic", methods=["POST"])
def reset_traffic():
    try:
        data = request.json
        peer_name = data.get("peerName")
        config_name = data.get("config", "wg0.conf")

        if not peer_name:
            return jsonify(error="Peer name is required."), 400

        with json_lock:  
            peers = load_peers_with_lock(config_name)

            peer = next((p for p in peers if p["peer_name"] == peer_name), None)
            if not peer:
                return jsonify(error=f"Peer '{peer_name}' not found in {config_name}."), 404

            interface = peer["config"].split(".")[0]
            public_key = peer["public_key"]
            peer_ip = peer["peer_ip"]

            reset_peer_traffic(interface, public_key, peer_ip)

            peer["used"] = 0
            peer["remaining"] = convert_to_bytes(peer["limit"])
            peer["last_received_bytes"] = 0
            peer["last_sent_bytes"] = 0
            
            save_peers_with_lock(config_name, peers)

        return jsonify(
            success=True,
            message=f"The traffic statistics for the user '{peer_name}' in the file {config_name} have been reset."
        )
    except Exception as e:
        print(f"error in resetting traffic: {e}")
        return jsonify(error=f"error in resetting traffic: {e}"), 500


@app.route("/api/reset-expiry", methods=["POST"])
def reset_expiry():
    try:
        data = request.json
        peer_name = data.get("peerName")
        config_name = data.get("config", "wg0.conf")  

        if not peer_name:
            return jsonify(error="Peer name is required."), 400

        with json_lock:  
            peers = load_peers_with_lock(config_name)

            peer = next((p for p in peers if p["peer_name"] == peer_name), None)
            if not peer:
                return jsonify(error=f"Peer '{peer_name}' not found in {config_name}."), 404

            expiry_duration = calculate_expiry_duration(peer.get("expiry_time", {}))  
            peer["remaining_time"] = expiry_duration  

            save_peers_with_lock(config_name, peers)

        return jsonify(
            success=True,
            message=f"Expiry time for peer '{peer_name}' in {config_name} has been reset.",
        )
    except Exception as e:
        print(f"error in resetting expiry: {e}")
        return jsonify(error=f"error in resetting expiry: {e}"), 500

def calculate_expiry_duration(expiry_config):

    months = expiry_config.get("months", 0) * 30 * 24 * 60  
    days = expiry_config.get("days", 0) * 24 * 60
    hours = expiry_config.get("hours", 0) * 60
    minutes = expiry_config.get("minutes", 0)
    return months + days + hours + minutes


def sanitize_ip(ip_address: str):
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip_address):
        return ip_address
    else:
        raise ValueError(f"Wrong IP address: {ip_address}")

def add_blackhole_route(peer_ip):
    try:
        sanitized_ip = sanitize_ip(peer_ip)
        ip_path = "ip"

        check_route = subprocess.run(
            [ip_path, "route", "show", f"{sanitized_ip}/32"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if check_route.returncode == 0:
            if f"blackhole {sanitized_ip}" in check_route.stdout:
                print(f"Blackhole route already exists for {sanitized_ip}. Skipping.")
                return True  

            print(f"Existing non-blackhole route found for {sanitized_ip}. Removing it.")
            remove_route = subprocess.run(
                [ip_path, "route", "del", f"{sanitized_ip}/32"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if remove_route.returncode != 0:
                print(f"error in removing existing route for {sanitized_ip}: {remove_route.stderr.strip()}")
        else:
            print(f"no existing route found for {sanitized_ip}. adding blackhole route.")

        add_route = subprocess.run(
            [ip_path, "route", "add", "blackhole", f"{sanitized_ip}/32"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if add_route.returncode == 0:
            print(f"Successfully added blackhole route for {sanitized_ip}")
            return True
        else:
            print(f"error in adding blackhole route for {sanitized_ip}: {add_route.stderr.strip()}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"error in IP route command for {sanitized_ip}: {e}")
        return False
    except ValueError as e:
        print(f"wrong IP address provided: {e}")
        return False


def remove_blackhole_route(peer_ip):
    try:
        sanitized_ip = sanitize_ip(peer_ip)
        ip_path = "ip"

        check_route = subprocess.run(
            [ip_path, "route", "show", f"{sanitized_ip}/32"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if check_route.returncode == 0 and f"dev" in check_route.stdout:
            print(f"Route exists for {sanitized_ip}, but it is not a blackhole route. Not removing.")
            return False

        if check_route.returncode != 0 or f"blackhole {sanitized_ip}" not in check_route.stdout:
            print(f"No blackhole route found for {sanitized_ip}. Nothing to remove.")
            return False

        subprocess.run([ip_path, "route", "del", "blackhole", f"{sanitized_ip}/32"], check=True)
        print(f"Successfully removed blackhole route for {sanitized_ip}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"error in removing blackhole route for {sanitized_ip}: {e}")
        return False
    except ValueError as e:
        print(f"Invalid IP address provided: {e}")
        return False


def bytes_to_readable(bytes_value):

    if bytes_value >= 1024 ** 3:  
        return f"{bytes_value / (1024 ** 3):.2f} GiB"
    elif bytes_value >= 1024 ** 2: 
        return f"{bytes_value / (1024 ** 2):.2f} MiB"
    elif bytes_value >= 1024:  
        return f"{bytes_value / 1024:.2f} KiB"
    else:
        return f"{bytes_value} bytes"


def convert_to_bytes(limit):

    try:
        if isinstance(limit, (int, float)):
            return int(limit)

        size, unit = float(limit[:-3]), limit[-3:].upper()
        unit_mapping = {
            "B": 1,
            "KIB": 1024,
            "MIB": 1024 ** 2,
            "GIB": 1024 ** 3,
        }

        if unit not in unit_mapping:
            raise ValueError(f"Wrong unit: {unit}")
        
        return int(size * unit_mapping[unit])
    except (ValueError, TypeError) as e:
        print(f"error in converting limit to bytes: {e}")
        return 0

@app.route('/api/generate-template', methods=['POST'])
def generate_template():
    try:
        data = request.json
        peer_name = data.get("peer_name")
        config_name = data.get("config_name") 

        if not peer_name or not config_name:
            app.logger.error("Peer name and config name are required.")
            return jsonify({"error": "Peer name and config name are required."}), 400

        db_file_name = f"{config_name}.json" 
        db_path = os.path.join("db", db_file_name)
        if not os.path.exists(db_path):
            app.logger.error(f"Configuration file '{db_file_name}' not found in 'db'.")
            return jsonify({"error": f"Configuration file '{db_file_name}' not found in 'db'."}), 404

        with open(db_path, "r") as db_file:
            peers = json.load(db_file)

        peer = next((p for p in peers if p["peer_name"] == peer_name), None)
        if not peer:
            app.logger.error(f"Peer '{peer_name}' not found in '{db_file_name}'.")
            return jsonify({"error": f"Peer '{peer_name}' not found in '{db_file_name}'"}), 404

        peer_ip = peer.get("peer_ip", "N/A")
        dns = peer.get("dns", "N/A")
        data_limit = peer.get("limit", "N/A")
        expiry_time = peer.get("expiry_time", {})
        expiry = f"{expiry_time.get('months', 0)} months, {expiry_time.get('days', 0)} days"
        persistent_keepalive = peer.get("persistent_keepalive", 25)
        mtu = peer.get("mtu", 1280)
        private_key = peer.get("private_key", "N/A")
        public_key = peer.get("public_key", "N/A")

        server_ip = obtain_server_public_ip()
        wg_config_file = f"{config_name}.conf"
        server_port = server_listen_port(wg_config_file)  

        qr_data = f"""
[Interface]
PrivateKey = {private_key}
Address = {peer_ip}/32
DNS = {dns}
MTU = {mtu}

[Peer]
PublicKey = {public_key}
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = {server_ip}:{server_port}
PersistentKeepalive = {persistent_keepalive}
""".strip()

        app.logger.debug(f"Generated QR Data: {qr_data}")

        return jsonify({
            "peer_name": peer_name,
            "peer_ip": peer_ip,
            "data_limit": data_limit,
            "expiry": expiry,
            "qr_data": qr_data
        }), 200

    except Exception as e:
        app.logger.exception("Couldn't generate template.")
        return jsonify({"error": f"Couldn't generate template: {str(e)}"}), 500




@app.route('/api/delete-template', methods=['POST'])
def delete_template():

    try:
        data = request.json
        filename = data.get("filename")

        if not filename:
            return jsonify({"error": "Filename is required."}), 400

        file_path = os.path.join("static", "generated", filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"message": f"File '{filename}' deleted successfully."}), 200
        else:
            return jsonify({"error": f"File '{filename}' not found."}), 404

    except Exception as e:
        app.logger.error(f"Couldn't delete file: {str(e)}", exc_info=True)
        return jsonify({"error": f"Couldn't delete file: {str(e)}"}), 500


@app.route('/api/bot-peer-details-fa', methods=['GET'])
def get_peer_details_for_bot_fa():
    peer_name = request.args.get('peerName')
    config_name = request.args.get('configName')

    if not peer_name:
        return jsonify({"error": "Peer name is required"}), 400

    if not config_name:
        return jsonify({"error": "Config name is required"}), 400

    try:
        peers = load_peers_from_json(config_name)
        if not peers:
            return jsonify({"error": f"No peers found for config '{config_name}'"}), 404

        peer = next((p for p in peers if p["peer_name"] == peer_name), None)
        if not peer:
            return jsonify({"error": f"Peer '{peer_name}' not found"}), 404

        peer_ip = peer.get('peer_ip', None)
        if not peer_ip:
            return jsonify({"error": "Invalid or missing peer IP"}), 400

        app.logger.debug(f"Peer data: {peer}")

        qr_code = (
            f"[Interface]\n"
            f"PrivateKey = {peer.get('private_key', 'YOUR_PRIVATE_KEY')}\n"
            f"Address = {peer_ip}/32\n"
            f"DNS = {peer.get('dns', '1.1.1.1')}\n\n"
            f"[Peer]\n"
            f"PublicKey = {peer.get('public_key', 'YOUR_PUBLIC_KEY')}\n"
            f"AllowedIPs = 0.0.0.0/0, ::/0\n"
            f"PersistentKeepalive = {peer.get('persistent_keepalive', 25)}"
        )

        created_at_str = peer.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
        created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        expiry_days = peer.get("expiry_days", 30)
        expiry = created_at + timedelta(days=expiry_days)
        now = datetime.now(timezone.utc)

        expiry_human = (
            f"{(expiry - now).days} روز باقی مانده" if (expiry - now).total_seconds() > 0 else "منقضی"
        )

        data_limit = peer.get('limit', 'N/A')
        used_data = peer.get('used', 0)
        remaining_data = peer.get('remaining', 0)

        app.logger.debug(f"Data limit: {data_limit}, Used data: {used_data}, Remaining data: {remaining_data}")

        peer_details = {
            "peer_name": peer_name,
            "peer_ip": peer_ip,
            "qr_code": qr_code,
            "dns": peer.get('dns', '1.1.1.1'),
            "limit": data_limit,
            "used": used_data,
            "remaining": remaining_data,
            "created_at": created_at_str,
            "expiry": expiry.strftime("%Y-%m-%d %H:%M:%S"),
            "expiry_human": expiry_human
        }

        app.logger.debug(f"Peer details to return: {peer_details}")

        return jsonify(peer_details), 200

    except Exception as e:
        app.logger.error(f"error in fetching peer details for bot: {str(e)}")
        return jsonify({"error": "Couldn't fetch peer details"}), 500


@app.route('/api/bot-peer-details', methods=['GET'])
def get_peer_details_for_bot():
    peer_name = request.args.get('peerName')
    config_name = request.args.get('configName')

    if not peer_name:
        return jsonify({"error": "Peer name is required"}), 400

    if not config_name:
        return jsonify({"error": "Config name is required"}), 400

    try:
        peers = load_peers_from_json(config_name)
        if not peers:
            return jsonify({"error": f"No peers found for config '{config_name}'"}), 404

        peer = next((p for p in peers if p["peer_name"] == peer_name), None)
        if not peer:
            return jsonify({"error": f"Peer '{peer_name}' not found"}), 404

        peer_ip = peer.get('peer_ip', None)
        if not peer_ip:
            return jsonify({"error": "Invalid or missing peer IP"}), 400

        app.logger.debug(f"Peer data: {peer}")

        qr_code = (
            f"[Interface]\n"
            f"PrivateKey = {peer.get('private_key', 'YOUR_PRIVATE_KEY')}\n"
            f"Address = {peer_ip}/32\n"
            f"DNS = {peer.get('dns', '1.1.1.1')}\n\n"
            f"[Peer]\n"
            f"PublicKey = {peer.get('public_key', 'YOUR_PUBLIC_KEY')}\n"
            f"AllowedIPs = 0.0.0.0/0, ::/0\n"
            f"PersistentKeepalive = {peer.get('persistent_keepalive', 25)}"
        )

        created_at_str = peer.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
        created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        expiry_days = peer.get("expiry_days", 30)
        expiry = created_at + timedelta(days=expiry_days)
        now = datetime.now(timezone.utc)

        expiry_human = (
            f"{(expiry - now).days} days remaining" if (expiry - now).total_seconds() > 0 else "Expired"
        )

        data_limit = peer.get('limit', 'N/A')
        used_data = peer.get('used', 0)
        remaining_data = peer.get('remaining', 0)

        app.logger.debug(f"Data limit: {data_limit}, Used data: {used_data}, Remaining data: {remaining_data}")

        peer_details = {
            "peer_name": peer_name,
            "peer_ip": peer_ip,
            "qr_code": qr_code,
            "dns": peer.get('dns', '1.1.1.1'),
            "limit": data_limit,
            "used": used_data,
            "remaining": remaining_data,
            "created_at": created_at_str,
            "expiry": expiry.strftime("%Y-%m-%d %H:%M:%S"),
            "expiry_human": expiry_human
        }

        app.logger.debug(f"Peer details to return: {peer_details}")

        return jsonify(peer_details), 200

    except Exception as e:
        app.logger.error(f"error in fetching peer details for bot: {str(e)}")
        return jsonify({"error": "Couldn't fetch peer details"}), 500
    
@app.route("/api/block-peer", methods=["POST"])
def block_peer():
    try:
        data = request.json
        peer_name = data.get("peerName")
        config_name = data.get("config", "wg0.conf")

        if not peer_name:
            return jsonify(error="Peer name is required."), 400

        with json_lock:  
            peers = load_peers_with_lock(config_name)  

            peer = next((p for p in peers if p["peer_name"] == peer_name), None)
            if not peer:
                return jsonify(error=f"Peer '{peer_name}' not found in {config_name}."), 404

            if peer.get("monitor_blocked", False) and peer.get("expiry_blocked", False):
                return jsonify(
                    success=True,
                    message=f"Peer {peer_name} in {config_name} is already blocked."
                )

            print(f"Blocking IP: {peer['peer_ip']} for {config_name}")
            success = add_blackhole_route(peer["peer_ip"])
            if not success:
                return jsonify(error=f"Couldn't block peer {peer_name} in {config_name}."), 500

            peer["monitor_blocked"] = True
            peer["expiry_blocked"] = True

            save_peers_with_lock(config_name, peers)

        return jsonify(
            success=True,
            blocked=True,
            message=f"Peer {peer_name} in {config_name} has been blocked."
        )
    except Exception as e:
        print(f"error in blocking peer: {e}")
        return jsonify(error=str(e)), 500


@app.route("/api/unblock-peer", methods=["POST"])
def unblock_peer():
    try:
        data = request.json
        peer_name = data.get("peerName")
        config_name = data.get("config", "wg0.conf")

        if not peer_name:
            return jsonify(error="Peer name is required."), 400

        with json_lock:  
            peers = load_peers_with_lock(config_name)  

            peer = next((p for p in peers if p["peer_name"] == peer_name), None)
            if not peer:
                return jsonify(error=f"Peer '{peer_name}' not found in {config_name}."), 404

            if not peer.get("monitor_blocked", False) and not peer.get("expiry_blocked", False):
                return jsonify(
                    success=True,
                    message=f"Peer {peer_name} in {config_name} is already unblocked."
                )

            print(f"Unblocking IP: {peer['peer_ip']} for {config_name}")
            success = remove_blackhole_route(peer["peer_ip"])
            if not success:
                return jsonify(error=f"Couldn't unblock peer {peer_name} in {config_name}."), 500

            peer["monitor_blocked"] = False
            peer["expiry_blocked"] = False

            save_peers_with_lock(config_name, peers)

        return jsonify(
            success=True,
            blocked=False,
            message=f"Peer {peer_name} in {config_name} has been unblocked."
        )
    except Exception as e:
        print(f"error in unblocking peer: {e}")
        return jsonify(error=str(e)), 500

    

def derive_public_key(private_key: str) -> str:

    try:
        private_key = private_key.strip()
        missing_padding = len(private_key) % 4
        if missing_padding:
            private_key += "=" * (4 - missing_padding)

        private_key_bytes = base64.b64decode(private_key)

        if len(private_key_bytes) != 32:
            raise ValueError("Wrong private key length. Expected 32 bytes.")

        public_key_bytes = nacl.bindings.crypto_scalarmult_base(private_key_bytes)

        public_key = base64.b64encode(public_key_bytes).decode("utf-8")
        return public_key
    except Exception as e:
        raise ValueError(f"Couldn't derive public key from private key: {e}")


def server_config_details(config_file: str) -> dict:

    config_path = os.path.join(WIREGUARD_CONFIG_DIR, config_file)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_file} not found.")

    private_key = None
    listen_port = None
    with open(config_path, "r") as file:
        for line in file:
            if line.startswith("PrivateKey"):
                private_key = line.split("=")[1].strip()
            if line.startswith("ListenPort"):
                listen_port = line.split("=")[1].strip()

    if not private_key:
        raise ValueError(f"No PrivateKey found in {config_file}.")
    if not listen_port:
        raise ValueError(f"No ListenPort found in {config_file}.")

    public_key = derive_public_key(private_key)
    return {"private_key": private_key, "public_key": public_key, "listen_port": listen_port}


def server_listen_port(config_file: str) -> str:

    config_path = os.path.join(WIREGUARD_CONFIG_DIR, config_file)
    listen_port = None
    with open(config_path, "r") as file:
        for line in file:
            if line.startswith("ListenPort"):
                listen_port = line.split("=")[1].strip()
    if not listen_port:
        raise ValueError(f"No ListenPort found in {config_file}.")
    return listen_port

def obtain_server_keys() -> dict:

    server_keys = {}
    for config_file in os.listdir(WIREGUARD_CONFIG_DIR):
        if config_file.endswith(".conf"):
            config_path = os.path.join(WIREGUARD_CONFIG_DIR, config_file)
            with open(config_path, "r") as file:
                private_key = None
                for line in file:
                    if line.strip().startswith("PrivateKey"):
                        private_key = line.split("=")[1].strip()
                        break
                if private_key:
                    public_key = derive_public_key(private_key)
                    server_keys[config_file] = (private_key, public_key)
                else:
                    print(f"No private key found in {config_file}.")
    return server_keys


def obtain_public_key_conf(config_name: str) -> str:

    try:
        server_details = server_config_details(config_name)
        return server_details['public_key']
    except Exception as e:
        raise ValueError(f"error in retrieving server public key: {e}")

try:
    server_keys = obtain_server_keys()
    for config, keys in server_keys.items():
        private_key, public_key = keys
        print(f"Config: {config}\nPrivateKey: {private_key}\nPublicKey: {public_key}\n")
except Exception as e:
    print(f"Error: {e}")

@app.route('/api/export-peer-qr', methods=['GET'])
def export_peer_qr():
    peer_name = request.args.get('peerName')
    config = request.args.get('config')

    if not peer_name or not config:
        return jsonify({"error": "Peer name and config are required"}), 400

    response = export_peer() 
    if response.status_code != 200:
        return response

    peer_config = response.get_data(as_text=True)

    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(peer_config)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    img_io = BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png", as_attachment=False, download_name=f"{peer_name}.png")

@app.route("/api/export-peer", methods=["GET"])
def export_peer():
    peer_name = request.args.get("peerName")
    config_file = request.args.get("config", "wg0.conf") 

    if not peer_name:
        return jsonify(error="Peer name is required to export config."), 400

    try:
        peers = load_peers_from_json(config_file)
    except Exception as e:
        return jsonify(error=f"error in reading JSON for {config_file}: {str(e)}"), 500

    peer = next((p for p in peers if p["peer_name"] == peer_name and p["config"] == config_file), None)
    if not peer:
        return jsonify(error=f"Peer '{peer_name}' not found in {config_file}."), 404

    dns = peer.get("dns", "1.1.1.1") 
    persistent_keepalive = peer.get("persistent_keepalive", 25)  
    mtu = peer.get("mtu", 1280)  

    try:
        server_public_key = obtain_public_key_conf(config_file)
        custom_ip = obtain_custom_ip()
        server_ip = custom_ip or obtain_server_public_ip()
        server_port = server_listen_port(config_file)
    except ValueError as e:
        return jsonify(error=f"error in retrieving server details: {e}"), 500

    address_cidr = f"{peer['peer_ip']}/32"

    peer_config = (
        f"[Interface]\n"
        f"PrivateKey = {peer['private_key']}\n"
        f"Address = {address_cidr}\n"
        f"DNS = {dns}\n"
        f"MTU = {mtu}\n"
        f"\n"
        f"[Peer]\n"
        f"PublicKey = {server_public_key}\n"
        f"Endpoint = {server_ip}:{server_port}\n"
        f"AllowedIPs = 0.0.0.0/0, ::/0\n"
        f"PersistentKeepalive = {persistent_keepalive}\n"
    )

    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".conf")
        with open(temp_file.name, "w") as file:
            file.write(peer_config)

        response = send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f"{peer_name}.conf",  
            mimetype="application/octet-stream", 
        )

        
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.cache_control.must_revalidate = True

        return response
    except Exception as e:
        return jsonify(error=f"error in creating config file: {str(e)}"), 500


@app.route("/api/qr-code", methods=["GET"])
def generate_qr_code():
    peer_name = request.args.get("peerName")
    config_file = request.args.get("config", "wg0.conf") 

    if not peer_name:
        return jsonify(error="Peer name is required."), 400

    try:
        peers = load_peers_from_json(config_file)
    except Exception as e:
        return jsonify(error=f"error in reading JSON for {config_file}: {str(e)}"), 500

    peer = next((p for p in peers if p["peer_name"] == peer_name and p["config"] == config_file), None)
    if not peer:
        return jsonify(error=f"Peer '{peer_name}' not found in {config_file}."), 404

    dns = peer.get("dns", "1.1.1.1") 
    persistent_keepalive = peer.get("persistent_keepalive", 25)  
    mtu = peer.get("mtu", 1280)  

    try:
        server_public_key = obtain_public_key_conf(config_file)
        custom_ip = obtain_custom_ip()
        server_ip = custom_ip or obtain_server_public_ip()
        server_port = server_listen_port(config_file)
    except ValueError as e:
        return jsonify(error=f"error in retrieving server details: {e}"), 500

    address_cidr = f"{peer['peer_ip']}/32"

    peer_config = (
        f"[Interface]\n"
        f"PrivateKey = {peer['private_key']}\n"
        f"Address = {address_cidr}\n"
        f"DNS = {dns}\n"
        f"MTU = {mtu}\n"
        f"\n"
        f"[Peer]\n"
        f"PublicKey = {server_public_key}\n"
        f"Endpoint = {server_ip}:{server_port}\n"
        f"AllowedIPs = 0.0.0.0/0, ::/0\n"
        f"PersistentKeepalive = {persistent_keepalive}\n"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(peer_config)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return jsonify(qr_code=f"data:image/png;base64,{img_str}")

@app.route('/api/get-peers', methods=['GET'])
def get_peers():
    peer_name = request.args.get("peer_name")
    config_name = request.args.get("config_name")  

    if not peer_name:
        return jsonify(error="Peer name is required."), 400

    db_file_path = os.path.join("db", f"{config_name}.json") if config_name else "db/all_peers.json"

    if not os.path.exists(db_file_path):
        return jsonify(error=f"Config file `{db_file_path}` not found."), 404

    try:
        with open(db_file_path, "r") as db_file:
            peers = json.load(db_file)

        matched_peers = [peer for peer in peers if peer_name.lower() in peer["peer_name"].lower()]
        return jsonify(peers=matched_peers), 200

    except Exception as e:
        return jsonify(error=f"error in reading peer data: {str(e)}"), 500


@app.route("/api/export-peer-telegram", methods=["GET"])
def export_peer_telegram(peer_name, config_file="wg0.conf"):
    try:
        if not peer_name:
            return None, "Peer name is required to export config.", 400

        peers = load_peers_from_json(config_file)

        peer = next((p for p in peers if p["peer_name"] == peer_name and p["config"] == config_file), None)
        if not peer:
            return None, f"Peer '{peer_name}' not found in {config_file}.", 404

        dns = peer.get("dns", "1.1.1.1")  
        persistent_keepalive = peer.get("persistent_keepalive", 25)  
        mtu = peer.get("mtu", 1280)  

        server_public_key = obtain_public_key_conf(config_file)
        custom_ip = obtain_custom_ip()
        server_ip = custom_ip or obtain_server_public_ip()
        server_port = server_listen_port(config_file)

        address_cidr = f"{peer['peer_ip']}/32"
        peer_config = (
            f"[Interface]\n"
            f"PrivateKey = {peer['private_key']}\n"
            f"Address = {address_cidr}\n"
            f"DNS = {dns}\n"
            f"MTU = {mtu}\n"
            f"\n"
            f"[Peer]\n"
            f"PublicKey = {server_public_key}\n"
            f"Endpoint = {server_ip}:{server_port}\n"
            f"AllowedIPs = 0.0.0.0/0, ::/0\n"
            f"PersistentKeepalive = {persistent_keepalive}\n"
        )

        return peer_config, None, 200
    except Exception as e:
        logger.error(f"error in export_peer_telegram: {e}")
        return None, "Internal server error.", 500

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route("/api/download-peer-config", methods=["GET"])
def download_peer_config():
    try:
        peer_name = request.args.get("peerName")
        config_file = request.args.get("config", "wg0.conf")

        if not peer_name or not config_file:
            return jsonify({"error": "Peer name and config file are required"}), 400

        peer_config, error_message, status_code = export_peer_telegram(peer_name, config_file)
        if peer_config is None:
            return jsonify({"error": error_message}), status_code

        return Response(
            peer_config,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename={peer_name}.conf"}
        )
    except Exception as e:
        logger.error(f"error in /api/download-peer-config: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/download-peer-qr", methods=["GET"])
def download_peer_qr():
    try:
        peer_name = request.args.get("peerName")
        config_file = request.args.get("config", "wg0.conf")

        if not peer_name or not config_file:
            return jsonify({"error": "Peer name and config file are required"}), 400

        peer_config, error_message, status_code = export_peer_telegram(peer_name, config_file)
        if peer_config is None:
            return jsonify({"error": error_message}), status_code

        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(peer_config)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        img_io = BytesIO()
        img.save(img_io, "PNG")
        img_io.seek(0)
        return send_file(
            img_io,
            mimetype="image/png",
            as_attachment=False, 
            download_name=f"{peer_name}.png"
        )
    except Exception as e:
        logger.error(f"error in /api/download-peer-qr: {e}")
        return jsonify({"error": "Internal server error"}), 500


def obtain_config_files():
    try:
        return [f for f in os.listdir(WIREGUARD_CONFIG_DIR) if f.endswith(".conf")]
    except Exception as e:
        print(f"error in accessing {WIREGUARD_CONFIG_DIR}: {e}")
        return []

CONFIG_FILE = "endip.json" 

def obtain_custom_ip():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            data = json.load(file)
            return data.get("custom_ip")
    return None

def set_custom_ip(ip):
    data = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            data = json.load(file)
    data["custom_ip"] = ip
    with open(CONFIG_FILE, "w") as file:
        json.dump(data, file)

def custom_ip_or_default():
    custom_ip = obtain_custom_ip()  
    if custom_ip:
        return custom_ip 
    return obtain_server_public_ip()  

@app.route("/api/get-custom-ip", methods=["GET"])
def custom_ip_endpoint():
    try:
        ip = custom_ip_or_default()
        return jsonify(custom_ip=ip)
    except Exception as e:
        return jsonify(error=f"error in retrieving custom IP: {str(e)}"), 500

@app.route("/api/update-custom-ip", methods=["POST"])
def update_custom_ip():
    data = request.get_json()
    custom_ip = data.get("custom_ip")

    if not custom_ip:
        return jsonify(error="Custom IP or Subdomain is required"), 400

    try:
        set_custom_ip(custom_ip)
        return jsonify(message="Custom IP/Subdomain updated successfully")
    except Exception as e:
        return jsonify(error=f"error in updating custom IP/Subdomain: {str(e)}"), 500


def read_file_content(file_name):
    try:
        path = os.path.join(WIREGUARD_CONFIG_DIR, file_name)
        with open(path, "r") as file:
            content = file.read()
            print(f"Content of {file_name}:\n{content}")  
        return content
    except Exception as e:
        print(f"error in reading {file_name}: {str(e)}")
        return None

def obtain_private_key(config_file):
    content = read_file_content(config_file)
    if content is None:
        return None
    for line in content.splitlines():
        if line.startswith("PrivateKey"):
            private_key = line.split("=")[1].strip()
            if private_key:
                return private_key
    return None


def gen_public_from_private(private_key: str) -> str:

    try:
        private_key = private_key.strip()  
        missing_padding = len(private_key) % 4
        if missing_padding:
            private_key += '=' * (4 - missing_padding)

        private_key_bytes = base64.b64decode(private_key)

        if len(private_key_bytes) != 32:
            raise ValueError("Wrong private key length. Expected 32 bytes.")

        public_key_bytes = nacl.bindings.crypto_scalarmult_base(private_key_bytes)

        public_key = base64.b64encode(public_key_bytes).decode('utf-8')
        return public_key
    except base64.binascii.Error as e:
        print(f"Base64 decoding error: {e}")
        return None
    except ValueError as e:
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        print(f"error in generating public key: {e}")
        return None


def load_peers():
    global PEERS
    PEERS = []  

    public_ip = obtain_server_public_ip()

    for config_file in obtain_config_files():
        listen_port = None
        try:
            content = read_file_content(config_file)
            for line in content.splitlines():
                if line.startswith("ListenPort"):
                    listen_port = line.split("=")[1].strip()
                    break
        except Exception as e:
            print(f"error in reading ListenPort from {config_file}: {e}")
            continue

        endpoint = f"{public_ip}:{listen_port}" if public_ip and listen_port else None

        if content and "Error" not in content:
            peer = None
            for line in content.splitlines():
                if line.startswith("[Peer]"):
                    if peer and peer.get("publicKey") and peer.get("ip"):
                        peer["config_file"] = config_file
                        peer["endpoint"] = endpoint  
                        PEERS.append(peer)
                    peer = {"name": None, "ip": None, "publicKey": None}
                elif peer is not None:
                    if line.startswith("#"):
                        peer["name"] = line[1:].strip()
                    if line.startswith("PublicKey"):
                        peer["publicKey"] = line.split("=")[1].strip()
                    if line.startswith("AllowedIPs"):
                        peer["ip"] = line.split("=")[1].strip().split("/")[0]
            if peer and peer.get("publicKey") and peer.get("ip"):
                peer["config_file"] = config_file
                peer["endpoint"] = endpoint  
                PEERS.append(peer)


def obt_private_ip(file_name):
    content = read_file_content(file_name)
    if "Error" in content:
        return None
    for line in content.splitlines():
        if line.startswith("Address"):
            return line.split("=")[1].strip()
    return None


def calculate_available_ips(private_ip):
    try:
        network = ip_network(private_ip, strict=False)
        
        used_ips = set()

        for conf in obtain_config_files():
            content = read_file_content(conf)
            
            for line in content.splitlines():
                if line.startswith("AllowedIPs") or line.startswith("Address"):
                    ip = line.split("=")[-1].strip().split("/")[0]
                    used_ips.add(ip)
        
        available_ips = [str(ip) for ip in network.hosts() if str(ip) not in used_ips]
        
        return available_ips
    except ValueError:
        return []


@app.route("/api/configs", methods=["GET"])
def wg_configs():
    try:
        configs = [f for f in os.listdir(WIREGUARD_CONFIG_DIR) if f.endswith(".conf")]
        return jsonify({"configs": configs}), 200
    except Exception as e:
        return jsonify({"error": f"Couldn't load configs: {str(e)}"}), 500


def sanitize_interface_name(interface_name: str):
    if re.match(r"^[a-zA-Z0-9_-]+$", interface_name):
        return interface_name
    else:
        raise ValueError(f"Wrong interface name: {interface_name}")

@app.route("/api/config-details", methods=["GET"])
def wg_config_details():
    config_file = request.args.get("config", "wg0.conf")
    config_path = os.path.join(WIREGUARD_CONFIG_DIR, config_file)

    if not os.path.exists(config_path):
        return jsonify(error=f"Configuration file {config_file} does not exist."), 404

    details = {"active": False, "Address": "N/A", "ListenPort": "N/A", "DNS": "N/A", "MTU": "N/A"}

    try:
        with open(config_path, "r") as file:
            for line in file:
                line = line.strip()
                if line.startswith("Address"):
                    details["Address"] = line.split("=")[1].strip()
                elif line.startswith("ListenPort"):
                    details["ListenPort"] = line.split("=")[1].strip()
                elif line.startswith("DNS"):
                    details["DNS"] = line.split("=")[1].strip()
                elif line.startswith("MTU"):
                    details["MTU"] = line.split("=")[1].strip()

        interface_name = config_file.split(".")[0]
        try:
            sanitized_interface_name = sanitize_interface_name(interface_name)

            ip_path = "ip"  

            command = [ip_path, "link", "show", sanitized_interface_name] 
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                details["active"] = "state UNKNOWN" in result.stdout or "state UP" in result.stdout
            else:
                details["active"] = False 

        except ValueError as e:
            return jsonify(error=str(e)), 400  
        except Exception as e:
            print(f"Error checking interface status: {e}")
            details["active"] = False  

        return jsonify(details), 200

    except Exception as e:
        print(f"error in reading config file {config_file}: {e}")
        return jsonify(error=f"Couldn't read config file {config_file}. {str(e)}"), 500

@app.route("/api/toggle-config", methods=["POST"])
def toggle_config():
    config_file = request.args.get("config")
    if not config_file:
        return jsonify(error="Configuration file is required."), 400

    try:
        interface_name = sanitize_interface_name(config_file.split(".")[0])
    except ValueError as e:
        return jsonify(error=str(e)), 400

    active = request.args.get("active", "false").lower() == "true"

    wg_quick_path = "wg-quick"  

    try:
        if active:
            result = subprocess.run(
                [wg_quick_path, "up", interface_name], 
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                [wg_quick_path, "down", interface_name], 
                check=True,
                capture_output=True,
                text=True,
            )

        ip_path = "ip" 
        interface_state = subprocess.run(
            [ip_path, "link", "show", interface_name],
            capture_output=True,
            text=True
        )

        is_active = "state UNKNOWN" in interface_state.stdout or "state UP" in interface_state.stdout

        return jsonify(
            message=f"Configuration '{config_file}' has been {'enabled' if is_active else 'disabled'}.",
            active=is_active,
            output=result.stdout + result.stderr,
        )
    except subprocess.CalledProcessError as e:
        print(f"error in toggling config {config_file}: {e}")
        return jsonify(
            error=f"Couldn't {'enable' if active else 'disable'} config '{config_file}': {e.stderr}",
            output=e.stdout + e.stderr,
        ), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify(error=str(e)), 500

    
@app.route("/api/toggle-peer", methods=["POST"])
def toggle_peer():
    try:
        data = request.json
        peer_name = data.get("peerName")
        blocked = data.get("blocked", False)  
        config_name = data.get("config", "wg0.conf")

        if not peer_name:
            return jsonify(error="Peer name is required."), 400

        with json_lock:  
            peers = load_peers_with_lock(config_name) 

            peer = next((p for p in peers if p["peer_name"] == peer_name), None)

            if not peer:
                return jsonify(error=f"Peer '{peer_name}' not found in {config_name}."), 404

            print(f"Current state of peer '{peer_name}': monitor_blocked={peer.get('monitor_blocked')}, expiry_blocked={peer.get('expiry_blocked')}")

            peer["monitor_blocked"] = blocked
            peer["expiry_blocked"] = blocked

            if not blocked: 
                print(f"Enabling peer '{peer_name}'. Resetting values.")

                interface = peer["config"].split(".")[0]
                public_key = peer["public_key"]
                peer_ip = peer.get("peer_ip")

                reset_peer_traffic(interface, public_key, peer_ip)

                peer["remaining"] = convert_to_bytes(peer.get("limit", "0MiB"))
                peer["remaining_time"] = calculate_expiry_duration(peer.get("expiry_time", {}))
                peer["used"] = 0
                peer["last_received_bytes"] = 0  
                peer["last_sent_bytes"] = 0   

                print(f"Unblocking IP: {peer['peer_ip']} for {config_name}")
                success = remove_blackhole_route(peer["peer_ip"])
                if not success:
                    print(f"Failed to remove blackhole route for {peer['peer_ip']}")
                    return jsonify(error=f"Couldn't unblock peer {peer_name} in {config_name}."), 500
            else:  
                print(f"Disabling peer '{peer_name}'. Blocking IP.")
                success = add_blackhole_route(peer["peer_ip"])
                if not success:
                    print(f"Couldn't add blackhole route for {peer['peer_ip']}")
                    return jsonify(error=f"Couldn't block peer {peer_name} in {config_name}."), 500

            save_peers_with_lock(config_name, peers)

        return jsonify(
            message=f"Peer {peer_name} in {config_name} {'disabled' if blocked else 'enabled'} successfully.",
            blocked=blocked,
        )

    except Exception as e:
        print(f"error in toggling peer: {e}")
        return jsonify(error="Couldn't toggle peer state."), 500



@app.route("/api/available-ips", methods=["GET"])
def track_available_ips():
    config_file = request.args.get("config", "wg0.conf")
    
    private_ip = obt_private_ip(config_file)
    
    if not private_ip:
        return jsonify(error=f"Unable to extract private IP from {config_file}"), 400
    
    available_ips = calculate_available_ips(private_ip)
    
    return jsonify(availableIps=available_ips[:100])

@app.route("/api/generate-keys", methods=["GET"])
def generate_keys():
    try:
        wg_path = "wg" 

        result_private = subprocess.run(
            [wg_path, "genkey"], 
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        private_key = result_private.stdout.strip() 
        
        if not private_key:
            raise ValueError("Couldn't generate private key")

        result_public = subprocess.run(
            [wg_path, "pubkey"], 
            input=private_key,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        public_key = result_public.stdout.strip() 
        
        if not public_key:
            raise ValueError("Couldn't generate public key")

        return jsonify(privateKey=private_key, publicKey=public_key)

    except subprocess.CalledProcessError as e:
        print(f"error in generating keys: {e.stderr}")
        return jsonify(error=f"error in generating keys: {e.stderr}"), 500
    except ValueError as e:
        print(f"Value error generating keys: {e}")
        return jsonify(error=f"Value error: {e}"), 500
    except Exception as e:
        print(f"Unexpected error generating keys: {str(e)}")
        return jsonify(error=f"Unexpected error generating keys: {str(e)}"), 500


def obtain_server_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=text", timeout=5)
        return response.text.strip() if response.status_code == 200 else None
    except Exception as e:
        print(f"error in retrieving public IP: {e}")
        return None

def reload_blocked_peers():
    try:
        config_files = [f for f in os.listdir(WIREGUARD_CONFIG_DIR) if f.endswith(".conf")]
        
        for config_file in config_files:
            try:
                peers = load_peers_from_json(config_file)

                for peer in peers:
                    if peer.get("monitor_blocked") or peer.get("expiry_blocked"):
                        logging.info(f"Blocking peer: {peer['peer_name']} ({peer['peer_ip']})")
                        add_blackhole_route(peer["peer_ip"])  
                    else:
                        logging.info(f"Peer {peer['peer_name']} does not meet blocking criteria.")
            except Exception as e:
                logging.error(f"error in processing peers for {config_file}: {e}")
    except Exception as e:
        logging.error(f"error in reloading blocked peers: {e}")



def reload_unblocked_peers():
    try:
        config_files = [f for f in os.listdir(WIREGUARD_CONFIG_DIR) if f.endswith(".conf")]
        
        for config_file in config_files:
            try:
                peers = load_peers_from_json(config_file)

                for peer in peers:
                    if not peer.get("blocked"):
                        print(f"Removing blackhole route for unblocked peer: {peer['peer_name']} ({peer['peer_ip']})")
                        remove_blackhole_route(peer["peer_ip"]) 
            except Exception as e:
                print(f"error in processing peers for {config_file}: {e}")
    except Exception as e:
        print(f"error in reloading unblocked peers: {e}")

@app.route('/api/reload-blocked-peers', methods=['POST'])
def api_reload_blocked_peers():
    try:
        reload_blocked_peers()
        return jsonify({"message": "Blocked peers reloaded successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/reload-unblocked-peers', methods=['POST'])
def api_reload_unblocked_peers():
    try:
        reload_unblocked_peers()
        return jsonify({"message": "Unblocked peers reloaded successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def sanitize_command_part(command_part):

    sanitized_part = re.sub(r'[^a-zA-Z0-9_./-]', '', command_part)
    return sanitized_part

def run_command(command):
    try:
        if not all(isinstance(part, str) for part in command):
            raise ValueError("All command components must be strings.")

        sanitized_command = [sanitize_command_part(part) for part in command]

        process = subprocess.Popen(
            sanitized_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(f"Command failed: {stderr.strip()}")

        return stdout.strip() if stdout.strip() else "Success"
    
    except Exception as e:
        print(f"error in executing command '{' '.join(command)}': {str(e)}")
        return f"error in executing command: {str(e)}"
    
@app.route('/warp/status', methods=['GET'])
def warp_status():
    wgcf_status = "Inactive"

    try:
        command = ["ip", "link", "show"]
        interfaces = run_command(command).splitlines()

        if any("wgcf" in line for line in interfaces):
            wgcf_status = "Active"

    except Exception as e:
        print(f"error in checking service status: {str(e)}")

    return jsonify({
        "wgcf_status": wgcf_status
    })


@app.route('/xray/status', methods=['GET'])
def xray_status():
    xray_status = "Inactive"

    try:
        command = ["sudo", "systemctl", "is-active", "xray"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            xray_status = "Active"
    except Exception as e:
        print(f"error in checking service status: {str(e)}")

    return jsonify({
        "xray_status": xray_status
    })



@app.route('/warp/reset', methods=['POST'])
def reset_warp():
    try:
        messages = []

        command = ["ip", "link", "show"]
        interfaces = run_command(command).splitlines()

        if any("wgcf" in line for line in interfaces):
            messages.append("Wireguard interface 'wgcf' is already up.")
        else:
            try:
                wg_up_result = run_command(["sudo", "wg-quick", "up", "wgcf"])
                messages.append("Wireguard interface 'wgcf' brought up successfully.")
            except Exception as e:
                messages.append(f"error in bringing up Wireguard interface 'wgcf': {str(e)}")
                return jsonify({"message": " | ".join(messages)}), 500

        return jsonify({"message": " | ".join(messages)})

    except Exception as e:
        print(f"Unexpected error in /warp/reset: {str(e)}")
        return jsonify({"message": "Unexpected error occurred while resetting WARP. Please try again."}), 500



@app.route('/xray/reset', methods=['POST'])
def reset_xray():
    try:
        messages = []

        try:
            xray_result = run_command(["sudo", "systemctl", "restart", "xray"])
            messages.append("Xray restarted successfully.")
        except Exception as e:
            messages.append(f"error in restarting Xray: {str(e)}")
            return jsonify({"message": " | ".join(messages)}), 500

        return jsonify({"message": " | ".join(messages)})

    except Exception as e:
        print(f"Unexpected error in /xray/reset: {str(e)}")
        return jsonify({"message": "Unexpected error occurred while resetting Xray. Please try again."}), 500



@app.route('/warp/enable', methods=['POST'])
def enable_warp():
    wg_result1 = run_command(["sudo", "wg-quick", "down", "wgcf"])
    wg_result2 = run_command(["sudo", "wg-quick", "up", "wgcf"])
    wg_result3 = run_command(["sudo", "systemctl", "enable", "wg-quick@wgcf"])
    xray_result = run_command(["sudo", "systemctl", "restart", "xray"])

    if "Error" in wg_result1 or "Error" in wg_result2 or "Error" in wg_result3 or "Error" in xray_result:
        return jsonify({"message": f"error in enabling WARP: {wg_result1} | {wg_result2} | {wg_result3} | {xray_result}"}), 500

    return jsonify({"message": "WARP enabled successfully! Wireguard and Xray restarted."})


@app.route('/warp/stop', methods=['POST'])
def stop_warp():
    messages = []
    
    try:
        interfaces = run_command(["ip", "link", "show"]).splitlines()
        if any("wgcf" in line for line in interfaces):
            try:
                wg_down_result = run_command(["sudo", "wg-quick", "down", "wgcf"])
                disable_warp()
                messages.append("Wireguard interface brought down successfully.")
            except Exception as e:
                messages.append(f"error in bringing down Wireguard interface: {str(e)}")
        else:
            messages.append("Wireguard interface 'wgcf' not found.")
        
        try:
            wg_stop_result = run_command(["sudo", "systemctl", "stop", "wg-quick@wgcf"])
            messages.append("Wireguard service stopped successfully.")
        except Exception as e:
            messages.append(f"error in stopping Wireguard service: {str(e)}")
        
        return jsonify({"message": " | ".join(messages)})

    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500



@app.route('/xray/stop', methods=['POST'])
def stop_xray():
    messages = []
    
    try:
        try:
            xray_stop_result = run_command(["sudo", "systemctl", "stop", "xray"])
            disable_xray()
            messages.append("Xray service stopped successfully.")
        except Exception as e:
            messages.append(f"error in stopping Xray service: {str(e)}")
        
        return jsonify({"message": " | ".join(messages)})

    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500



@app.route('/warp/disable', methods=['POST'])
def disable_warp():
    messages = [] 

    try:
        try:
            wg_down_result = run_command("sudo wg-quick down wgcf")
            print(f"Wireguard Down Result: {wg_down_result}")
            messages.append("Wireguard interface brought down successfully.")
        except Exception as e:
            error_message = f"error in bringing down Wireguard interface: {str(e)}"
            print(error_message)
            messages.append(error_message)

        try:
            wg_stop_result = run_command("sudo systemctl stop wg-quick@wgcf")
            print(f"Wireguard Stop Result: {wg_stop_result}")
            messages.append("Wireguard service stopped successfully.")
        except Exception as e:
            error_message = f"error in stopping Wireguard service: {str(e)}"
            print(error_message)
            messages.append(error_message)

        return jsonify({"message": " | ".join(messages)})

    except Exception as e:
        error_message = f"Unexpected error occurred while disabling WARP: {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500


@app.route('/xray/disable', methods=['POST'])
def disable_xray():
    messages = []  

    try:
        try:
            xray_stop_result = run_command(["sudo", "systemctl", "stop", "xray"])
            print(f"Xray Stop Result: {xray_stop_result}")
            messages.append("Xray service stopped successfully.")
        except Exception as e:
            error_message = f"error in stopping Xray service: {str(e)}"
            print(error_message)
            messages.append(error_message)

        try:
            xray_disable_result = run_command(["sudo", "systemctl", "disable", "xray"])
            print(f"Xray Disable Result: {xray_disable_result}")
            messages.append("Xray service disabled successfully.")
        except Exception as e:
            error_message = f"error in disabling Xray service: {str(e)}"
            print(error_message)
            messages.append(error_message)

        return jsonify({"message": " | ".join(messages)})

    except Exception as e:
        error_message = f"Unexpected error occurred while disabling Xray: {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500



@app.route('/warp/apply-geosites', methods=['POST'])
def apply_geosites():
    try:
        geosites = request.json.get('geosites', [])
        if not geosites:
            return {"message": "No geosites selected."}, 400

        config_path = "/usr/local/etc/xray/config.json"
        with open(config_path, "r") as xray_file:
            config = json.load(xray_file)

        for rule in config["routing"]["rules"]:
            if rule["type"] == "field" and rule["outboundTag"] == "warp":
                rule["domain"] = geosites

        with open(config_path, "w") as xray_file:
            json.dump(config, xray_file, indent=4)

        xray_restart = run_command(["sudo", "systemctl", "restart", "xray"])
        if "Error" in xray_restart:
            return {"message": "error in restarting Xray"}, 500

        return {"message": f"Geosites {geosites} applied successfully!"}

    except Exception as e:
        return {"message": f"error in applying geosites: {str(e)}"}, 500



@app.route('/warp/install', methods=['POST'])
def install_fullwarp_route():
    try:
        thread = Thread(target=install_fullwarp)
        thread.start()
        return jsonify({"message": "Installation started!"})
    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500

@app.route('/warp/install-progress', methods=['GET'])
def install_progress_route():
    try:
        if not os.path.exists(INSTALL_PROGRESS_FILE):
            return jsonify({"error": "Progress file not found."}), 404

        with open(INSTALL_PROGRESS_FILE, "r") as f:
            progress_data = json.load(f)
        return jsonify(progress_data), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Progress file contains invalid JSON."}), 500
    except Exception as e:
        return jsonify({"error": f"error in fetching progress: {str(e)}"}), 500


@app.route('/warp/install-xray', methods=['POST'])
def install_xray_warp_route():
    try:
        thread = Thread(target=install_warp)
        thread.start()
        return jsonify({"message": "Installation started!"})
    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500

@app.route('/warp/install-xray-progress', methods=['GET'])
def install_xray_progress_route():
    try:
        if not os.path.exists(INSTALL_PROGRESS_FILE):
            return jsonify({"error": "Progress file not found."}), 404

        with open(INSTALL_PROGRESS_FILE, "r") as f:
            progress_data = json.load(f)
        return jsonify(progress_data), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Progress file contains invalid JSON."}), 500
    except Exception as e:
        return jsonify({"error": f"error in fetching progress: {str(e)}"}), 500


@app.route('/warp/install-xray', methods=['POST'])
def install_xraywarp_route():
    try:
        result = install_warp()  
        if "Error" in result.get("message", ""):
            return jsonify({"message": result["message"]}), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"message": f"Unexpected error: {str(e)}"}), 500


@app.route('/warp/uninstall', methods=['POST'])
def uninstall_warp():
    try:
        print("Stopping related services...")
        try:
            run_command(["sudo", "systemctl", "stop", "wg-quick@wgcf"])
        except Exception as e:
            print(f"Warning: Couldn't stop wg-quick@wgcf service. {str(e)}")

        try:
            run_command(["sudo", "wg-quick", "down", "wgcf"])
        except Exception as e:
            print(f"Warning: Couldn't stop WARP {str(e)}")

        print("Removing WARP configs...")
        run_command(["sudo", "rm", "-f", "/etc/wireguard/wgcf.conf"])
        run_command(["sudo", "rm", "-f", "/usr/local/bin/wgcf"])

        print("Ensuring Wireguard remains installed...")
        try:
            wireguard_status = run_command(["dpkg-query", "-l", "|", "grep", "wireguard"])
            if "wireguard" not in wireguard_status:
                raise Exception("Warp deleted")
        except Exception as e:
            raise Exception(f"Wireguard validation failed: {str(e)}")

        print("WARP uninstallation completed successfully!")
        return {"message": "WARP uninstallation completed successfully!"}

    except Exception as e:
        error_message = f"error in during WARP uninstallation: {str(e)}"
        print(error_message)
        return {"message": error_message}



@app.route('/xray/uninstall', methods=['POST'])
def uninstall_xray():
    try:
        print("Stopping related services...")
        try:
            run_command(["sudo", "systemctl", "stop", "xray"])
        except Exception as e:
            print(f"Warning: Couldn't stop Xray service. {str(e)}")

        print("Removing Xray configs...")
        run_command(["sudo", "rm", "-rf", "/usr/local/etc/xray"])
        run_command(["sudo", "rm", "-f", "/usr/local/bin/xray"])

        print("Xray uninstallation completed successfully!")
        return jsonify({"message": "Xray uninstallation completed successfully!"})

    except Exception as e:
        error_message = f"error in during Xray uninstallation: {str(e)}"
        print(error_message)
        return jsonify({"message": error_message}), 500



@app.route('/api/server-ips', methods=['GET'])
def obtain_server_ips():
    try:
        ipv4 = None
        try:
            result = subprocess.run(
                ["hostname", "-I"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                timeout=5, 
                check=True
            )
            ipv4 = result.stdout.split()[0] 
        except subprocess.CalledProcessError:
            ipv4 = 'Unavailable'
        except Exception as e:
            ipv4 = 'Unavailable'
            print(f"error in obtaining IPv4: {e}")

        ipv6 = None
        try:
            ipv6_response = requests.get('https://api6.ipify.org?format=json', timeout=5)
            if ipv6_response.status_code == 200:
                ipv6 = ipv6_response.json().get('ip', 'Unavailable')
            else:
                ipv6 = 'Unavailable'
        except requests.RequestException as e:
            ipv6 = 'Unavailable'
            print(f"error in obtaining IPv6: {e}")

        return jsonify({'public_ipv4': ipv4, 'public_ipv6': ipv6}), 200

    except Exception as e:
        print(f"error in obtaining server IPs: {e}")
        return jsonify({'error': str(e)}), 500  
    

@app.route('/api/speed', methods=['GET'])
def obtain_speed():
    try:
        initial_counters = psutil.net_io_counters()
        initial_upload = initial_counters.bytes_sent
        initial_download = initial_counters.bytes_recv
        time.sleep(1)
        final_counters = psutil.net_io_counters()
        final_upload = final_counters.bytes_sent
        final_download = final_counters.bytes_recv

        upload_speed = (final_upload - initial_upload) / 1024 
        download_speed = (final_download - initial_download) / 1024  

        return jsonify({
            'uploadSpeed': upload_speed,
            'downloadSpeed': download_speed
        }), 200
    except Exception as e:
        app.logger.error(f"error in /api/speed: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500

    
@app.route('/api/logs', methods=['GET', 'DELETE'])
def manage_logs():
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wireguard.log')

    if request.method == 'GET':
        limit = request.args.get('limit', 20, type=int)
        try:
            if not os.path.exists(log_file_path) or os.stat(log_file_path).st_size == 0:
                return jsonify({'logs': []}), 200

            with open(log_file_path, 'r') as log_file:
                logs = log_file.readlines()
            return jsonify({'logs': logs[-limit:]}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            with open(log_file_path, 'w') as log_file:
                log_file.truncate(0)  
            return jsonify({'message': 'Logs cleared successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route("/warp")
def warp_page():
    if "username" not in session:
        flash("Please log in to access Warp.", "error")
        return redirect("/login")
    
    language = session.get('language', 'en')
    template_name = "warp-fa.html" if language == "fa" else "warp.html"
    return render_template(template_name)

short_links = {}
@app.route("/s/<short_id>", methods=["GET"])
def short_redirect(short_id):
    short_links = load_short_links()

    encrypted_link = short_links.get(short_id)
    if not encrypted_link:
        return "Link not found or already removed", 404

    try:
        long_link = cipher.decrypt(encrypted_link.encode()).decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return "Invalid link", 404

    return redirect(long_link)





def load_short_links():
    try:
        with open(SHORT_LINKS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_short_links(short_links):
    with open(SHORT_LINKS_FILE, "w") as file:
        json.dump(short_links, file, indent=4)

@app.route("/api/create-peer", methods=["POST"])
def create_peer():
    try:
        data = request.json
        print(f"Received data: {data}")
        
        peer_name = data.get('peerName')
        if not peer_name or not re.match(r'^[a-zA-Z0-9_-]+$', peer_name):
            return jsonify({"error": "Wrong peer name. Only letters, numbers, underscores, and dashes are allowed."}), 400


        peer_ip = data.get('peerIp')
        try:
            sanitized_peer_ip = sanitize_ip(peer_ip)
        except ValueError:
            return jsonify({"error": "Wrong IP address."}), 400

        data_limit = data.get('dataLimit')
        if not data_limit or not re.match(r'^\d+(MiB|GiB)$', data_limit):
            return jsonify({"error": "Wrong data limit. Must be a number followed by MiB or GiB."}), 400
        numeric_limit = int(data_limit[:-3])
        if numeric_limit <= 0 or numeric_limit > 1024:
            return jsonify({"error": "Data limit must be between 1 and 1024 MiB/GiB."}), 400

        config_file = data.get("configFile", "wg0.conf")
        if not re.match(r'^[a-zA-Z0-9_-]+\.conf$', config_file):
            return jsonify({"error": "Wrong config file name."}), 400

        dns = data.get('dns') or "1.1.1.1, 1.0.0.1"

        expiry_days = data.get('expiryDays', 0)
        expiry_months = int(data.get("expiryMonths") or 0)
        expiry_hours = int(data.get("expiryHours") or 0)
        expiry_minutes = int(data.get("expiryMinutes") or 0)
        if expiry_days < 0 or expiry_months < 0 or expiry_hours < 0 or expiry_minutes < 0:
            return jsonify({"error": "Expiry times cannot be negative."}), 400

        first_usage = not data.get("firstUsage", False)
        persistent_keepalive = data.get("persistentKeepalive", 25)
        mtu = data.get("mtu", 1280)

        print(f"First usage set to: {first_usage}")

        total_expiry_minutes = (
            expiry_months * 30 * 24 * 60 +
            expiry_days * 24 * 60 +
            expiry_hours * 60 +
            expiry_minutes
        )
        if total_expiry_minutes <= 0:
            return jsonify({"error": "Total expiry time must be greater than zero."}), 400

        bulk_count = int(data.get("bulkCount", 1))  

        with json_lock:
            peers = load_peers_with_lock(config_file)
            print(f"Loaded peers from {config_file}.json: {peers}")

            if bulk_count == 1:
                for peer in peers:
                    if peer.get("peer_ip") == peer_ip:
                        if not peer.get("deleted", False):
                            return jsonify({"error": f"Peer IP {peer_ip} is already in use."}), 400
                        else:
                            peer["deleted"] = False
                            save_peers_with_lock(config_file, peers)
                            break

                peer_token = generate_peer_token()

                client_private_key_bytes = nacl.bindings.randombytes(32)
                client_private_key = base64.b64encode(client_private_key_bytes).decode("utf-8")
                client_public_key = derive_public_key(client_private_key)

                peer = {
                    "peer_name": peer_name,
                    "peer_ip": peer_ip,
                    "dns": dns,
                    "limit": data_limit,
                    "used": 0,
                    "remaining": convert_to_bytes(data_limit),
                    "monitor_blocked": False,
                    "expiry_blocked": False,
                    "private_key": client_private_key,
                    "public_key": client_public_key,
                    "token": peer_token,  
                    "expiry_time": {
                        "months": expiry_months,
                        "days": expiry_days,
                        "hours": expiry_hours,
                        "minutes": expiry_minutes,
                    },
                    "remaining_time": total_expiry_minutes,
                    "first_usage": first_usage,
                    "persistent_keepalive": persistent_keepalive,
                    "mtu": mtu,
                    "config": config_file,
                    "last_received_bytes": 0,
                    "last_sent_bytes": 0
                }

                peers.append(peer)
                save_peers_with_lock(config_file, peers)

                interface = sanitize_interface_name(config_file.split(".")[0])
                wg_path = "wg"  

                subprocess.run(
                    [wg_path, "set", interface, "peer", client_public_key, "allowed-ips", f"{sanitized_peer_ip}/32"],
                    check=True
                )

                config_path = os.path.join("/etc/wireguard", config_file) 
                peer_config = (
                    f"[Peer]\n"
                    f"# {peer_name}\n"
                    f"PublicKey = {client_public_key}\n"
                    f"AllowedIPs = {peer_ip}/32\n"
                    f"PersistentKeepalive = {persistent_keepalive}\n"
                ).strip() + "\n\n"

                with open(config_path, "a") as conf:
                    conf.write(peer_config)

                short_links = load_short_links()

                long_interactive_link = url_for(
                    'peer_details',
                    peer_name=peer['peer_name'],
                    config_file=peer['config'],
                    token=peer_token,
                    _external=True
                )
                encrypted_link = cipher.encrypt(long_interactive_link.encode())
                short_id = secrets.token_urlsafe(8)
                if short_id not in short_links:  
                    short_links[short_id] = encrypted_link.decode()
                    save_short_links(short_links)

                short_interactive_link = url_for('short_redirect', short_id=short_id, _external=True)

                print(f"Long interactive link for peer '{peer_name}': {long_interactive_link}")
                print(f"Short interactive link for peer '{peer_name}': {short_interactive_link}")

                return jsonify({
                    "message": f"Peer created successfully in {config_file}!",
                    "peer_name": peer_name,
                    "short_link": short_interactive_link
                })

            else:
                network = ip_network(peer_ip + "/24", strict=False)
                used_ips = [
                    peer["peer_ip"]
                    for peer in peers
                    if not peer.get("deleted", False)
                ]
                available_ips = [
                    str(ip) for ip in network.hosts() if str(ip) not in used_ips and str(ip) >= peer_ip
                ]

                if len(available_ips) < bulk_count:
                    return jsonify({"error": "Not enough available IP addresses for the requested bulk creation."}), 400

                responses = []
                for i in range(bulk_count):
                    current_peer_ip = available_ips[i]
                    new_peer_name = f"{peer_name}-{i + 1}"

                    peer_token = generate_peer_token()

                    client_private_key_bytes = nacl.bindings.randombytes(32)
                    client_private_key = base64.b64encode(client_private_key_bytes).decode("utf-8")
                    client_public_key = derive_public_key(client_private_key)

                    peer = {
                        "peer_name": new_peer_name,
                        "peer_ip": current_peer_ip,
                        "dns": dns,
                        "limit": data_limit,
                        "used": 0,
                        "remaining": convert_to_bytes(data_limit),
                        "monitor_blocked": False,
                        "expiry_blocked": False,
                        "private_key": client_private_key,
                        "public_key": client_public_key,
                        "token": peer_token,  
                        "expiry_time": {
                            "months": expiry_months,
                            "days": expiry_days,
                            "hours": expiry_hours,
                            "minutes": expiry_minutes,
                        },
                        "remaining_time": total_expiry_minutes,
                        "first_usage": first_usage,
                        "persistent_keepalive": persistent_keepalive,
                        "mtu": mtu,
                        "config": config_file,
                        "last_received_bytes": 0,
                        "last_sent_bytes": 0
                    }

                    peers.append(peer)

                    interface = sanitize_interface_name(config_file.split(".")[0])
                    wg_path = "wg"  
                    subprocess.run(
                        [wg_path, "set", interface, "peer", client_public_key, "allowed-ips", f"{current_peer_ip}/32"],
                        check=True
                    )

                    config_path = os.path.join("/etc/wireguard", config_file)
                    peer_config = (
                        f"[Peer]\n"
                        f"# {new_peer_name}\n"
                        f"PublicKey = {client_public_key}\n"
                        f"AllowedIPs = {current_peer_ip}/32\n"
                        f"PersistentKeepalive = {persistent_keepalive}\n"
                    ).strip() + "\n\n"

                    with open(config_path, "a") as conf:
                        conf.write(peer_config)

                    short_links = load_short_links()
                    long_interactive_link = url_for(
                        'peer_details',
                        peer_name=peer['peer_name'],
                        config_file=peer['config'],
                        token=peer_token,
                        _external=True
                    )
                    encrypted_link = cipher.encrypt(long_interactive_link.encode())
                    short_id = secrets.token_urlsafe(8)
                    if short_id not in short_links:  
                        short_links[short_id] = encrypted_link.decode()
                        save_short_links(short_links)

                    short_interactive_link = url_for('short_redirect', short_id=short_id, _external=True)

                    responses.append({
                        "peer_name": new_peer_name,
                        "short_link": short_interactive_link,
                        "peer_ip": current_peer_ip
                    })

                save_peers_with_lock(config_file, peers)

                return jsonify({
                    "message": f"{bulk_count} peers created successfully.",
                    "peers": responses
                }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500



@app.route("/api/get-peer-link", methods=["GET"])
def get_peer_short_link():
    peer_name = request.args.get("peerName")
    config_file = request.args.get("config")

    if not peer_name or not config_file:
        return jsonify({"error": "Peer name and config file are required."}), 400

    try:
        with json_lock:
            peers = load_peers_with_lock(config_file)
            peer = next((p for p in peers if p["peer_name"] == peer_name), None)
            if not peer:
                return jsonify({"error": f"Peer '{peer_name}' not found in {config_file}."}), 404

            short_links = load_short_links()
            long_link = url_for(
                'peer_details',
                peer_name=peer_name,
                config_file=config_file,
                token=peer["token"],
                _external=True
            )

            short_id = next(
                (key for key, value in short_links.items()
                 if cipher.decrypt(value.encode()).decode() == long_link),
                None
            )

            if short_id:
                short_link = url_for('short_redirect', short_id=short_id, _external=True)
                return jsonify({"short_link": short_link})
            else:
                return jsonify({"error": "Short link not found."}), 404
    except Exception as e:
        print(f"error in fetching peer short link: {e}")
        return jsonify({"error": f"error happened: {str(e)}"}), 500


def generate_peer_token():
    return secrets.token_urlsafe(16)

@app.route('/peer-details', methods=['GET'])
def peer_details():
    peer_name = request.args.get('peer_name')
    config_file = request.args.get('config_file')
    token = request.args.get('token')

    app.logger.info(f"Peer Name: {peer_name}")
    app.logger.info(f"Config File: {config_file}")
    app.logger.info(f"Token: {token}")

    if not peer_name or not config_file or not token:
        return jsonify({"error": "Peer name, config file, and token are required."}), 400

    return render_template(
        'template.html',
        peer_name=peer_name,
        config_file=config_file,
        token=token
    )

@app.route("/api/obt-peer-botdetails", methods=["GET"])
def obt_peerbot_details():
    peer_name = request.args.get("peer_name")
    config_file = request.args.get("config_file")

    if not peer_name or not config_file:
        return jsonify({"error": "Peer name and config file are required."}), 400

    try:
        peers_file = obtain_peers_file(config_file)
        peers_metadata = load_peers_from_json(peers_file)

        peer = next((p for p in peers_metadata if p["peer_name"] == peer_name), None)

        if not peer:
            return jsonify({"error": f"Peer with name '{peer_name}' not found in {config_file}."}), 404

        peer_details = {
            "peer_name": peer["peer_name"],
            "limit": peer.get("limit", "N/A"),
            "used": peer.get("used", 0),
            "remaining": peer.get("remaining", 0),
            "expiry_time": peer.get("expiry_time", {}),
            "status": "active" if not peer.get("monitor_blocked") and not peer.get("expiry_blocked") else "inactive",
        }

        return jsonify(peer_details)

    except Exception as e:
        print(f"Error retrieving peer details: {e}")
        return jsonify({"error": f"An error occurred while fetching peer details: {str(e)}"}), 500


@app.route('/api/peer-detailz', methods=['GET'])
def api_peer_details():
    peer_name = request.args.get('peer_name')  
    config_file = request.args.get('config_file')  
    token = request.args.get('token') 

    if not peer_name or not config_file or not token:
        return jsonify({"error": "Peer name, config file, and token are required."}), 400

    try:
        peer_details = obtain_peer_details_from_storage(peer_name, config_file, token)

        return jsonify(peer_details)

    except ValueError as e:
        app.logger.error(f"ValueError: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

def obtain_peer_details_from_storage(peer_name, config_file, token):
    try:
        peers_file = obtain_peers_file(config_file)
        peers_metadata = load_peers_from_json(peers_file)

        peer = next((p for p in peers_metadata if p["peer_name"] == peer_name), None)

        if not peer:
            raise ValueError(f"Peer with name '{peer_name}' not found in {config_file}.")

        if peer["token"] != token:
            raise ValueError("Invalid token for this peer.")

        peer["used_human"] = bytes_to_readable(peer.get("used", 0))
        peer["remaining_human"] = bytes_to_readable(peer.get("remaining", 0))
        peer["limit_human"] = bytes_to_readable(convert_to_bytes(peer["limit"]))

        created_at_str = peer.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
        created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)

        expiry_months = peer.get("expiry_time", {}).get("months", 0)
        expiry_days = peer.get("expiry_time", {}).get("days", 0)
        expiry_hours = peer.get("expiry_time", {}).get("hours", 0)
        expiry_minutes = peer.get("expiry_time", {}).get("minutes", 0)

        expiry = created_at + timedelta(
            days=(expiry_months * 30) + expiry_days,
            hours=expiry_hours,
            minutes=expiry_minutes
        )
        now = datetime.now(timezone.utc)

        peer["expiry"] = expiry.strftime("%Y-%m-%d %H:%M:%S")

        time_diff = expiry - now
        if time_diff.total_seconds() <= 0:
            peer["expiry_human"] = "Expired"
        else:
            exp_days = time_diff.days
            exp_hours = (time_diff.seconds // 3600) % 24
            exp_minutes = (time_diff.seconds % 3600) // 60
            peer["expiry_human"] = f"{exp_days} روز، {exp_hours} ساعت، {exp_minutes} دقیقه باقی مانده"

        total_minutes = peer.get("remaining_time", 0)
        days = total_minutes // (24 * 60)
        hours = (total_minutes % (24 * 60)) // 60
        minutes = total_minutes % 60
        peer["remaining_time_human"] = f"{days} روز، {hours} ساعت، {minutes} دقیقه"

        is_active = not (peer.get("monitor_blocked", False) or peer.get("expiry_blocked", False))
        peer["status"] = "active" if is_active else "inactive"

        return {
            "peer_name": peer["peer_name"],
            "limit_human": peer["limit_human"],
            "used_human": peer["used_human"],
            "remaining_human": peer["remaining_human"],
            "expiry_human": peer["expiry_human"],
            "remaining_time": peer["remaining_time"],
            "remaining_time_human": peer["remaining_time_human"],
            "status": peer["status"]  
        }

    except Exception as e:
        raise ValueError(f"error in obtaining peer details: {str(e)}")



def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json")
        if response.status_code == 200:
            return response.json().get("ip")
    except Exception as e:
        print(f"error in fetching public IP: {e}")
    return None

def get_server_location():
    public_ip = get_public_ip()
    print(f"got Public IP: {public_ip}") 
    if not public_ip:
        print("Couldn't determine the public IP.")
        return {"country": "Unknown", "country_code": ""}

    try:
        response = requests.get(f"https://ipwho.is/{public_ip}")
        print(f"ipwho.is Response Status Code: {response.status_code}")  
        print(f"ipwho.is Response Text: {response.text}")  
        if response.status_code == 200:
            data = response.json()
            return {
                "country": data.get("country", "Unknown"),
                "country_code": data.get("country_code", "").lower(),
            }
    except Exception as e:
        print(f"error in fetching server location: {e}")

    return {"country": "Unknown", "country_code": ""}


@app.context_processor
def inject_server_location():
    location = get_server_location()
    return dict(server_location=location)


def sanitize_public_key(public_key: str):
    if re.match(r"^[A-Za-z0-9+/=]+$", public_key):
        return public_key
    else:
        raise ValueError(f"Wrong public key: {public_key}")

short_links_lock = threading.Lock()

@app.route("/api/delete-peer", methods=["POST"])
def delete_peer():
    try:
        data = request.json
        peer_name = data.get("peerName")
        config_file = data.get("configFile") 

        if not peer_name:
            return jsonify(error="Peer name is required."), 400

        if not config_file or not re.match(r"^[a-zA-Z0-9_-]+\.conf$", config_file):
            return jsonify(error="Valid config file name is required."), 400

        with json_lock:  
            peers = load_peers_with_lock(config_file) 

            peer = next((p for p in peers if p["peer_name"] == peer_name), None)
            if not peer:
                return jsonify(error=f"Peer '{peer_name}' not found in {config_file}."), 404

            interface = sanitize_interface_name(config_file.split(".")[0])
            public_key = sanitize_public_key(peer["public_key"])

            try:
                wg_path = "wg"
                result = subprocess.run(
                    [wg_path, "set", interface, "peer", public_key, "remove"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if result.returncode != 0:
                    logging.error(f"error in removing peer from Wireguard: {result.stderr}")
                    return jsonify(error=f"Couldn't remove peer from Wireguard: {result.stderr}"), 500
            except subprocess.CalledProcessError as e:
                logging.error(f"error in removing peer from Wireguard: {e.stderr}")
                return jsonify(error=f"Couldn't remove peer from Wireguard: {e.stderr}"), 500

            peer_ip = peer.get("peer_ip")
            if peer_ip and not remove_blackhole_route(peer_ip):
                logging.warning(f"Couldn't remove blackhole route for IP {peer_ip}.")

            config_path = os.path.join(WIREGUARD_CONFIG_DIR, config_file)
            try:
                with open(config_path, "r") as conf_file:
                    lines = conf_file.readlines()

                new_lines = []
                inside_peer_block = False

                for i, line in enumerate(lines):
                    if line.startswith("[Peer]"):
                        if f"# {peer_name}" in lines[i + 1] or peer["public_key"] in lines[i + 1]:
                            inside_peer_block = True
                            continue
                    if inside_peer_block:
                        if line.strip() == "":  
                            inside_peer_block = False
                        continue
                    new_lines.append(line)

                with open(config_path, "w") as conf_file:
                    conf_file.writelines(new_lines)

                logging.info(f"Updated Wireguard config file '{config_path}'.")
            except Exception as e:
                logging.error(f"error in updating Wireguard config file '{config_path}': {e}")
                return jsonify(error="Couldn't update Wireguard config file."), 500

            peers = [p for p in peers if p["peer_name"] != peer_name]
            save_peers_with_lock(config_file, peers)

        with short_links_lock:  
            short_links = load_short_links()  

            link_to_delete = None
            for short_id, encrypted_link in short_links.items():
                try:
                    long_link = cipher.decrypt(encrypted_link.encode()).decode()
                    if f"peer_name={peer_name}" in long_link:
                        link_to_delete = short_id
                        break
                except Exception as e:
                    logging.error(f"Error decrypting short link: {e}")
                    continue

            if link_to_delete:
                del short_links[link_to_delete]  
                save_short_links(short_links)  
                logging.info(f"Deleted short link for peer '{peer_name}'.")

        return jsonify(success=True, message=f"Peer '{peer_name}' has been deleted dynamically.")
    except Exception as e:
        logging.error(f"error in deleting peer: {e}")
        return jsonify(error=f"error in deleting peer: {e}"), 500


@app.route("/api/delete-all-configs", methods=["POST"])
def delete_all_configs():
    try:
        data = request.json
        confirmation = data.get("confirmation", False)

        if not confirmation:
            return jsonify(error="Coanfirmation is required to delete all configs."), 400

        config_file = "wg0.conf" 
        config_path = os.path.join(WIREGUARD_CONFIG_DIR, config_file)

        if not os.path.exists(config_path):
            return jsonify(error="Wireguard config file does not exist."), 404

        with open(config_path, "r") as file:
            lines = file.readlines()

        new_lines = []
        inside_peer_block = False
        for line in lines:
            if line.startswith("[Peer]"):
                inside_peer_block = True
                continue
            if inside_peer_block and line.strip() == "":
                inside_peer_block = False
                continue
            if not inside_peer_block:
                new_lines.append(line)

        with open(config_path, "w") as file:
            file.writelines(new_lines)

        logging.info(f"All peer configs deleted from '{config_path}', but the [Interface] section was retained.")

        peers_path = os.path.join(DB_DIR, f"{config_file.split('.')[0]}.json")
        if os.path.exists(peers_path):
            with open(peers_path, "w") as peers_file:
                peers_file.write("[]") 
            logging.info(f"Cleared peers in JSON file '{peers_path}'.")

        return jsonify(message="All peer configs deleted successfully.")
    except Exception as e:
        logging.error(f"error in deleting all configs: {e}")
        return jsonify(error=f"An error occurred: {str(e)}"), 500


@app.route("/api/get-peer-info", methods=["GET"])
def get_peer_info():

    try:
        peer_name = request.args.get("peerName")
        config_file = request.args.get("configFile", "wg0.conf")

        if not peer_name:
            return jsonify({"error": "Peer name is required."}), 400

        if not re.match(r"^[a-zA-Z0-9_-]+\.conf$", config_file):
            return jsonify({"error": "Wrong config file name."}), 400

        peers = load_peers_from_json(config_file)
        peer = next((p for p in peers if p["peer_name"] == peer_name), None)

        if not peer:
            return jsonify({"error": f"Peer '{peer_name}' not found in {config_file}."}), 404

        return jsonify({"peerInfo": peer})
    except Exception as e:
        logging.error(f"error in retrieving peer info: {e}")
        return jsonify({"error": "Couldn't retrieve peer info."}), 500


def reset_peer_traffic(interface, public_key, peer_ip=None):
    try:
        interface = sanitize_interface_name(interface)
        public_key = sanitize_public_key(public_key)

        wg_path = "wg"  

        config_file = f"/etc/wireguard/{interface}.conf"

        with tempfile.TemporaryDirectory() as tmp_dir:
            backup_file = f"{tmp_dir}/peer_backup.conf"

            with open(config_file, "r") as config:
                lines = config.readlines()

            peer_config = []
            in_peer_section = False

            for line in lines:
                if f"PublicKey = {public_key}" in line:
                    in_peer_section = True
                if in_peer_section:
                    peer_config.append(line)
                if in_peer_section and line.strip() == "":
                    break  

            if peer_config:
                with open(backup_file, "w") as backup:
                    backup.writelines(peer_config)

                print(f"Backup of peer {public_key} saved to {backup_file}.")
            else:
                print(f"Peer {public_key} not found in {config_file}. Skipping backup.")

            subprocess.run([wg_path, "set", interface, "peer", public_key, "remove"], check=True)
            print(f"Peer {public_key} removed from {interface}, resetting counters.")

            if peer_ip:
                sanitized_peer_ip = sanitize_ip(peer_ip)
                subprocess.run(
                    [wg_path, "set", interface, "peer", public_key, "allowed-ips", f"{sanitized_peer_ip}/32"],
                    check=True
                )
                print(f"Peer {public_key} re-added to {interface} with allowed IP {sanitized_peer_ip}. Traffic counters reset.")
            else:
                if peer_config:
                    with open(config_file, "a") as config:
                        config.writelines(peer_config)
                    print(f"Peer {public_key} re-added to {interface} with backed-up configuration. Traffic counters reset.")
                else:
                    print(f"No peer configuration found for {public_key}. Cannot re-add.")

    except subprocess.CalledProcessError as e:
        print(f"Error while checking/removing peer {public_key} in {interface}: {e}")
        return
    except ValueError as e:
        print(f"Sanitization error: {e}")
        return



def parse_traffic(peer_ip, public_key):
    try:
        if not isinstance(peer_ip, str) or not isinstance(public_key, str):
            raise ValueError("Both peer_ip and public_key must be strings.")

        wg_path = "wg"  

        result = subprocess.run(
            [wg_path, "show", "all", "dump"], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        wg_output = result.stdout

        lines = wg_output.splitlines()

        for line in lines:
            columns = line.split("\t")
            if len(columns) > 5 and columns[1] == public_key:
                allowed_ips = columns[4].split(",")
                if any(peer_ip in ip for ip in allowed_ips):
                    received_bytes = int(columns[5])
                    sent_bytes = int(columns[6])
                    total_bytes = received_bytes + sent_bytes
                    return total_bytes

        return 0
    except Exception as e:
        print(f"error in parsing traffic for IP {peer_ip}: {e}")
        return 0


@app.route("/api/peers-by-interface", methods=["GET"])
def obtain_peers_interface():
    interface = request.args.get("interface")

    if not interface:
        return jsonify({"error": "Interface parameter is required."}), 400

    try:
        peers_file = obtain_peers_file(f"{interface}.conf")
        
        peers_metadata = load_peers_from_json(peers_file)

        if not peers_metadata:
            return jsonify({"error": f"No peers found for interface {interface}."}), 404

        for peer in peers_metadata:
            peer["peer_name"] = peer.get("peer_name", "Unnamed Peer")
            peer["peer_ip"] = peer.get("peer_ip", "N/A")
            peer["public_key"] = peer.get("public_key", "N/A")
            peer["used_human"] = bytes_to_readable(peer.get("used", 0))
            peer["remaining_human"] = bytes_to_readable(peer.get("remaining", 0))
            peer["limit_human"] = bytes_to_readable(convert_to_bytes(peer["limit"]))

        return jsonify({"peers": peers_metadata})
    except FileNotFoundError:
        return jsonify({"error": f"Configuration file for interface {interface} not found."}), 404
    except Exception as e:
        print(f"error in loading peers for interface {interface}: {e}") 
        return jsonify(error=f"error occurred: {str(e)}"), 500


def format_size(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1024 ** 2:
        return f"{size / 1024:.2f} KiB"
    elif size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MiB"
    else:
        return f"{size / (1024 ** 3):.2f} GiB"


def parse_limit_to_bytes(limit_str):
    if not limit_str or not isinstance(limit_str, str):
        return None
    units = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}
    try:
        num = ''.join(filter(str.isdigit, limit_str))
        unit = ''.join(filter(str.isalpha, limit_str))
        if unit in units:
            return int(num) * units[unit]
    except (ValueError, KeyError):
        return None
    return None


@app.route('/api/search-peers', methods=['GET'])
def search_peers():
    try:
        query = request.args.get('query', '').strip().lower()
        filter_value = request.args.get('filter', '').strip().lower()

        db_directory = os.path.join(BASE_DIR, "db")
        if not os.path.exists(db_directory):
            app.logger.error(f"DB directory not found: {db_directory}")
            return jsonify({"error": "DB directory not found."}), 500

        all_peers = []

        for filename in os.listdir(db_directory):
            if filename.endswith('.json'):
                filepath = os.path.join(db_directory, filename)
                try:
                    with open(filepath, 'r') as file:
                        peers = json.load(file)
                        if isinstance(peers, list):
                            all_peers.extend(peers)
                except json.JSONDecodeError as e:
                    app.logger.error(f"JSON in {filepath} is invalid: {e}")
                    continue
                except Exception as e:
                    app.logger.error(f"Error reading file {filepath}: {e}")
                    continue

        filtered_peers = []
        for peer in all_peers:
            is_banned = peer.get('monitor_blocked', False) or peer.get('expiry_blocked', False)

            if query and query not in (peer.get('peer_name', '').lower() or '') and query not in (peer.get('peer_ip', '').lower() or ''):
                continue

            if filter_value == "active" and is_banned:
                continue
            if filter_value == "inactive" and not is_banned:
                continue

            data_limit = parse_limit_to_bytes(peer.get('limit', ""))
            used_data = peer.get('used', 0)
            if data_limit is not None:
                remaining_data = peer.get('remaining', max(0, data_limit - used_data))
                peer['remaining_human'] = format_size(remaining_data)
            else:
                peer['remaining_human'] = "Unlimited"

            peer['used_human'] = format_size(used_data)
            peer['limit_human'] = format_size(data_limit) if data_limit else "Unlimited"

            peer['status'] = 'active' if not is_banned else 'inactive'
            filtered_peers.append(peer)

        return jsonify({
            "peers": filtered_peers,
            "count": len(filtered_peers)
        })

    except Exception as e:
        app.logger.error(f"Error in search-peers: {e}")
        return jsonify({"error": "An internal error occurred."}), 500



@app.route("/api/peers", methods=["GET"])
def obtain_peers():
    config_file = request.args.get("config", "wg0.conf")
    page = int(request.args.get("page", 1))  
    limit = int(request.args.get("limit", 10))  
    fetch_all = request.args.get("fetch_all", "false").lower() == "true"  

    try:
        peers_file = obtain_peers_file(config_file)
        peers_metadata = load_peers_from_json(peers_file)

        filtered_peers = [p for p in peers_metadata if p.get("config") == config_file]

        for peer in filtered_peers:
            peer["peer_name"] = peer.get("peer_name", "Unnamed Peer")
            peer["peer_ip"] = peer.get("peer_ip", "N/A")
            peer["public_key"] = peer.get("public_key", "N/A")
            peer["used_human"] = bytes_to_readable(peer.get("used", 0))
            peer["remaining_human"] = bytes_to_readable(peer.get("remaining", 0))
            peer["limit_human"] = bytes_to_readable(convert_to_bytes(peer["limit"]))

        if fetch_all:
            response = {
                "peers": filtered_peers,
                "total_peers": len(filtered_peers),
            }
        else:
            total_peers = len(filtered_peers)
            start = (page - 1) * limit
            end = start + limit
            paginated_peers = filtered_peers[start:end]

            total_pages = (total_peers + limit - 1) // limit

            response = {
                "peers": paginated_peers,
                "total_peers": total_peers,
                "total_pages": total_pages,
                "current_page": page,
            }

        return jsonify(response)
    except Exception as e:
        return jsonify(error=f"Error in loading peers: {str(e)}"), 500



@app.route("/api/metrics", methods=["GET"])
@limiter.limit("20 per minute")
def obtain_metrics():

    try:
        metrics = cache.get("metrics")
        if not metrics:
            raise ValueError("Metrics are not available.")

        if isinstance(metrics, str):
            metrics = json.loads(metrics)

        return jsonify(metrics)
    except Exception as e:
        print(f"error in fetching metrics: {e}")
        return jsonify(
            cpu="Unavailable",
            ram="Unavailable",
            disk={"used": "N/A", "total": "N/A"},
            uptime="N/A",
            error=str(e)
        ), 500


@app.route("/api/edit-peer", methods=["POST"])
@limiter.limit("20 per minute")
@validate_json(schema=edit_peer_schema)
def edit_peer():
    try:
        data = request.json
        peer_name = data.get("peerName")
        config_file = data.get("configFile")

        if not config_file or not os.path.isfile(f"{WIREGUARD_CONFIG_DIR}/{config_file}"):
            return jsonify({"error": f"Invalid or missing config file: {config_file}"}), 400

        if not peer_name or not re.match(r'^[a-zA-Z0-9_-]+$', peer_name):
            return jsonify({
                "error": "Wrong peer name. Only letters, numbers, underscores, and dashes are allowed."
            }), 400

        new_limit = data.get("dataLimit")
        if new_limit:
            if not re.match(r'^\d+(MiB|GiB)$', new_limit):
                return jsonify({"error": "Wrong data limit. Must be a number followed by MiB or GiB."}), 400
            numeric_limit = int(new_limit[:-3])
            if numeric_limit <= 0 or numeric_limit > 1024: 
                return jsonify({"error": "Data limit must be between 1 and 1024 MiB/GiB."}), 400

        new_dns = data.get("dns")

        expiry_months = int(data.get("expiryMonths") or 0)
        expiry_days = int(data.get("expiryDays") or 0)
        expiry_hours = int(data.get("expiryHours") or 0)
        expiry_minutes = int(data.get("expiryMinutes") or 0)

        if expiry_months < 0 or expiry_days < 0 or expiry_hours < 0 or expiry_minutes < 0:
            return jsonify({"error": "Expiry times cannot be negative."}), 400

        with json_lock:
            peers = load_peers_with_lock(config_file)
            peer = next((p for p in peers if p["peer_name"] == peer_name), None)
            if not peer:
                return jsonify({"error": f"Peer {peer_name} not found in {config_file}"}), 404

            if new_limit:
                peer["limit"] = new_limit
                peer["remaining"] = max(0, convert_to_bytes(new_limit) - peer.get("used", 0))

            if new_dns:
                peer["dns"] = new_dns

            total_minutes = (
                expiry_months * 30 * 24 * 60 +  
                expiry_days * 24 * 60 +        
                expiry_hours * 60 +            
                expiry_minutes                
            )

            if total_minutes > 0:
                peer["expiry_time"] = {
                    "months": expiry_months,
                    "days": expiry_days,
                    "hours": expiry_hours,
                    "minutes": expiry_minutes
                }
                peer["remaining_time"] = total_minutes

            save_peers_with_lock(config_file, peers)

        return jsonify({"message": "Peer updated successfully", "peer": peer})

    except Exception as e:
        print(f"error in editing peer: {e}")
        return jsonify({"error": f"Couldn't update peer: {str(e)}"}), 500




@app.route("/api/wireguard-details", methods=["GET"])
def wireguard_details():
    config_file = request.args.get("config", "wg0.conf")
    
    try:
        interface_name = sanitize_interface_name(config_file.split(".")[0])

        ip_path = "ip" 

        result = subprocess.run(
            [ip_path, "link", "show", interface_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0:
            is_active = "state UP" in result.stdout or "state UNKNOWN" in result.stdout
        else:
            is_active = False

        uptime = obtain_system_uptime()
        server_details = server_config_details(config_file)

        config_path = os.path.join(WIREGUARD_CONFIG_DIR, config_file)
        ip_address, dns = None, None
        if os.path.exists(config_path):
            with open(config_path, "r") as file:
                for line in file:
                    if line.startswith("Address"):
                        ip_address = line.split("=")[1].strip()
                    elif line.startswith("DNS"):
                        dns = line.split("=")[1].strip()

        return jsonify({
            "interface": interface_name,
            "active": is_active,
            "uptime": uptime,
            "private_key": server_details.get("private_key", "N/A"),
            "public_key": server_details.get("public_key", "N/A"),
            "ip": ip_address or "N/A",
            "port": server_details.get("listen_port", "N/A"),
            "dns": dns or "N/A",
        })

    except ValueError as e:
        return jsonify(error=str(e)), 400  
    except Exception as e:
        print(f"error in fetching Wireguard details for {config_file}: {e}")
        return jsonify(error=f"Couldn't retrieve Wireguard details: {str(e)}"), 500

@app.route("/api/get-interfaces", methods=["GET"])
def obt_interfaces():
    try:
        interfaces = [f for f in os.listdir("/etc/wireguard") if f.endswith(".conf")]
        interfaces = [os.path.splitext(f)[0] for f in interfaces]  
        return jsonify(interfaces=interfaces)
    except Exception as e:
        logging.error(f"error in fetching interfaces: {e}")
        return jsonify(error=f"Couldn't fetch interfaces: {e}"), 500


decrement_lock = Lock()

def decrease_remaining_time():
    if not decrement_lock.acquire(blocking=False):
        logging.info("Skipping expiry timer as another instance is already running.")
        return
    logging.info("Acquired decrement lock.")

    try:
        print("INFO: Starting expiry job.")

        config_files = [f for f in os.listdir(WIREGUARD_CONFIG_DIR) if f.endswith(".conf")]

        for config_file in config_files:
            peers_file = obtain_peers_file(config_file)

            def load_peers_with_lock():
                try:
                    with open(peers_file, "r") as f:
                        fcntl.flock(f, fcntl.LOCK_SH)  
                        peers_data = json.load(f)
                        fcntl.flock(f, fcntl.LOCK_UN)  
                    return peers_data
                except FileNotFoundError:
                    print(f"INFO: {peers_file} not found. Initializing empty peer list.")
                    return []  
                except Exception as e:
                    print(f"ERROR: Couldn't load peers from {peers_file}: {e}")
                    return []

            def save_peers_with_lock(peers_data):
                try:
                    with open(peers_file + '.tmp', "w") as temp_file:
                        fcntl.flock(temp_file, fcntl.LOCK_EX)  
                        json.dump(peers_data, temp_file, indent=4)
                        fcntl.flock(temp_file, fcntl.LOCK_UN)  

                    os.rename(peers_file + '.tmp', peers_file)
                    print(f"INFO: Successfully saved {peers_file} with lock.")
                except Exception as e:
                    print(f"ERROR: Couldn't save peers to {peers_file}: {e}")

            peers = load_peers_with_lock()
            print(f"INFO: Loaded peers from {peers_file}. Total peers: {len(peers)}")

            unique_peers = set()
            for peer in peers:
                peer_ip = peer.get("peer_ip")
                print(f"DEBUG: Checking peer '{peer['peer_name']}' with IP {peer_ip}")

                if peer_ip in unique_peers:
                    print(f"DEBUG: Skipping duplicate peer '{peer['peer_name']}'")
                    continue
                unique_peers.add(peer_ip)

                if peer.get("used", 0) > 0 and not peer.get("first_usage", False):
                    peer["first_usage"] = True
                    print(f"INFO: First usage detected for peer '{peer['peer_name']}'.")

                if peer.get("first_usage") and not peer.get("expiry_blocked", False) and peer.get("remaining_time", 0) > 0:
                    old_time = peer["remaining_time"]
                    peer["remaining_time"] -= 1
                    print(f"INFO: Remaining time for peer '{peer['peer_name']}' decremented from {old_time} to {peer['remaining_time']}.")

                    if peer["remaining_time"] <= 0:
                        print(f"INFO: Remaining time for peer '{peer['peer_name']}' is 0. Blocking the peer due to expired time.")
                        if add_blackhole_route(peer["peer_ip"]):
                            peer["expiry_blocked"] = True
                            print(f"WARNING: Peer '{peer['peer_name']}' has been blocked due to expired time.")
                        else:
                            print(f"ERROR: Couldn't add blackhole route for peer '{peer['peer_name']}'.")

            save_peers_with_lock(peers)

    except Exception as e:
        print(f"ERROR: An error occurred in expiry timer: {e}")

    finally:
        decrement_lock.release()  
        print("INFO: Finished expiry timer job.")



def track_peer_usage(peer_ip):

    config_files = [f for f in os.listdir(WIREGUARD_CONFIG_DIR) if f.endswith(".conf")]

    for config_file in config_files:
        peers_file = f"{config_file.split('.')[0]}.json"
        peers = load_peers_from_json(peers_file)

        for peer in peers:
            if peer['peer_ip'] == peer_ip:
                if peer.get("first_usage", False):
                    print(f"DEBUG: First usage already registered for peer {peer['peer_name']} in {peers_file}. No reset performed.")
                    return {"message": "Usage already tracked."}

                if peer.get("used", 0) > 0:
                    peer["first_usage"] = True

                    expiry_time = peer.get("expiry_time", {})
                    peer["remaining_time"] = (
                        expiry_time.get("months", 0) * 30 * 24 * 60
                        + expiry_time.get("days", 0) * 24 * 60
                        + expiry_time.get("hours", 0) * 60
                        + expiry_time.get("minutes", 0)
                    )
                    print(f"DEBUG: First usage set to True and remaining time initialized to {peer['remaining_time']} minutes for peer {peer['peer_name']} in {peers_file}.")

                    save_peers_to_json(peers_file, peers)
                    return {"message": f"First usage registered for peer {peer['peer_name']}"}

                print(f"DEBUG: No traffic used yet for peer {peer['peer_name']} in {peers_file}.")
                return {"error": "No traffic used yet."}

    print("DEBUG: Peer with IP {peer_ip} not found in any config.")
    return {"error": "Peer not found."}


def clean_invalid_jobs(scheduler):
    for job_id in ["backup_json", "backup_wireguard"]:
        try:
            job = scheduler.get_job(job_id)
            if job:
                logging.info(f"Removing stale job: {job_id}")
                scheduler.remove_job(job_id)
        except JobLookupError:
            logging.warning(f"Job {job_id} not found in the scheduler.")


GEO_PATH = "/usr/local/etc/xray/config.json"

@app.route('/api/get-active-geosites', methods=['GET'])
def get_active_geosites():
    try:
        with open(GEO_PATH, 'r') as config_file:
            config_data = json.load(config_file)
        
        active_geosites = []
        for rule in config_data.get('routing', {}).get('rules', []):
            if rule.get('type') == 'field' and rule.get('outboundTag') == 'warp':
                active_geosites.extend(rule.get('domain', []))
        
        return jsonify({"active_geosites": active_geosites})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/track-usage", methods=["POST"])
def handle_track_usage():
    data = request.get_json()
    peer_ip = data.get("peerIp")
    
    if not peer_ip:
        return jsonify({"error": "Peer IP is required"}), 400
    
    result = track_peer_usage(peer_ip)
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify({"message": f"Countdown started for peer with IP {peer_ip}"})


def create_shortlinks():

    if not os.path.exists(SHORT_LINKS_FILE):
        try:
            with open(SHORT_LINKS_FILE, "w") as file:
                json.dump({}, file) 
            print(f"{SHORT_LINKS_FILE} created successfully.")
        except Exception as e:
            print(f"Error creating {SHORT_LINKS_FILE}: {str(e)}")
    else:
        print(f"{SHORT_LINKS_FILE} already exists.")

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite') 
}
executors = {
    'default': ThreadPoolExecutor(10), 
}
job_defaults = {
    'coalesce': True,  
    'misfire_grace_time': 30  
}


scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=system_timezone
)



if __name__ == "__main__":
    create_shortlinks()
    config = load_config()
    flask_port = config["flask"]["port"]
    use_tls = config["flask"]["tls"]
    cert_path = config["flask"].get("cert_path")
    key_path = config["flask"].get("key_path")
    debug_mode = config["flask"].get("debug", False)
    auto_backup_int = config["wireguard"].get("auto_backup_int", 30)

    if use_tls and cert_path:
        try:
            flask_host = cert_path.split("/live/")[1].split("/")[0] 
        except IndexError:
            raise ValueError("Invalid cert_path format. Expected format: '/etc/letsencrypt/live/<domain>/fullchain.pem'")
    else:
        flask_host = "localhost"  

    setup_logging(debug_mode)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_file = os.path.join(BASE_DIR, "db.json")

    if not os.path.exists(db_file):
        with open(db_file, "w") as file:
            json.dump({}, file)
        logging.info(f"Created new database file: {db_file}")
    else:
        try:
            with open(db_file, "r") as file:
                json.load(file)
            logging.info(f"Database file '{db_file}' is valid.")
        except json.JSONDecodeError:
            with open(db_file, "w") as file:
                json.dump({}, file)
            logging.warning(f"Wrong JSON detected in '{db_file}'. Resetting to an empty dictionary.")

    reload_blocked_peers()
    logging.info("Clearing invalid jobs from the database...")
    clean_invalid_jobs(scheduler)
    scheduler.remove_all_jobs()

    logging.info("Starting Flask application.")

    with tempfile.NamedTemporaryFile(delete=False) as temp_lock_file:
        scheduler_lock_path = temp_lock_file.name  

    scheduler_lock = InterProcessLock(scheduler_lock_path)

    if scheduler_lock.acquire(blocking=False):
        try:
            logging.info("Acquired lock. Initializing BackgroundScheduler.")

            if not scheduler.get_job("decrease_time"):
                logging.info("Adding decrease_remaining_time job.")
                scheduler.add_job(
                    decrease_remaining_time,
                    "interval",
                    minutes=1,
                    id="decrement_time",
                    max_instances=1,
                    replace_existing=True
                )

            if not scheduler.get_job("monitor_traffic"):
                logging.info("Adding monitor_traffic job.")
                scheduler.add_job(
                    monitor_traffic,
                    "interval",
                    seconds=23,
                    id="monitor_traffic",
                    max_instances=1,
                    replace_existing=True
                )

            if not scheduler.get_job("automated_backup"):
                logging.info(f"Adding automated_backup job with interval {auto_backup_int} minutes.")
                scheduler.add_job(
                    create_automated_backup,
                    "interval",
                    minutes=auto_backup_int,
                    id="automated_backup",
                    max_instances=1,
                    replace_existing=True,
                )

            if not scheduler.get_job("system_metrics"):
                logging.info("Adding system metrics job.")
                scheduler.add_job(
                    system_metrics_job,
                    trigger=IntervalTrigger(seconds=9),
                    id="system_metrics",
                    max_instances=1,
                    replace_existing=True,
                )

            try:
                system_metrics_job()
                print("Metrics collected and cached successfully during initialization.")
            except Exception as e:
                print(f"Error during initial metrics collection: {e}")

            scheduler.start()
            logging.info(f"Scheduled Jobs: {scheduler.get_jobs()}")
        except Exception as e:
            logging.error(f"Couldn't initialize scheduler: {e}")
        finally:
            scheduler_lock.release()
            logging.info("Scheduler lock released.")
    else:
        logging.warning("Scheduler is already running. Skipping initialization.")

    class GunicornApp(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    try:
        gunicorn_config = config["gunicorn"]
        options = {
            "bind": f"0.0.0.0:{flask_port}",
            "workers": gunicorn_config.get("workers", 2),
            "threads": gunicorn_config.get("threads", 1),
            "loglevel": gunicorn_config.get("loglevel", "info"),
            "timeout": gunicorn_config.get("timeout", 120),
            "accesslog": gunicorn_config.get("accesslog", "-") if gunicorn_config.get("accesslog") != "" else None,
            "errorlog": gunicorn_config.get("errorlog", "-") if gunicorn_config.get("errorlog") != "" else None,
        }

        if use_tls:
            if not cert_path or not key_path:
                raise ValueError("TLS is enabled, but cert_path or key_path is not configured in config.yaml.")
            options.update({
                "certfile": cert_path,
                "keyfile": key_path,
            })

        protocol = "https" if use_tls else "http"

        homepage_url = f"{protocol}://{flask_host}:{flask_port}/"
        print(f"Application running at {homepage_url}")
        logging.info(f"Application running at {homepage_url}")

        logging.info("Starting Gunicorn server.")
        GunicornApp(app, options).run()

    except Exception as e:
        logging.error(f"Couldn't start Gunicorn server: {e}")

    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutting down application.")
        if scheduler:
            scheduler.shutdown(wait=False)


