import requests
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- CONFIGURATION ---
BOT_TOKEN = "8661349935:AAGiQix2OBzVCTjmtz6ZGtGTNQjSzfL1yOk"  # Enter your Bot Token here
EXTERNAL_API_URL = ""  # Enter your API URL here (e.g., https://api.example.com/lookup?phone=)

# --- DUMMY HTTP SERVER ---
# Some platforms require a binding port to keep the process alive.
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running...")

def run_http_server():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, DummyHandler)
    print("Dummy HTTP server started on port 8080")
    httpd.serve_forever()

# --- BOT LOGIC ---
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

def handle_updates():
    offset = 0
    print("Bot started... Press Ctrl+C to stop.")
    
    while True:
        try:
            # Long polling: timeout=30 means it waits 30s for a new message
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url).json()

            if not response.get("ok"):
                print(f"API Error: {response.get('description')}")
                time.sleep(5)
                continue

            for update in response.get("result", []):
                update_id = update["update_id"]
                offset = update_id + 1  # Increment offset to acknowledge message
                
                if "message" not in update:
                    continue
                
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")

                # 1. Handle /start command
                if text == "/start":
                    keyboard = {
                        "keyboard": [[{"text": "📱 Phone Lookup"}]],
                        "resize_keyboard": True,
                        "one_time_keyboard": False
                    }
                    send_message(chat_id, "Welcome! Use the button below to start.", keyboard)

                # 2. Handle Button Click
                elif text == "📱 Phone Lookup":
                    send_message(chat_id, "📞 Send 10 digit mobile number:")

                # 3. Handle Phone Number Input (10 digits)
                elif text.isdigit() and len(text) == 10:
                    # Inform user lookup is happening
                    send_message(chat_id, "<i>Searching records...</i>")
                    
                    try:
                        # Call External API
                        api_res = requests.get(f"{EXTERNAL_API_URL}{text}")
                        data = api_res.json()
                        
                        # Format JSON for Telegram
                        formatted_json = json.dumps(data, indent=2)
                        message_body = f"<pre>{formatted_json}</pre>"
                        send_message(chat_id, message_body)
                    except Exception as e:
                        send_message(chat_id, f"❌ Error fetching data: {str(e)}")

                # 4. Handle Invalid Input
                else:
                    if text != "/start":
                        send_message(chat_id, "❌ Invalid input. Please send exactly 10 digits.")

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Start the dummy server in a separate thread
    threading.Thread(target=run_http_server, daemon=True).start()
    
    # Start the bot polling
    handle_updates()
