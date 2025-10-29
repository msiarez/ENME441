import socket
import RPi.GPIO as GPIO

# =========================
# GPIO + PWM SETUP
# =========================
led_pins = [17, 27, 22]      # BCM pin numbers for the 3 LEDs
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
<head><title>LED Brightness Control</title></head>
<body>

<!-- Problem 2: three independent sliders, no submit button -->
<div>
  LED1:
  <input id="s0" type="range" min="0" max="100" value="{brightness[0]}">
  <span id="v0">{brightness[0]}</span>
</div>
<br>
<div>
  LED2:
  <input id="s1" type="range" min="0" max="100" value="{brightness[1]}">
  <span id="v1">{brightness[1]}</span>
</div>
<br>
<div>
  LED3:
  <input id="s2" type="range" min="0" max="100" value="{brightness[2]}">
  <span id="v2">{brightness[2]}</span>
</div>

<script>
// Attach input listeners that (1) update the % readout and (2) POST to the server.
function wireSlider(idx) {{
  var s = document.getElementById('s' + idx);
  var v = document.getElementById('v' + idx);
  function send(val) {{
    // POST as application/x-www-form-urlencoded
    fetch('/', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
      body: 'led=' + idx + '&brightness=' + encodeURIComponent(val)
    }}).catch(function(e){{ console.log(e); }});
  }}
  // live update the number and send to server on every change
  s.addEventListener('input', function() {{
    v.textContent = s.value;
    send(s.value);
  }});
}}

// Wire all three sliders
wireSlider(0);
wireSlider(1);
wireSlider(2);
</script>

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
