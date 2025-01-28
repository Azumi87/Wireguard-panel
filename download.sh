#!/bin/bash

LIGHT_RED="\033[1;31m"
LIGHT_GREEN="\033[1;32m"
LIGHT_YELLOW="\033[1;33m"
LIGHT_BLUE="\033[1;34m"
CYAN="\033[0;36m"
NC="\033[0m"  

prompt_action() {
    echo -e "${CYAN}Do you want to update or install?${NC}"
    echo -e "${CYAN}════════════════════════════════════════${NC}"
    echo -e "${LIGHT_YELLOW}1)${LIGHT_GREEN} Update${NC}"
    echo -e "${LIGHT_YELLOW}2)${NC} Install/Reinstall${NC}"
    echo -e "${CYAN}════════════════════════════════════════${NC}"
    read -p "Enter (1 or 2): " ACTION_CHOICE
}

update_files() {
    REPO_URL="https://github.com/Azumi67/Wireguard-panel.git"
    TMP_DIR="/tmp/wireguard-panel-update"
    SCRIPT_DIR="/usr/local/bin/Wireguard-panel"

    echo -e "${CYAN}Updating Wireguard Panel...${NC}"

    if [ -d "$TMP_DIR" ]; then
        echo -e "${LIGHT_YELLOW}Removing existing temporary directory...${NC}"
        sudo rm -rf "$TMP_DIR"
    fi

    echo -e "${LIGHT_YELLOW}Cloning repository...${NC}"
    git clone "$REPO_URL" "$TMP_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${LIGHT_RED}[Error]: Couldn't clone repo.${NC}"
        return
    fi

    echo -e "${CYAN}Replacing files...${NC}"

    if [ -f "$SCRIPT_DIR/src/telegram/robot.py" ]; then
        sudo rm "$SCRIPT_DIR/src/telegram/robot.py" && echo -e "${LIGHT_GREEN}✔ Removed: telegram/robot.py${NC}" || echo -e "${LIGHT_RED}✘ Failed to remove: telegram/robot.py${NC}"
    fi

    if [ -f "$SCRIPT_DIR/src/telegram/robot-fa.py" ]; then
        sudo rm "$SCRIPT_DIR/src/telegram/robot-fa.py" && echo -e "${LIGHT_GREEN}✔ Removed: telegram/robot-fa.py${NC}" || echo -e "${LIGHT_RED}✘ Failed to remove: telegram/robot-fa.py${NC}"
    fi

    if [ -f "$TMP_DIR/src/app.py" ]; then
        sudo mv "$TMP_DIR/src/app.py" "$SCRIPT_DIR/src/" && echo -e "${LIGHT_GREEN}✔ Updated: app.py${NC}" || echo -e "${LIGHT_RED}✘ Failed to update: app.py${NC}"
    else
        echo -e "${LIGHT_RED}[Error]: app.py not found in repository.${NC}"
    fi

    if [ -d "$TMP_DIR/src/static" ]; then
        echo -e "${LIGHT_YELLOW}Updating static directory, skipping static/images...${NC}"
        sudo mkdir -p "$SCRIPT_DIR/src/static" 
        for item in "$TMP_DIR/src/static/"*; do
            if [ "$(basename "$item")" != "images" ]; then
                sudo cp -r "$item" "$SCRIPT_DIR/src/static/" && \
                echo -e "${LIGHT_GREEN}✔ Updated: $(basename "$item") in static directory${NC}" || \
                echo -e "${LIGHT_RED}✘ Failed to update: $(basename "$item") in static directory${NC}"
            fi
        done
    else
        echo -e "${LIGHT_RED}[Error]: static directory not found in repository.${NC}"
    fi

    if [ -d "$TMP_DIR/src/templates" ]; then
        sudo rm -rf "$SCRIPT_DIR/src/templates"
        sudo mv "$TMP_DIR/src/templates" "$SCRIPT_DIR/src/" && echo -e "${LIGHT_GREEN}✔ Updated: templates${NC}" || echo -e "${LIGHT_RED}✘ Failed to update: templates${NC}"
    else
        echo -e "${LIGHT_RED}[Error]: templates directory not found in repository.${NC}"
    fi

    if [ -f "$TMP_DIR/src/telegram/robot.py" ]; then
        sudo mv "$TMP_DIR/src/telegram/robot.py" "$SCRIPT_DIR/src/telegram/" && echo -e "${LIGHT_GREEN}✔ Updated: telegram/robot.py${NC}" || echo -e "${LIGHT_RED}✘ Failed to update: telegram/robot.py${NC}"
    else
        echo -e "${LIGHT_RED}[Error]: telegram/robot.py not found in repository.${NC}"
    fi

    if [ -f "$TMP_DIR/src/telegram/robot-fa.py" ]; then
        sudo mv "$TMP_DIR/src/telegram/robot-fa.py" "$SCRIPT_DIR/src/telegram/" && echo -e "${LIGHT_GREEN}✔ Updated: telegram/robot-fa.py${NC}" || echo -e "${LIGHT_RED}✘ Failed to update: telegram/robot-fa.py${NC}"
    else
        echo -e "${LIGHT_RED}[Error]: telegram/robot-fa.py not found in repository.${NC}"
    fi

    if [ -d "$TMP_DIR/src/telegram/static" ]; then
        echo -e "${LIGHT_YELLOW}Updating telegram/static directory, skipping static/images...${NC}"
        sudo mkdir -p "$SCRIPT_DIR/src/telegram/static" 
        for item in "$TMP_DIR/src/telegram/static/"*; do
            if [ "$(basename "$item")" != "images" ]; then
                sudo cp -r "$item" "$SCRIPT_DIR/src/telegram/static/" && \
                echo -e "${LIGHT_GREEN}✔ Updated: $(basename "$item") in telegram/static directory${NC}" || \
                echo -e "${LIGHT_RED}✘ Failed to update: $(basename "$item") in telegram/static directory${NC}"
            fi
        done
    else
        echo -e "${LIGHT_RED}[Error]: telegram/static directory not found in repository.${NC}"
    fi

    if [ -f "$TMP_DIR/src/setup.sh" ]; then
        sudo mv "$TMP_DIR/src/setup.sh" "$SCRIPT_DIR/src/" && echo -e "${LIGHT_GREEN}✔ Updated: setup.sh${NC}" || echo -e "${LIGHT_RED}✘ Failed to update: setup.sh${NC}"
        sudo chmod +x "$SCRIPT_DIR/src/setup.sh" && echo -e "${LIGHT_GREEN}✔ setup.sh is now executable.${NC}" || echo -e "${LIGHT_RED}✘ Failed to make setup.sh executable.${NC}"
    else
        echo -e "${LIGHT_RED}[Error]: setup.sh not found in repository.${NC}"
    fi

    echo -e "${CYAN}Cleaning up temporary files...${NC}"
    sudo rm -rf "$TMP_DIR" && echo -e "${LIGHT_GREEN}✔ Temporary files removed.${NC}" || echo -e "${LIGHT_RED}✘ Failed to remove temporary files.${NC}"

    read -p "$(echo -e "${CYAN}Press Enter to re-run the updated setup.sh...${NC}")"
    echo -e "${CYAN}Running setup.sh from the directory...${NC}"
    cd "$SCRIPT_DIR/src" || { echo -e "${LIGHT_RED}[Error]: Failed to navigate to $SCRIPT_DIR/src.${NC}"; return; }
    sudo ./setup.sh
    if [ $? -ne 0 ]; then
        echo -e "${LIGHT_RED}✘ setup.sh failed. Please check the script for errors.${NC}"
        return
    fi

    echo -e "${LIGHT_GREEN}✔ setup.sh ran successfully.${NC}"
    echo -e "${LIGHT_GREEN}Update completed successfully!${NC}"
}


uninstall_mnu() {
    SCRIPT_DIR=$(dirname "$(realpath "$0")")

    echo -e "${LIGHT_YELLOW}Do you want to uninstall first? ${LIGHT_GREEN}[yes]${NC}/${LIGHT_RED}[no]${NC}: \c"
    read -r CONFIRM
    if [[ "$CONFIRM" != "yes" && "$CONFIRM" != "y" ]]; then
        echo -e "${CYAN}Uninstallation aborted.${NC}"
        return
    fi

    BACKUP_DIR="/etc/wire-backup/uninstall_backups_$(date +%Y%m%d_%H%M%S)"
    WIREGUARD_DIR="/etc/wireguard"
    SYSTEMD_SERVICE="/etc/systemd/system/wireguard-panel.service"
    PANEL_DIR="/usr/local/bin/Wireguard-panel"
    WIRE_SCRIPT="/usr/local/bin/wire"

    echo -e "${INFO}[INFO]${YELLOW}Backing up data to $BACKUP_DIR...${NC}"
    sudo mkdir -p "$BACKUP_DIR"

    if [ -d "$SCRIPT_DIR/db" ]; then
        sudo cp -r "$SCRIPT_DIR/db" "$BACKUP_DIR/db" && echo -e "${SUCCESS}[SUCCESS]Database backed up successfully.${NC}" || echo -e "${ERROR}Couldn't back up database.${NC}"
    else
        echo -e "${WARNING}No database found to back up.${NC}"
    fi

    if [ -d "$SCRIPT_DIR/backups" ]; then
        sudo cp -r "$SCRIPT_DIR/backups" "$BACKUP_DIR/backups" && echo -e "${SUCCESS}[SUCCESS]Backups directory saved successfully.${NC}" || echo -e "${ERROR}Couldn't back up backups directory.${NC}"
    else
        echo -e "${WARNING}No backups directory found to back up.${NC}"
    fi

    if [ -d "$WIREGUARD_DIR" ]; then
        sudo cp -r "$WIREGUARD_DIR" "$BACKUP_DIR/wireguard" && echo -e "${SUCCESS}[SUCCESS]Wireguard configurations backed up successfully.${NC}" || echo -e "${ERROR}Couldn't back up Wireguard configurations.${NC}"
    else
        echo -e "${WARNING}No Wireguard configs found to back up.${NC}"
    fi

    echo -e "${INFO}[INFO]${YELLOW}Disabling and bringing down WireGuard interfaces...${NC}"
    if ls /etc/wireguard/*.conf >/dev/null 2>&1; then
        for iface in $(ls /etc/wireguard/*.conf | xargs -n1 basename | sed 's/\.conf//'); do
            sudo wg-quick down "$iface" && echo -e "${SUCCESS}[SUCCESS]Interface $iface brought down.${NC}" || echo -e "${ERROR}Couldn't bring down interface $iface.${NC}"
        done
    else
        echo -e "${WARNING}No WireGuard interfaces found to bring down.${NC}"
    fi

    if systemctl list-units --type=service | grep -q "telegram-bot-en.service"; then
        echo -e "${INFO}[INFO]${YELLOW}Stopping and disabling English Telegram bot service...${NC}"
        sudo systemctl stop telegram-bot-en.service
        sudo systemctl disable telegram-bot-en.service
        sudo rm -f /etc/systemd/system/telegram-bot-en.service && echo -e "${SUCCESS}[SUCCESS]Telegram bot (English) service removed.${NC}" || echo -e "${ERROR}Couldn't remove Telegram bot (English) service file.${NC}"
        sudo systemctl daemon-reload
    else
        echo -e "${WARNING}No English Telegram bot service found.${NC}"
    fi

    if systemctl list-units --type=service | grep -q "telegram-bot-fa.service"; then
        echo -e "${INFO}[INFO]${YELLOW}Stopping and disabling Farsi Telegram bot service...${NC}"
        sudo systemctl stop telegram-bot-fa.service
        sudo systemctl disable telegram-bot-fa.service
        sudo rm -f /etc/systemd/system/telegram-bot-fa.service && echo -e "${SUCCESS}[SUCCESS]Telegram bot (Farsi) service removed.${NC}" || echo -e "${ERROR}Couldn't remove Telegram bot (Farsi) service file.${NC}"
        sudo systemctl daemon-reload
    else
        echo -e "${WARNING}No Farsi Telegram bot service found.${NC}"
    fi

    if [ -f "$SYSTEMD_SERVICE" ]; then
        echo -e "${INFO}[INFO]${YELLOW}Stopping & disabling Wireguard Panel service...${NC}"
        sudo systemctl stop wireguard-panel.service
        sudo systemctl disable wireguard-panel.service
        sudo rm -f "$SYSTEMD_SERVICE" && echo -e "${SUCCESS}[SUCCESS]Service file removed successfully.${NC}" || echo -e "${ERROR}Couldn't remove service file.${NC}"
        sudo systemctl daemon-reload
    else
        echo -e "${WARNING}Wireguard panel service is not installed.${NC}"
    fi

    echo -e "${INFO}[INFO]${YELLOW}Deleting Wireguard panel files and configs...${NC}"
    sudo rm -rf "$PANEL_DIR" && echo -e "${SUCCESS}[SUCCESS]Removed /usr/local/bin/Wireguard-panel directory.${NC}" || echo -e "${ERROR}Couldn't remove /usr/local/bin/Wireguard-panel directory.${NC}"

    if [ -d "$WIREGUARD_DIR" ]; then
        sudo rm -rf "$WIREGUARD_DIR" && echo -e "${SUCCESS}[SUCCESS]Wireguard configs removed successfully.${NC}" || echo -e "${ERROR}Couldn't remove Wireguard configurations.${NC}"
    fi

    if [ -f "$WIRE_SCRIPT" ]; then
        sudo rm -f "$WIRE_SCRIPT" && echo -e "${SUCCESS}[SUCCESS]Removed wire script from /usr/local/bin.${NC}" || echo -e "${ERROR}Couldn't remove wire script.${NC}"
    else
        echo -e "${WARNING}Wire script not found in /usr/local/bin.${NC}"
    fi

    echo -e "${INFO}[INFO]${YELLOW}Freeing up space...${NC}"
    sudo apt autoremove -y && sudo apt autoclean -y && echo -e "${SUCCESS}[SUCCESS]Space cleared successfully.${NC}" || echo -e "${ERROR}Couldn't free up space.${NC}"

    echo -e "\n${YELLOW}Uninstallation Complete! Backups saved to: ${GREEN}$BACKUP_DIR${NC}"
}


reinstall() {
    uninstall_mnu
    TARGET_DIR="/usr/local/bin/Wireguard-panel"
    REPO_URL="https://github.com/Azumi67/Wireguard-panel.git"

    echo -e "${LIGHT_YELLOW}Reinstalling... Removing old setup directory.${NC}"
    sudo rm -rf "$TARGET_DIR"
    echo -e "${LIGHT_BLUE}Cloning Wireguard-panel repo into $TARGET_DIR...${NC}"
    sudo git clone "$REPO_URL" "$TARGET_DIR"

    if [ $? -ne 0 ]; then
        echo -e "${LIGHT_RED}✘ cloning repository failed. Exiting.${NC}"
        return
    fi

    echo -e "${LIGHT_GREEN}✔ Reinstall/Install complete.${NC}"

    SETUP_SCRIPT="$TARGET_DIR/src/setup.sh"
    if [ -f "$SETUP_SCRIPT" ]; then
        echo -e "${CYAN}Making setup.sh runnable...${NC}"
        sudo chmod +x "$SETUP_SCRIPT" && echo -e "${LIGHT_GREEN}✔ setup.sh is now executable.${NC}" || echo -e "${LIGHT_RED}✘ Failed to make setup.sh executable.${NC}"
    else
        echo -e "${LIGHT_RED}[Error]: setup.sh not found in $TARGET_DIR/src.${NC}"
        return
    fi

    echo -e "${CYAN}Running setup.sh from the directory...${NC}"
    cd "$TARGET_DIR/src"
    sudo ./setup.sh
    if [ $? -ne 0 ]; then
        echo -e "${LIGHT_RED}✘ setup.sh rerunning failed. Please check the script for errors.${NC}"
        return
    fi

    echo -e "${LIGHT_GREEN}✔ setup.sh ran successfully.${NC}"
}


create_wire_script() {
    WIRE_SCRIPT="/usr/local/bin/wire"

    echo -e "${CYAN}Recreating the 'wire' script...${NC}"

    sudo rm -f "$WIRE_SCRIPT"

    echo -e "#!/bin/bash" | sudo tee "$WIRE_SCRIPT" > /dev/null
    echo -e "sudo chmod +x /usr/local/bin/Wireguard-panel/src/setup.sh" | sudo tee -a "$WIRE_SCRIPT" > /dev/null
    echo -e "cd /usr/local/bin/Wireguard-panel/src && sudo ./setup.sh" | sudo tee -a "$WIRE_SCRIPT" > /dev/null

    echo -e "${CYAN}Making 'wire' script runnable...${NC}"
    sudo chmod +x "$WIRE_SCRIPT" && echo -e "${LIGHT_GREEN}✔ 'wire' script is now runnable.${NC}" || echo -e "${LIGHT_RED}✘ Failed to make 'wire' script executable.${NC}"

    if [[ ":$PATH:" != *":/usr/local/bin:"* ]]; then
        echo -e "${CYAN}Adding /usr/local/bin to PATH...${NC}"
        echo "export PATH=\$PATH:/usr/local/bin" | sudo tee -a /etc/profile > /dev/null
        export PATH=$PATH:/usr/local/bin
        echo -e "${LIGHT_GREEN}✔ /usr/local/bin added to PATH.${NC}"
    else
        echo -e "${LIGHT_YELLOW}/usr/local/bin is already in PATH.${NC}"
    fi
}

install_newupdate() {
    VENV_DIR="/usr/local/bin/Wireguard-panel/src/venv"

    echo -e "${CYAN}Activating venv...${NC}"

    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        if [ $? -ne 0 ]; then
            echo -e "${LIGHT_RED}[Error]: Couldn't activate the venv.${NC}"
            return 1
        fi

        echo -e "${LIGHT_YELLOW}Installing jdatetime...${NC}"
        pip install jdatetime
        if [ $? -ne 0 ]; then
            echo -e "${LIGHT_RED}[Error]: Couldn't install jdatetime.${NC}"
            deactivate
            return 1
        fi

        deactivate
        echo -e "${LIGHT_GREEN}✔ jdatetime installed & venv deactivated.${NC}"
    else
        echo -e "${LIGHT_RED}[Error]: Venv not found at $VENV_DIR.${NC}"
        return 1
    fi
}


main() {
    prompt_action  

    if [ "$ACTION_CHOICE" -eq 2 ]; then
        reinstall
    else
        install_newupdate
        update_files
    fi

    create_wire_script

    echo -e "${LIGHT_GREEN}Process complete.${NC}"
}

main
