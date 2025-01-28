import os
import subprocess
import platform
import requests 
import json 
import re
import pexpect
import time


def cloudflare_key():
    try:
        print("Adding the Cloudflare WARP GPG key...")
        child = pexpect.spawn("curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg")
        index = child.expect([r"Overwrite\? \(y/N\)", pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        if index == 0:
            child.sendline("y") 
            child.expect(pexpect.EOF)  
        print("GPG key added successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to add GPG key: {e}")

def setup_cloudflare_warp():
    try:
        print("Creating the keyrings directory...")
        run_command("sudo mkdir -p --mode=0755 /usr/share/keyrings", check=True)
        
        cloudflare_key()
        
        print("Adding the Cloudflare WARP repo...")
        repository_content = "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ focal main"
        run_command(f"echo '{repository_content}' | sudo tee /etc/apt/sources.list.d/cloudflare-client.list", check=True)
        
        print("Updating ...")
        run_command("sudo apt update", check=True)
        
        print("Installing Cloudflare WARP...")
        run_command("yes | sudo apt install cloudflare-warp", check=True)
        
        print("Verifying installation...")
        result = run_command("warp-cli --version", check=True)
        print(f"Cloudflare WARP installed successfully. Version: {result}")
    
    except RuntimeError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"unusual error: {e}")

def detect_arch():
    arch = platform.machine()
    if arch == "x86_64":
        return "amd64"
    elif arch in ["armv7l", "armhf"]:
        return "armv7"
    elif arch in ["aarch64", "arm64"]:
        return "arm64"
    else:
        raise Exception(f"architecture not supported: {arch}")


def parse_wireguard(file_path):
    config_data = {}
    with open(file_path, "r") as file:
        lines = file.readlines()
    
    current_section = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            current_section = line.strip("[]")
            config_data[current_section] = {}
        else:
            key, value = map(str.strip, line.split("=", 1))
            if current_section:
                config_data[current_section][key] = value

    return config_data

def rewrite_final_wgcf(file_path, public_ipv4):
    with open(file_path, "r") as file:
        lines = file.readlines()

    updated_lines = []
    inside_interface = False
    post_up_inserted = False 
    post_down_inserted = False  

    for line in lines:
        stripped_line = line.strip()

        if stripped_line == "[Interface]":
            inside_interface = True
            updated_lines.append(line)
            continue

        if inside_interface:
            if not post_up_inserted:
                updated_lines.append(f"PostUp = ip rule add from {public_ipv4} table main\n")
                post_up_inserted = True

            if not post_down_inserted:
                updated_lines.append(f"PostDown = ip rule delete from {public_ipv4} table main\n")
                post_down_inserted = True

            if stripped_line == "" or stripped_line.startswith("["):
                inside_interface = False

        updated_lines.append(line)

    with open(file_path, "w") as file:
        file.writelines(updated_lines)

    print(f"Successfully updated {file_path} with PostUp and PostDown.")


def wireguard_active(interface):
    try:
        output = run_command(f"ip link show {interface}")
        return f"{interface}:" in output 
    except Exception:
        return False 
    
def generate_xray_config(wg_config):
    xray_config = {
        "log": {
            "access": "none",
            "dnsLog": False,
            "error": "",
            "loglevel": "warning",
            "maskAddress": ""
        },
        "routing": {
            "domainStrategy": "AsIs",
            "rules": [
                {
                    "type": "field",
                    "outboundTag": "warp",
                    "domain": [
                        "geosite:meta",
                        "geosite:apple",
                        "geosite:google",
                        "geosite:openai",
                        "geosite:spotify",
                        "geosite:netflix"
                    ]
                },
                {
                    "inboundTag": ["api"],
                    "outboundTag": "api",
                    "type": "field"
                },
                {
                    "outboundTag": "blocked",
                    "protocol": ["bittorrent"],
                    "type": "field"
                }
            ]
        },
        "dns": None,
        "outbounds": [
            {
                "protocol": "freedom",
                "settings": {
                    "domainStrategy": "UseIP",
                    "noises": [],
                    "redirect": ""
                },
                "tag": "direct"
            },
            {
                "protocol": "blackhole",
                "settings": {},
                "tag": "blocked"
            },
            {
                "tag": "warp",
                "protocol": "wireguard",
                "settings": {
                    "mtu": 1320,
                    "secretKey": wg_config["Interface"]["PrivateKey"],
                    "address": wg_config["Interface"]["Address"].split(", "),
                    "workers": 2,
                    "domainStrategy": "ForceIP",
                    "reserved": [144, 243, 209],
                    "peers": [
                        {
                            "publicKey": wg_config["Peer"]["PublicKey"],
                            "allowedIPs": wg_config["Peer"]["AllowedIPs"].split(", "),
                            "endpoint": wg_config["Peer"]["Endpoint"],
                            "keepAlive": 0
                        }
                    ],
                    "kernelMode": False
                }
            }
        ],
        "transport": None,
        "policy": {
            "levels": {
                "0": {
                    "statsUserDownlink": True,
                    "statsUserUplink": True
                }
            },
            "system": {
                "statsInboundDownlink": True,
                "statsInboundUplink": True
            }
        },
        "api": {
            "services": ["HandlerService", "LoggerService", "StatsService"],
            "tag": "api"
        },
        "stats": {},
        "reverse": None,
        "fakedns": None,
        "observatory": None,
        "burstObservatory": None
    }
    return xray_config

def save_xray_config(config, path="/usr/local/etc/xray/config.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        json.dump(config, file, indent=4)
    print(f"Xray configuration saved to {path}")

def download_install_xray():
    print("Downloading the latest Xray release...")
    response = requests.get("https://api.github.com/repos/XTLS/Xray-core/releases/latest")
    if response.status_code == 200:
        latest_release = response.json()
        xray_version = latest_release['tag_name']
        print(f"Latest Xray version: {xray_version}")
        assets = latest_release['assets']
        xray_url = None
        for asset in assets:
            if "linux" in asset["name"] and asset["name"].endswith(".zip"):
                xray_url = asset["browser_download_url"]
                break
        if not xray_url:
            raise Exception("No suitable Xray release found.")
    else:
        raise Exception("getting the latest Xray release info failed.")

    print(f"Downloading Xray from {xray_url}...")
    run_command(f"wget -q --show-progress -O xray.zip {xray_url}")

    if not os.path.exists("xray.zip"):
        raise Exception("Download failed: xray.zip not found.")

    print("Installing Xray...")
    run_command("unzip -o xray.zip -d xray_temp")
    run_command("sudo mv xray_temp/xray /usr/local/bin/")
    run_command("sudo chmod +x /usr/local/bin/xray")
    os.makedirs("/usr/local/etc/xray", exist_ok=True)
    os.makedirs("/usr/local/share/xray", exist_ok=True)
    run_command("sudo mv xray_temp/*.dat /usr/local/share/xray/")
    run_command("rm -rf xray.zip xray_temp")

    print("Xray installed successfully.")


def fetch_publicip():
    services = [
        "https://ifconfig.me",
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://checkip.amazonaws.com",
    ]

    for service in services:
        try:
            print(f"Trying to fetch public IP from {service}...")
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                ip = response.text.strip()
                if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
                    print(f"Successfully fetched public IP: {ip}")
                    return ip
                else:
                    print(f"Invalid IP address detected: {ip}")
        except requests.RequestException as e:
            print(f"Failed to fetch IP from {service}: {e}")

    raise Exception("Unable to determine public IPv4 address from any service.")


def setup_xray_service():
    service_content = """
[Unit]
Description=Xray Service
After=network.target

[Service]
ExecStart=/usr/local/bin/xray -config /usr/local/etc/xray/config.json
Restart=on-failure

[Install]
WantedBy=multi-user.target
    """
    service_path = "/etc/systemd/system/xray.service"
    with open(service_path, "w") as file:
        file.write(service_content)

    run_command("sudo systemctl daemon-reload")
    run_command("sudo systemctl enable xray")
    run_command("sudo systemctl restart xray")
    print("Xray service configured and started.")


def run_command(command, check=False):
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}\nError: {result.stderr}")
    return result.stdout.strip()


install_progress = 0
installing = False

def install_warp():
    global install_progress, installing
    install_progress = 0
    installing = True

    steps = [
        "Step 1: Installing required packages...",
        "Step 2: Fetching wgcf version...",
        "Step 3: Registering WARP account...",
        "Step 4: Generating Wireguard profile...",
        "Step 5: Fetching public IPv4...",
        "Step 6: Configuring and restarting Xray...",
        "Step 7: Downloading geosite and geoip databases..."
    ]

    try:
        for i, step in enumerate(steps):
            print(step)
            install_progress = int((i + 1) / len(steps) * 100)
            update_progress(install_progress)  

            if step == "Step 1: Installing required packages...":
                run_command("sudo apt install -y wireguard curl unzip wget expect")
                print("Step 1: Installed required packages.")
            
            elif step == "Step 2: Fetching wgcf version...":
                response = requests.get("https://api.github.com/repos/ViRb3/wgcf/releases/latest")
                if response.status_code == 200:
                    latest_release = response.json()
                    wgcf_version = latest_release['tag_name'].lstrip('v') 
                else:
                    raise Exception("Failed to fetch the latest wgcf release version.")
                print(f"Latest wgcf version: {wgcf_version}")

                arch = platform.architecture()[0]
                if "64" in arch:
                    arch = "amd64"
                elif "32" in arch:
                    arch = "386"
                else:
                    raise Exception("Unsupported system architecture.")

                wgcf_url = f"https://github.com/ViRb3/wgcf/releases/download/v{wgcf_version}/wgcf_{wgcf_version}_linux_{arch}"
                run_command(f"wget -q --show-progress -O wgcf {wgcf_url}")
                run_command("chmod +x wgcf && sudo mv wgcf /usr/local/bin/")
                print("Step 2: Downloaded and installed wgcf.")

            elif step == "Step 3: Registering WARP account...":
                if not os.path.exists("wgcf-account.toml"):
                    print("Registering Cloudflare WARP account...")
                    try:
                        child = pexpect.spawn("wgcf register")
                        time.sleep(2)
                        child.sendline("")  
                        child.expect(pexpect.EOF)
                        print("Step 3: Registered Cloudflare WARP account.")
                    except pexpect.exceptions.ExceptionPexpect as e:
                        raise RuntimeError(f"Failed to register Cloudflare WARP account: {e}")
                else:
                    print("WARP account already exists. Skipping registration.")

            elif step == "Step 4: Generating Wireguard profile...":
                current_dir = os.path.dirname(os.path.abspath(__file__))
                wgcf_profile_path = os.path.join(current_dir, "wgcf-profile.conf")

                if not os.path.exists(wgcf_profile_path):
                    print("Generating Wireguard profile...")
                    run_command("wgcf generate", check=True)
                    print(f"Step 4: Generated Wireguard profile at {wgcf_profile_path}.")
                else:
                    print(f"Wireguard profile already exists at {wgcf_profile_path}.")

            elif step == "Step 5: Fetching public IPv4...":
                public_ipv4 = fetch_publicip()
                print(f"Step 5: VPS Public IPv4: {public_ipv4}")

            elif step == "Step 6: Configuring and restarting Xray...":
                print("Configuring Xray...")
                if not os.path.exists("/usr/local/bin/xray"):
                    download_install_xray()
                if not os.path.exists("/usr/local/etc/xray"):
                    os.makedirs("/usr/local/etc/xray")

                current_dir = os.path.dirname(os.path.abspath(__file__))
                wgcf_profile_path = os.path.join(current_dir, "wgcf-profile.conf")
                wg_config = parse_wireguard(wgcf_profile_path)

                xray_config = generate_xray_config(wg_config)
                xray_config_path = "/usr/local/etc/xray/config.json"
                with open(xray_config_path, "w") as xray_file:
                    json.dump(xray_config, xray_file, indent=4)
                print(f"Xray configuration saved to {xray_config_path}.")
                setup_xray_service()

            elif step == "Step 7: Downloading geosite and geoip databases...":
                run_command(
                    "curl -L -o /usr/local/share/xray/geosite.dat https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat && "
                    "curl -L -o /usr/local/share/xray/geoip.dat https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat"
                )
                run_command("sudo chmod 644 /usr/local/share/xray/{geosite.dat,geoip.dat}")
                print("Step 7: Downloaded geosite and geoip databases.")
            
            time.sleep(2)  

        install_progress = 100 
        update_progress(install_progress) 
        print("WARP and Xray installation complete.")
        return {"message": "WARP and Xray installed and configured successfully!"}

    except Exception as e:
        install_progress = 0 
        update_progress(install_progress)  
        print(f"Error during installation: {e}")
        return {"message": f"Error during installation: {e}"}

    finally:
        installing = False  

install_progress = 0
installing = False


def update_progress(progress):
    with open("install_progress.json", "w") as f:
        json.dump({"progress": progress}, f)

def install_fullwarp():
    global install_progress, installing
    install_progress = 0
    installing = True

    steps = [
        "Step 1: Installing required packages...",
        "Step 2: Fetching the latest wgcf version...",
        "Step 3: Registering WARP account...",
        "Step 4: Generating WARP configuration...",
        "Step 5: Fetching public IPv4...",
        "Step 6: Modifying wgcf-profile.conf...",
        "Step 7: Enabling and starting Wireguard service..."
    ]

    try:
        for i, step in enumerate(steps):
            print(step)
            install_progress = int((i + 1) / len(steps) * 100)
            update_progress(install_progress) 
            print(f"Progress: {install_progress}%")

            if step == "Step 1: Installing required packages...":
                run_command("sudo apt install -y wireguard curl unzip wget expect")
                print("Step 1: Installed required packages.")
            
            elif step == "Step 2: Fetching the latest wgcf version...":
                response = requests.get("https://api.github.com/repos/ViRb3/wgcf/releases/latest")
                if response.status_code == 200:
                    latest_release = response.json()
                    wgcf_version = latest_release['tag_name'].lstrip('v')  
                else:
                    raise Exception("Failed to fetch the latest wgcf release version.")
                print(f"Latest wgcf version: {wgcf_version}")

                arch = detect_arch()
                print(f"Detected architecture: {arch}")

                wgcf_url = f"https://github.com/ViRb3/wgcf/releases/download/v{wgcf_version}/wgcf_{wgcf_version}_linux_{arch}"
                run_command(f"wget -q --show-progress -O wgcf {wgcf_url}")
                run_command("chmod +x wgcf && sudo mv wgcf /usr/local/bin/")
                print("Step 2: Downloaded and installed wgcf.")

            elif step == "Step 3: Registering WARP account...":
                if not os.path.exists("wgcf-account.toml"):
                    print("Registering Cloudflare WARP account...")
                    try:
                        child = pexpect.spawn("wgcf register")
                        time.sleep(2)
                        child.sendline("") 
                        child.expect(pexpect.EOF)
                        print("Step 3: Registered Cloudflare WARP account.")
                    except pexpect.exceptions.ExceptionPexpect as e:
                        raise RuntimeError(f"Failed to register Cloudflare WARP account: {e}")
                else:
                    print("WARP account already exists. Skipping registration.")

            elif step == "Step 4: Generating WARP configuration...":
                if not os.path.exists("wgcf-profile.conf"):
                    run_command("wgcf generate")
                    print("Step 4: Generated WARP configuration.")
                else:
                    print("WARP configuration already exists. Skipping generation.")

            elif step == "Step 5: Fetching public IPv4...":
                public_ipv4 = fetch_publicip()
                print(f"Step 5: VPS Public IPv4: {public_ipv4}")

            elif step == "Step 6: Modifying wgcf-profile.conf...":
                print("Modifying wgcf-profile.conf...")
                wgcf_file_path = "./wgcf-profile.conf"
                new_wgcf_file_path = "/etc/wireguard/wgcf.conf"

                run_command(f"sudo mv {wgcf_file_path} {new_wgcf_file_path}")
                run_command(f"sudo chmod 600 {new_wgcf_file_path}")
                rewrite_final_wgcf(new_wgcf_file_path, public_ipv4)

            elif step == "Step 7: Enabling and starting Wireguard service...":
                print("Checking Wireguard interface status...")
                if wireguard_active("wgcf"):
                    print("Wireguard interface 'wgcf' is already active. Skipping 'wg-quick up'.")
                else:
                    print("Wireguard interface 'wgcf' is not active. Bringing it up...")
                    run_command("sudo wg-quick up wgcf")
                    print("Wireguard interface 'wgcf' brought up successfully.")

                run_command("sudo systemctl enable wg-quick@wgcf")
                print("Wireguard service enabled.")

            time.sleep(2)  

        install_progress = 100  
        update_progress(install_progress)  
        print("Installation complete!")
        return {"message": "WARP and Wireguard installed and configured successfully!"}

    except Exception as e:
        install_progress = 0  
        update_progress(install_progress)  
        print(f"Error during installation: {e}")
    finally:
        installing = False

