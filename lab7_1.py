import RPi.GPIO as gpio
import threading
import socket

gpio.setmode(gpio.BCM)

# Define PWM LED pins
led_pins = [17, 27, 22]
pwms = []
for pin in led_pins:
    gpio.setup(pin, gpio.OUT)
    p = gpio.PWM(pin, 1000)  # 1 kHz PWM
    p.start(0)
    pwms.append(p)

# Track brightness levels for each LED
brightness = [0, 0, 0]  # percent duty cycle

def set_brightness(led_idx, value):
    brightness[led_idx] = value
    pwms[led_idx].ChangeDutyCycle(value)

def web_page():
    html = f"""
    <html><head><title>LED Brightness Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    html{{font-family: Helvetica; text-align: center;}}
    h1{{color:#0F3376;}}
    input[type=range]{{width:50%;}}
    .button{{background-color:#4CAF50; color:white; padding:10px 24px; font-size:16px; border:none; border-radius:5px; cursor:pointer;}}
    </style></head>
    <body>
    <h1>3-LED Brightness Control</h1>
    <form action="/" method="POST">
      <p><b>Select LED:</b></p>
      <input type="radio" name="led_select" value="0" checked> LED 1<br>
      <input type="radio" name="led_select" value="1"> LED 2<br>
      <input type="radio" name="led_select" value="2"> LED 3<br><br>

      <p><b>Brightness (0–100):</b></p>
      <input type="range" min="0" max="100" name="brightness" value="0"><br><br>

      <button type="submit" class="button">Set Brightness</button>
    </form>

    <h2>Current LED Levels:</h2>
    <p>LED 1: {brightness[0]}%</p>
    <p>LED 2: {brightness[1]}%</p>
    <p>LED 3: {brightness[2]}%</p>
    </body></html>
    """
    return bytes(html, 'utf-8')

def parsePOSTdata(data):
    data_dict = {}
    idx = data.find('\r\n\r\n') + 4
    data = data[idx:]
    pairs = data.split('&')
    for pair in pairs:
        if '=' in pair:
            k, v = pair.split('=')
            data_dict[k] = v
    return data_dict

def serve_web_page():
    while True:
        conn, (client_ip, client_port) = s.accept()
        client_message = conn.recv(2048).decode('utf-8')
        data_dict = parsePOSTdata(client_message)
        if 'led_select' in data_dict and 'brightness' in data_dict:
            led_idx = int(data_dict['led_select'])
            val = int(data_dict['brightness'])
            set_brightness(led_idx, val)

        conn.send(b'HTTP/1.1 200 OK\r\n')
        conn.send(b'Content-Type: text/html\r\n')
        conn.send(b'Connection: close\r\n\r\n')
        conn.sendall(web_page())
        conn.close()

# Socket setup
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(3)

web_thread = threading.Thread(target=serve_web_page)
web_thread.daemon = True
web_thread.start()

try:
    while True:
        pass
except KeyboardInterrupt:
    for p in pwms:
        p.stop()
    gpio.cleanup()
    s.close()
