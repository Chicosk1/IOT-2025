import RPi.GPIO as gpio
import time as delay

gpio.setmode(gpio.BOARD)

pin_t = 15
pin_e = 16

led_vermelho = 11
led_verde    = 13

lixeira_V = 20
tempo_d = 0

gpio.setup(led_vermelho, gpio.OUT)
gpio.setup(led_verde   , gpio.OUT)

gpio.setup(pin_t, gpio.OUT)
gpio.setup(pin_e, gpio.IN)

def distancia():
    gpio.output(pin_t, True)
    delay.sleep(0.000001)
    gpio.output(pin_t, False)

    tempo_i = delay.time()
    tempo_f = delay.time()
    
    while gpio.input(pin_e) == False:
        tempo_i = delay.time()
    while gpio.input(pin_e) == True:
        tempo_f = delay.time()
        
    tempo_d   = tempo_f  - tempo_i
    distancia = (tempo_d * 34300)/2

    return distancia

while True:
    valor_lido = distancia()
    espaco_d = (valor_lido/lixeira_V)*100

    if valor_lido < 5:
        gpio.output(led_vermelho, True)
        gpio.output(led_verde, False)
    else:
        gpio.output(led_vermelho, False)
        gpio.output(led_verde, True)

    print('Distancia = %.1f cm' % valor_lido)
    print('EspaÃ§o Disponivel na Lixeira %.1f' % espaco_d, '%')
    
    delay.sleep(2)