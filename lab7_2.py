import socket
import RPi.GPIO as GPIO

# =========================
# GPIO + PWM SETUP
# =========================
led_pins = [5, 6, 26]      # BCM pin numbers for the 3 LEDs
freq = 1000                # PWM frequency (Hz)
brightness = [0, 0, 0]     # store current brightness % for each LED
pwms = []

GPIO.setmode(GPIO.BCM)
for pin in led_pins:
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, freq)
    pwm.start(0)
    pwms.append(pwm)


# =========================
# BRIGHTNESS CONTROL
# =========================
def change_brightness(index, value):
    """Clamp and set LED brightness."""
    try:
        val = int(value)
    except ValueError:
        val = 0
    val = max(0, min(100, val))
    brightness[index] = val
    pwms[index].ChangeDutyCycle(val)


# =========================
# POST DATA PARSER
# =========================
def parsePOSTdata(data):
    """Extract key:value pairs from POST body."""
    try:
        data = data.decode('utf-8')
    except:
        data = str(data)
    body_start = data.find('\r\n\r\n') + 4
    body = data[body_start:]
    pairs = body.split('&')
    result = {}
    for p in pairs:
        if '=' in p:
            k, v = p.split('=', 1)
            result[k] = v
    return result


# =========================
# HTML + JAVASCRIPT PAGE BUILDER
# =========================
def web_page():
    """Generate HTML + JavaScript for real-time LED control."""
    html = f'''
<html>
<head>
<title>Live LED Brightness Control</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
html{{font-family: Helvetica; text-align:center;}}
input[type=range]{{width:50%;}}
</style>
<script>
function updateLED(ledIndex, value) {{
  // Display value beside slider
  document.getElementById("val"+ledIndex).innerText = value + "%";

  // Send AJAX POST request
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/", true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  xhr.send("led=" + ledIndex + "&brightness=" + value);
}}
</script>
</head>
<body>
<h1>Live LED Brightness Control</h1>

<p><b>Move the sliders below to adjust LED brightness instantly.</b></p>

<div>
  <p>LED 1: <span id="val0">{brightness[0]}%</span></p>
  <input type="range" min="0" max="100" value="{brightness[0]}" oninput="updateLED(0, this.value)">
</div>

<div>
  <p>LED 2: <span id="val1">{brightness[1]}%</span></p>
  <input type="range" min="0" max="100" value="{brightness[1]}" oninput="updateLED(1, this.value)">
</div>

<div>
  <p>LED 3: <span id="val2">{brightness[2]}%</span></p>
  <input type="range" min="0" max="100" value="{brightness[2]}" oninput="updateLED(2, this.value)">
</div>

</body>
</html>
'''
    return bytes(html, "utf-8")


# =========================
# WEB SERVER LOOP
# =========================
def serve_web_page():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))  # Requires sudo to use port 80
    s.listen(1)
    print("Server running — visit http://raspberrypi.local or Pi's IP")

    while True:
        conn, addr = s.accept()
        request = conn.recv(2048)

        # If POST data received → update LED
        if b"POST" in request:
            post_data = parsePOSTdata(request)
            if "led" in post_data and "brightness" in post_data:
                try:
                    led_index = int(post_data["led"])
                    value = int(post_data["brightness"])
                    change_brightness(led_index, value)
                except Exception as e:
                    print("Error parsing POST:", e)

        # Send updated HTML page on first GET
        conn.send(b"HTTP/1.1 200 OK\r\n")
        conn.send(b"Content-Type: text/html\r\n")
        conn.send(b"Connection: close\r\n\r\n")
        conn.sendall(web_page())
        conn.close()


# =========================
# MAIN
# =========================
try:
    serve_web_page()
except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    for p in pwms:
        p.stop()
    GPIO.cleanup()
