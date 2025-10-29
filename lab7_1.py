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
