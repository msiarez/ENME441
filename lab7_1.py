import socket
import RPi.GPIO as GPIO

# =========================
#  GPIO + PWM SETUP
# =========================
led_pins = [17, 27, 22]       # BCM pin numbers for the 3 LEDs
freq = 1000                 # PWM frequency (Hz)
brightness = [0, 0, 0]      # store current brightness % for each LED
pwms = []

GPIO.setmode(GPIO.BCM)
for pin in led_pins:
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, freq)
    pwm.start(0)
    pwms.append(pwm)


# =========================
#  BRIGHTNESS CONTROL
# =========================
def change_brightness(index, value):
    """Clamp and set LED brightness."""
    try:
        val = int(value)
    except ValueError:
        val = 0
    val = max(0, min(100, val))       # Clamp 0–100
    brightness[index] = val
    pwms[index].ChangeDutyCycle(val)


# =========================
#  POST DATA PARSER
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
#  HTML PAGE BUILDER
# =========================
def web_page(selected_led=0):
    """Generate an HTML form showing current brightness for all LEDs."""
    c0 = 'checked' if selected_led == 0 else ''
    c1 = 'checked' if selected_led == 1 else ''
    c2 = 'checked' if selected_led == 2 else ''

    html = f'''
<html>
<head><title>LED Brightness Control</title></head>
<body>
<form action="/" method="POST">

  LED Brightness Control<br><br>

  Brightness level:<br>
  <input type="range" name="brightness" min="0" max="100" value="{brightness[selected_led]}"> {brightness[selected_led]}%<br><br>

  Select LED:<br>
  <input type="radio" name="led" value="0" {c0}> LED 1 ({brightness[0]}%)<br>
  <input type="radio" name="led" value="1" {c1}> LED 2 ({brightness[1]}%)<br>
  <input type="radio" name="led" value="2" {c2}> LED 3 ({brightness[2]}%)<br><br>

  <input type="submit" value="Change Brightness">
</form>
</body>
</html>
'''
    return bytes(html, "utf-8")


# =========================
#  WEB SERVER LOOP
# =========================
def serve_web_page():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))  # Port 80 requires sudo
    s.listen(1)
    print("Server running — visit http://raspberrypi.local or Pi's IP in browser")

    while True:
        print("Waiting for connection...")
        conn, addr = s.accept()
        print(f"Connection from {addr}")
        request = conn.recv(1024)

        selected_led = 0  # default LED

        if b"POST" in request:
            post_data = parsePOSTdata(request)
            if "led" in post_data and "brightness" in post_data:
                try:
                    led_index = int(post_data["led"])
                    selected_led = led_index
                    value = int(post_data["brightness"])
                    change_brightness(led_index, value)
                except Exception as e:
                    print("Error parsing POST:", e)

        # Send HTTP response
        conn.send(b"HTTP/1.1 200 OK\r\n")
        conn.send(b"Content-Type: text/html\r\n")
        conn.send(b"Connection: close\r\n\r\n")
        conn.sendall(web_page(selected_led))
        conn.close()


# =========================
#  MAIN
# =========================
try:
    serve_web_page()
except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    for p in pwms:
        p.stop()
    GPIO.cleanup()
