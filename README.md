#  Spotify OLED Display - ESP32 + Discord Bot

This project provides a real-time display of your currently playing Spotify track on an ESP32 connected to a 1.3" OLED screen (SH1106 128x64). It features synced lyrics, idle eye animations, a progress bar, and an animated equalizer, all powered by a Discord bot.

_This version has been modified by A-flp for personal use and learning, with significant parts rewritten in English._

##  Key Features & Benefits

*   **Real-time Spotify Track Display**: See what's playing instantly, including artist and song title.
*   **Synced Lyrics**: Enjoy lyrics displayed in sync with the music, enhancing the listening experience.
*   **Dynamic Visual Enhancements**:
    *   **Idle Eye Animations**: Engaging and playful animations when no music is playing.
    *   **Progress Bar**: Visual feedback on the current track's progression.
    *   **Animated Equalizer**: Dynamic visualizer that responds to music (simulated or actual, based on implementation).
*   **Cross-platform Integration**: Leverages Discord's Rich Presence for Spotify data, making it easy to use across different devices where Discord is active.
*   **Standalone Display**: Once configured, the ESP32 unit works independently to fetch and display music information.

##  Prerequisites & Dependencies

To set up and run this project, you will need:

### Hardware
*   **ESP32 Development Board**: Any ESP32 board (e.g., ESP32-WROOM-32).
*   **OLED Display**: 1.3" SH1106 128x64 OLED display (I2C communication).
*   **Jumper Wires & Breadboard**: For connecting components.

### Software
*   **Python 3.x**: For the Discord bot (`bot.py`).
*   **Arduino IDE**: For flashing the ESP32 firmware (`esp32.ino`).
    *   **ESP32 Board Package**: Install via Arduino Boards Manager.
    *   **Required Arduino Libraries**:
        *   `Adafruit GFX Library`
        *   `Adafruit SH1106 Library` (or a compatible SH1106 library like `U8g2` for SH1106)
        *   `ArduinoJson`
*   **Discord Account**: And permission to create a Discord Application for the bot.
*   **Spotify Account**: To play music and enable Discord Rich Presence.

### Python Dependencies (for `bot.py`)
Install using pip
```bash
pip install -r requirements.txt
```
(Note: `dataclasses` is usually built-in for Python 3.7+ but listed in `bot.py` snippet for clarity.)

##  Installation & Setup

Follow these steps to get your Spotify OLED display up and running.

### 1. Clone the Repository
Start by cloning the project repository to your local machine:
```bash
git clone https://github.com/A-flp/Spotify-ESP32.git
cd Spotify-ESP32
```

### 2. Discord Bot Setup (`bot.py`)

The `bot.py` script acts as an HTTP server that fetches Spotify Rich Presence data from Discord and serves it to the ESP32.

1.  **Create a Discord Application and Bot**:
    *   Go to the [Discord Developer Portal](https://discord.com/developers/applications).
    *   Click "New Application", give it a name (e.g., "Spotify OLED Bot").
    *   Navigate to the "Bot" tab in the left sidebar and click "Add Bot". Confirm.
    *   **Copy the Bot Token**. This will be used in your `.env` file.
    *   Under "Privileged Gateway Intents", enable `MESSAGE CONTENT INTENT`.
    *   **Invite the bot to your server**: Go to "OAuth2" -> "URL Generator". Select `bot` scope and `Read Messages/View Channels` permission (you might need `Send Messages` for feedback). Copy the generated URL and paste it into your browser to invite the bot to your desired Discord server.

2.  **Configure Environment Variables**:
    Create a file named `.env` in the root directory (`Spotify-ESP32/`) with the following content:
    ```
    DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
    BOT_CHANNEL_ID=YOUR_DISCORD_CHANNEL_ID_HERE
    # The ID of the Discord channel where the bot will listen for commands or report status.
    # Replace with the actual ID of a channel in your server (right-click channel -> Copy ID).
    ```
    *Replace `YOUR_BOT_TOKEN_HERE` with the token copied from Discord Developer Portal.*
    *Replace `YOUR_DISCORD_CHANNEL_ID_HERE` with the ID of a channel in your Discord server where your bot can interact.*

3.  **Install Python Dependencies**:
    Navigate to the project root and install the required Python libraries:
    ```bash
    pip install -r requirements.txt # (If a requirements.txt file exists)
    # Otherwise, use:
    # pip install discord.py aiohttp python-dotenv
    ```

4.  **Run the Discord Bot**:
    Execute the `bot.py` script:
    ```bash
    python bot.py
    ```
    The bot will start a web server, typically on port `8080`. Note the IP address or hostname where your bot is running, as you'll need it for the ESP32. If running on a local machine, find its local IP address (e.g., `ipconfig` on Windows, `ifconfig` or `ip a` on Linux/macOS). If running on a VPS, use its public IP or domain.

### 3. ESP32 Firmware Setup (`esp32.ino`)

The `esp32.ino` sketch connects to your Wi-Fi network, then periodically requests Spotify track information from the running Discord bot's HTTP server.

1.  **Open in Arduino IDE**:
    *   Open `esp32/esp32.ino` in the Arduino IDE.

2.  **Install ESP32 Board Package**:
    *   Go to `File > Preferences`. In "Additional Board Manager URLs", add `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`.
    *   Go to `Tools > Board > Boards Manager...`. Search for "ESP32" and install the "esp32 by Espressif Systems" package.

3.  **Install Libraries**:
    *   Go to `Sketch > Include Library > Manage Libraries...`.
    *   Search and install:
        *   `Adafruit GFX Library`
        *   `Adafruit SH1106 Library` (or `U8g2` for a more universal display library, if you prefer)
        *   `ArduinoJson`
        *   `WiFiManager` (if used in `esp32.ino` for easy Wi-Fi configuration)

4.  **Configure Wi-Fi and Bot Server Details**:
    Modify the following lines in `esp32.ino` to match your network and bot setup. Look for variables related to WiFi SSID, password, and the bot server address:
    ```cpp
    // Wi-Fi Credentials
    const char* ssid = "YOUR_WIFI_SSID";
    const char* password = "YOUR_WIFI_PASSWORD";

    // Discord Bot Server Details
    const char* botServerHost = "YOUR_BOT_SERVER_IP"; // e.g., "192.168.1.100" or "your-vps-domain.com"
    const int botServerPort = 8080; // Default port for the Python bot (check bot.py if unsure)

    // OLED Display I2C Pins (adjust if necessary)
    #define OLED_SDA_PIN 21
    #define OLED_SCL_PIN 22
    #define OLED_RST_PIN -1 // Set to -1 if your OLED has no RST pin or it's tied to VCC
    ```
    Adjust the OLED display pins (`OLED_SDA_PIN`, `OLED_SCL_PIN`, `OLED_RST_PIN`) according to your specific hardware connections.

5.  **Connect ESP32 & Upload Sketch**:
    *   Connect your ESP32 board to your computer via USB.
    *   Select the correct board (`Tools > Board > ESP32 Dev Module` or your specific ESP32 board) and COM port (`Tools > Port`).
    *   Click the "Upload" button (right arrow icon) in the Arduino IDE to flash the firmware to your ESP32.

### 4. Hardware Connections
Connect your SH1106 OLED display to the ESP32 via I2C. A typical connection scheme is:
*   **OLED VCC** to **ESP32 3.3V**
*   **OLED GND** to **ESP32 GND**
*   **OLED SCL** to **ESP32 GPIO 22** (default I2C SCL for ESP32)
*   **OLED SDA** to **ESP32 GPIO 21** (default I2C SDA for ESP32)
*   **OLED RST** (if present and used) to an available ESP32 GPIO pin (e.g., GPIO 16), defined as `OLED_RST_PIN` in `esp32.ino`. If your display doesn't have a RST pin or it's hardwired, set `OLED_RST_PIN` to `-1`.

##  How It Works & Usage

### Overall System Flow
1.  **Spotify Rich Presence**: When you play music on Spotify, it updates your Discord status via Rich Presence, displaying the song information.
2.  **Discord Bot**: The `bot.py` script, running on your PC or a VPS, connects to Discord and monitors your (or a specified user's) Rich Presence for Spotify activity.
3.  **HTTP Server**: The bot simultaneously hosts a simple HTTP server (e.g., at `http://YOUR_BOT_SERVER_IP:8080/spotify-data`). This server processes the Rich Presence data into a clean JSON format.
4.  **ESP32 Request**: The `esp32.ino` firmware, after connecting to your Wi-Fi, periodically makes HTTP requests to the bot's server endpoint.
5.  **Data Display**: The ESP32 receives the JSON data containing track name, artist, lyrics, progress, etc., parses it, and renders it dynamically on the OLED display.

### Using the System
Once both the Discord Bot and ESP32 are successfully set up and running:

1.  **Play music on Spotify**.
2.  Ensure your Discord application is open and your status is visible, displaying Spotify Rich Presence.
3.  The ESP32 will automatically connect to your Wi-Fi and begin fetching data. The OLED display will then show the current track, artist, progress bar, synced lyrics, and animations.

### Bot HTTP Endpoint (for ESP32 consumption)
The bot exposes an HTTP endpoint that the ESP32 consumes. The exact endpoint path is typically defined within `bot.py` (e.g., `/spotify-data`). It returns a JSON object similar to this:

```json
{
  "title": "Song Title Example",
  "artist": "Artist Name",
  "progress_ms": 120000,
  "duration_ms": 240000,
  "album_cover_url": "https://example.com/cover.jpg",
  "lyrics": [
    {"timestamp": 0, "text": "Lyric line one starts here"},
    {"timestamp": 5000, "text": "And the second line follows soon"},
    {"timestamp": 10000, "text": "Timing is everything with lyrics!"}
  ],
  "is_playing": true,
  "timestamp": 1678886400000
}
```
The ESP32 firmware parses this JSON to update the OLED display with all the necessary information.

##  Configuration Options

### `bot.py` (via `.env` file)
*   `DISCORD_TOKEN`: Your Discord bot's authentication token. **(Required)**
*   `BOT_CHANNEL_ID`: The ID of the Discord channel where your bot will operate and potentially send status messages. **(Required)**
*   `WEB_SERVER_HOST`: (Optional, if specified in `bot.py`) The host address for the web server. Default is often `0.0.0.0` (all interfaces).
*   `WEB_SERVER_PORT`: (Optional, if specified in `bot.py`) The port on which the HTTP server listens. Default is often `8080`.

### `esp32.ino`
*   `ssid`: Your Wi-Fi network's SSID.
*   `password`: Your Wi-Fi network's password.
*   `botServerHost`: The IP address or hostname of the machine running your `bot.py` script. This must be accessible by the ESP32 (e.g., local network IP or public VPS IP).
*   `botServerPort`: The port of the HTTP server run by `bot.py`.
*   **OLED Pin Definitions**: (`OLED_SDA_PIN`, `OLED_SCL_PIN`, `OLED_RST_PIN` or similar) Adjust these based on your ESP32's I2C connections and whether you use a reset pin for your OLED.
*   **Display Type**: If using an SSD1306 instead of SH1106, you will need to adjust the display initialization code (e.g., `Adafruit_SH1106` vs `Adafruit_SSD1306`) and potentially the display resolution if it differs.

 Acknowledgments

*   Original concept and base for the Discord bot by [EkiZR](https://github.com/EkiZR).
*   Please refer to the original repository by [EkiZR](https://github.com/EkiZR/Spotify-ESP32) for more information.
*   Inspired by the vibrant open-source community's creativity with ESP32 microcontrollers and OLED displays.
