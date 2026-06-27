# -*- coding: utf-8 -*-
# runtime.py (VERSION CON INTERFAZ GRAFICA USANDO Tkinter y caracteres ASCII unicamente)

import sys
import json
import threading
import random
# Tkinter es la libreria GUI estandar de Python, compatible con 2.7
import Tkinter as tk
import tkMessageBox # Necesario para el GAME OVER
# Quitamos os y msvcrt ya que la GUI maneja el dibujo y el input
# import os
# import msvcrt 

class Juego:
    def __init__(self, datos_juego):
        self.datos_juego = datos_juego
        self.tipo_juego = self.datos_juego.get('tipo_juego', 'TETRIS')
        config = self.datos_juego.get('config', {})
        self.ancho = config.get('grid_size', [10, 20])[0]
        self.alto = config.get('grid_size', [10, 20])[1]
        self.lives = config.get('lives', 3)
        self.grid = [[0 for _ in range(self.ancho)] for _ in range(self.alto)]
        self.puntuacion = 0 
        self.color_act='#FF0000'
        self.juego_terminado = False
        
        
        # --- Configuracion de la GUI ---
        self.root = tk.Tk()
        self.root.title("BrickScript - " + self.tipo_juego)
        # Configurar la accion al cerrar la ventana ('X' de la barra de titulo)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        
        if self.tipo_juego == "TANKS": self.taman_celda = 12 # Pixeles por celda
        else: self.taman_celda = 25 # Pixeles por celda
        self.ancho_canvas = self.ancho * self.taman_celda
        self.alto_canvas = self.alto * self.taman_celda
        
        # Canvas para dibujar el juego
        if self.tipo_juego == "TANKS": self.canvas = tk.Canvas(self.root, width=self.ancho_canvas, height=self.alto_canvas, bg="#033A01")
        else: self.canvas = tk.Canvas(self.root, width=self.ancho_canvas, height=self.alto_canvas, bg='#111111')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        # Marco lateral para la puntuacion y controles
        self.marco_score = tk.Frame(self.root, width=150, height=self.alto_canvas, bg='#222222')
        self.marco_score.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        self.label_score = tk.Label(self.marco_score, text="PUNTUACION\n0", bg='#222222', fg='white', font=('Consolas', 16, 'bold'))
        self.label_score.pack(pady=40, padx=10)

        if self.tipo_juego == 'TANKS':
           self.label_lives =tk.Label (self.marco_score, text="❤ " * self.lives, bg='#222222', fg='red',font=('Arial',18,'bold'))
           self.label_lives.pack(pady=10)
        
        # Nota: Se ha eliminado 'Q: Salir' de los controles en pantalla
        self.label_controles = tk.Label(self.marco_score, text="CONTROLES\nFlechas: Mover/Rotar", bg='#222222', fg='gray', font=('Consolas', 10))
        self.label_controles.pack(pady=20, padx=10)

        # Configurar eventos de teclado. Usamos <Key> para capturar cualquier tecla
        self.root.bind('<Key>', self.manejar_input_gui)
        self.velocidad_gravedad = 0.1
        
        if self.tipo_juego == 'TETRIS':
            self.pieza_actual = None
            self.pieza_x, self.pieza_y, self.pieza_rotacion = 0, 0, 0
            self.velocidad_gravedad = 0.4
        
        if self.tipo_juego == 'SNAKE':
            self.serpiente_cuerpo = []
            self.serpiente_direccion = (1, 0)
            self.posicion_comida = None
            self.velocidad_gravedad = 0.15
            self.inmortal = False
            self.cabeza = '#00FF00'
            self.cuerpo = '#33CC33'
            self.level=self.datos_juego['shapes'][next(iter(self.datos_juego['shapes']))]['level'] #Nueva variable para definir el nivel
            self.body=self.datos_juego['shapes'][next(iter(self.datos_juego['shapes']))]['body'] #Nueva variable para definir el cuerpo
            if self.level=="ENTUSIASTA": #activar frutas venenosas y power ups
                self.pos_fruta = None
                self.powertime=self.datos_juego['shapes'][next(iter(self.datos_juego['shapes']))]['power_up']
                self.powercool= False
                self.pos_power = None
            if self.level=="NYAN_CAT": #activar nubes y cola colorida solo en nivel Nyan_cat 
             self.nubes = []
             self.velocidad_gravedad = 0.1 
             self.nyan_colors = [
                 '#FF0000',
                 '#FF7F00',
                 '#FFFF00',
                 '#00FF00',
                 '#0000FF',
                 '#4B0082',
                 '#9400D3'
                        ]
        
        if self.tipo_juego == "TANKS":
            self.player_tanks = None
            self.enemy_tanks = []
            self.tank_walls=[]
            self.pos_cura=None
        self.timer_gravedad = 0
        self.ejecutar_evento('ON_START')
        if self.tipo_juego == "TANKS": self.tanks_generar_bordes()
        self.timer_id = None # Para controlar el loop de Tkinter
    def run(self):
        # Inicia el ciclo principal de juego de Tkinter
        self.root.after(50, self.game_loop) 
        self.root.mainloop() 

    def game_loop(self):
        if self.juego_terminado:
            self.mostrar_game_over()
            return

        # Logica de TICK/Gravedad
        # El loop se ejecuta cada 50ms (0.05 segundos)
        self.timer_gravedad += 0.05 
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            self.ejecutar_evento('ON_TICK')

        self.dibujar()

        # Programa el siguiente ciclo de juego
        self.timer_id = self.root.after(50, self.game_loop)

    def cerrar_ventana(self):
        # Detiene el loop de juego de forma segura
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.destroy()
        sys.exit(0)


    def manejar_input_gui(self, event):
        key = event.keysym.upper()
        
        # La opcion de salir con 'Q' ha sido eliminada.
        
        # Mapeo de teclas de flecha
        if self.tipo_juego == 'TETRIS':
            if key == 'UP': self.ejecutar_evento('ON_KEY_UP')
            elif key == 'DOWN': self.ejecutar_evento('ON_KEY_DOWN')
            elif key == 'LEFT': self.ejecutar_evento('ON_KEY_LEFT')
            elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')
        elif self.tipo_juego == 'SNAKE':
            # Llamamos a las funciones internas para Snake
            if key == 'UP': self.snake_cambiar_direccion('UP')
            elif key == 'DOWN': self.snake_cambiar_direccion('DOWN')
            elif key == 'LEFT': self.snake_cambiar_direccion('LEFT')
            elif key == 'RIGHT': self.snake_cambiar_direccion('RIGHT')
        elif self.tipo_juego=='TANKS':
            if key == 'UP': self.tanks_movimiento_player('UP')
            elif key == 'DOWN': self.tanks_movimiento_player('DOWN')
            elif key == 'LEFT': self.tanks_movimiento_player('LEFT')
            elif key == 'RIGHT': self.tanks_movimiento_player('RIGHT')



    def dibujar(self):
        self.canvas.delete("all") # Borrar todo en cada frame
        self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion))

        # Colores
        COLOR_GRID_FIJA = '#343434' # Gris oscuro para las celdas fijadas (Tetris)
        COLOR_WALL = '#FFD700'
        if self.tipo_juego == 'TETRIS' and self.pieza_actual:
            COLOR_PIEZA = self.color_actual
        if self.tipo_juego== "SNAKE":
         COLOR_SNAKE_CABEZA = self.cabeza # Verde brillante
         COLOR_SNAKE_CUERPO = self.cuerpo # Verde normal
         COLOR_FOOD = '#FF0000'      # Rojo
         COLOR_FRUIT = "#ECFC09"     # Amarillo
         COLOR_POWER = "#0D09FC"     # Azul
        if self.tipo_juego == "SNAKE":    
            COLOR_SNAKE_CABEZA = self.cabeza # Verde brillante
            COLOR_SNAKE_CUERPO = self.cuerpo # Verde normal
            COLOR_FOOD = '#FF0000'      # Rojo
            COLOR_FRUIT = "#ECFC09"     # Amarillo
            COLOR_POWER = "#0D09FC"     # Azul
       

        # 1. Dibujar la cuadricula estatica (grid base)
        for y in range(self.alto):
            for x in range(self.ancho):
                if self.grid[y][x] == 1:
                     self.dibujar_celda(x, y, COLOR_GRID_FIJA)

        # 2. Dibujar la pieza actual de Tetris
        if self.tipo_juego == 'TETRIS' and self.pieza_actual:
            matriz_pieza = self.pieza_actual[self.pieza_rotacion]
            for y_offset, fila in enumerate(matriz_pieza):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self.dibujar_celda(self.pieza_x + x_offset, self.pieza_y + y_offset, COLOR_PIEZA)
        

        # 3. Dibujar Snake y Comida
        if self.tipo_juego == 'SNAKE':
            if self.level=="NYAN_CAT":
             for x, y in self.nubes:
                 ts = self.taman_celda

                 px = (x * ts)
                 py = y * ts

                 self.canvas.create_oval(
                 px,
                 py,
                 px + ts,
                 py + ts,
                 fill='white',
                 outline='gray'
                 )

                 self.canvas.create_oval(
                 px + ts//2,
                 py - ts//4,
                 px + ts + ts//2,
                 py + ts - ts//4,
                 fill='white',
                 outline='gray'
                )
             
            # Comida
            if self.posicion_comida:
                x, y = self.posicion_comida
                self.dibujar_celda(x, y, COLOR_FOOD)

            if self.level=="ENTUSIASTA":
                if self.pos_fruta:
                    x, y = self.pos_fruta
                    self.dibujar_celda(x, y, COLOR_FRUIT)
                if self.pos_power:
                    x, y = self.pos_power
                    self.dibujar_celda(x, y, COLOR_POWER)
                
            # Cuerpo de la Serpiente
            for i, segmento in enumerate(self.serpiente_cuerpo):

                x, y = segmento

                if i == 0:
                    if self.level == "NYAN_CAT":
                        self.dibujar_circulo(x, y, COLOR_SNAKE_CABEZA)
                    else:
                        self.dibujar_cuerpo(x, y, COLOR_SNAKE_CABEZA)
                else:
                    color = self.nyan_colors[(i - 1) % len(self.nyan_colors)] \
                        if self.level=="NYAN_CAT" else COLOR_SNAKE_CUERPO

                    self.dibujar_cuerpo(x, y, color)
        for y in range(self.alto):
            for x in range(self.ancho):
                 if self.grid[y][x] == 1:
                   if self.tipo_juego == 'TANKS':
                        self.dibujar_celda(x, y, COLOR_WALL)
                   else:
                        self.dibujar_celda(x, y, COLOR_GRID_FIJA)
        

        if self.tipo_juego == "TANKS":
            if self.pos_cura:
             x,y=self.pos_cura
             self.dibujar_llave(x,y)

            if self.player_tanks:
                self.dibujar_tanque(
                    self.player_tanks['x'],
                    self.player_tanks['y'],
                    self.player_tanks['shape'],
                    self.player_tanks
                )

            for enemigo in self.enemy_tanks:
                self.dibujar_tanque(
                    enemigo['x'],
                    enemigo['y'],
                    enemigo['shape'],
                    enemigo
                ) 
            self.tanks_movimiento_enemy()       



    #Dibujar la figura que toma el cuerpo
    def dibujar_cuerpo(self,x,y,color):
        ts = self.taman_celda # Alias para taman de celda
        if self.body=="CIRCULO":
         x1 = (x * ts)-1
         y1 = (y * ts)-1

         x2 = x1 + ts+1
         y2 = y1 + ts+1

         self.canvas.create_oval(
             x1,
             y1,
             x2,
             y2,
             fill=color,
             outline='black'
            )
        elif self.body=="TRIANGULO":
            x1,y1= (x*ts), y * ts, # punta superior
            x2,y2= (x*ts)+ts, y1, # esquina inferior izquierda
            x3,y3= (x*ts)+ts/2 , y1+ts , # esquina inferior derecha
            self.canvas.create_polygon(
             x1, y1,
             x2, y2,
             x3, y3,
             fill=color,
             outline='black'
            )   
        else:
            x1, y1 = x * ts, y * ts
            x2, y2 = x1 + ts, y1 + ts
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#000000')




    def dibujar_celda(self, x, y, color):
        ts = self.taman_celda # Alias para taman de celda
        x1, y1 = x * ts, y * ts
        x2, y2 = x1 + ts, y1 + ts
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#000000')

    def actualizar_vidas(self):
        self.label_lives.config(text="❤ " * self.lives )
    def perder_vida(self):

        self.lives -= 1

        self.actualizar_vidas()

        if self.lives <= 0:
             self.juego_terminado = True

    #Dibujar cabeza nivel Nyan_Cat
    def dibujar_circulo(self, x, y, color):

        ts = self.taman_celda

        x1 = x * ts
        y1 = y * ts

        x2 = x1 + ts
        y2 = y1 + ts

        self.canvas.create_oval(
        x1,
         y1,
         x2,
         y2,
         fill=color,
         outline='black'
    )
        self.canvas.create_oval(
        x1 + ts*0.25,
        y1 + ts*0.25,
        x1 + ts*0.40,
        y1 + ts*0.40,
        fill='black'
    )

    # Ojo derecho
        self.canvas.create_oval(
         x1 + ts*0.60,
         y1 + ts*0.25,
         x1 + ts*0.75,
         y1 + ts*0.40,
         fill='black')

    def dibujar_llave(self, x, y):
     x=x*self.taman_celda
     y=y*self.taman_celda
     color="#707070"
     escala=0.3
     # Mango
     self.canvas.create_line(
         x, y,
         x+45*escala, y-45*escala,
         width=5*escala,
         capstyle=tk.ROUND,
         fill=color
     )

    # Agujero
     self.canvas.create_oval(
         x-8*escala, y-8*escala,
         x+8*escala, y+8*escala,
         fill="white",
         outline=color,
         width=3*escala
     )

    # Cabeza
     self.canvas.create_arc(
         x+30*escala, y-75*escala,
         x+80*escala, y-25*escala,
         start=40,
         extent=280,
         style=tk.ARC,
         width=14*escala,
         outline=color
     )

    #Dibujar tanques de tanks
    def dibujar_tanque(self, x, y, shape, tanque):
        
        sprite = shape["states"][tanque["rotation"]]

        colores = {
            1: shape['color'],
            2: "#808080",
            3: "#000000"
        }

        for fila_idx, fila in enumerate(sprite):
            for col_idx, valor in enumerate(fila):

                if valor == 0:
                    continue

                self.dibujar_celda(
                    x + col_idx,
                    y + fila_idx,
                    colores[valor]
                )

    #Funcion para obtener una posicion valida de spawneo (tanks)

    def obtener_posicion_valida(self, shape):

        sprite = shape['states'][0]

        alto_sprite = len(sprite)
        ancho_sprite = len(sprite[0])

        while True:

            MARGEN = 1

            x = random.randint(MARGEN, self.ancho - ancho_sprite - MARGEN)
            y = random.randint(MARGEN, self.alto - alto_sprite - MARGEN)

            libre = True

            #Comprobar celda en el grid (para obstaculos)

            for fila_idx in range(alto_sprite):
                for col_idx in range(ancho_sprite):

                    if self.grid[y + fila_idx][x + col_idx] == 1:
                        libre = False
                        break

                if not libre:
                    break
            if not libre:
                continue

            # Verificar jugador
            if self.player_tanks:

                sprite_player = self.player_tanks['shape']['states'][0]

                alto_player = len(sprite_player)
                ancho_player = len(sprite_player[0])

                if not (
                    x + ancho_sprite <= self.player_tanks['x'] or
                    self.player_tanks['x'] + ancho_player <= x or
                    y + alto_sprite <= self.player_tanks['y'] or
                    self.player_tanks['y'] + alto_player <= y
                ):
                    libre = False

            # Verificar enemigos
            for enemigo in self.enemy_tanks:

                sprite_enemy = enemigo['shape']['states'][0]

                alto_enemy = len(sprite_enemy)
                ancho_enemy = len(sprite_enemy[0])

                if not (
                    x + ancho_sprite <= enemigo['x'] or
                    enemigo['x'] + ancho_enemy <= x or
                    y + alto_sprite <= enemigo['y'] or
                    enemigo['y'] + alto_enemy <= y
                ):
                    libre = False
                    break

            if libre:
                return x, y


    def ejecutar_evento(self, nombre_evento):
        if nombre_evento in self.datos_juego['events']:
            for accion in self.datos_juego['events'][nombre_evento]:
                verbo, objeto = accion.get('accion'), accion.get('objeto') 
                if verbo == 'INCREASE_SCORE': self.puntuacion += int(objeto)
                if verbo == 'DECREASE_SCORE': self.puntuacion -= int(objeto)
                if verbo == 'GAME_OVER': self.juego_terminado = True

                if self.tipo_juego == 'TETRIS':
                    if verbo == 'SPAWN':
                      if objeto == "POWER_UP" : self.tetris_spawn_pieza("POWER_UP")
                      else: self.tetris_spawn_pieza()
                    if verbo == 'MOVE': self.tetris_mover_pieza(accion['params'][0])
                    if verbo == 'ROTATE': self.tetris_rotar_pieza()
                if self.tipo_juego == 'SNAKE':
                    if verbo == 'SPAWN' and objeto == 'PLAYER': self.snake_spawn_jugador(accion)
                    if verbo == 'SPAWN' and objeto == 'FOOD': self.snake_spawn_comida()
                    if verbo == 'SPAWN' and objeto == 'FRUIT': self.snake_spawn_fruta()
                    if verbo == 'SPAWN' and objeto == 'POWER_UP': self.snake_spawn_power()
                    if verbo == 'MOVE' and objeto == 'PLAYER': self.snake_mover_jugador()
                    if verbo == 'GROW': self.snake_crecer()
                    if verbo == 'SPAWN' and objeto == 'CLOUD'and self.level=="NYAN_CAT":
                        x, y = accion['params'][0]
                        self.nubes.append((x, y))
                if self.tipo_juego == 'TANKS':
                    if verbo == 'SPAWN' and objeto == 'PLAYER': self.tanks_spawn_player()
                    if verbo == 'SPAWN' and objeto == 'ENEMY' :  self.tanks_spawn_enemy()   
                    if verbo == 'SPAWN' and objeto == 'WALL'  : self.tank_spawn_wall(accion)
                    if verbo == 'SPAWN' and objeto == 'CURA'  : threading.Timer(2, self.tanks_spawn_cura).start()
                             

    # METODOS DE LOGICA DE JUEGO (MANTENIDOS DEL ARCHIVO ORIGINAL)
    # ---------------------------------------------------------------------
    def tank_spawn_wall(self, accion):
     x, y = accion['params'][0]
     self.tank_walls.append((x,y))
     self.grid[y][x] = 1

    def tanks_spawn_wall(self, x, y):
        self.grid[y][x] = 1 

    def tetris_spawn_pieza(self, tipo_spawn = "NORMAL"):
      

      shapes = self.datos_juego['shapes']

      filtradas = {}

      if tipo_spawn == "POWER_UP":

        for k, v in shapes.items():
          if k == "POWER_UP_PIECE":
            filtradas[k] = v
      else:

        for k, v in shapes.items():
          if k != "POWER_UP_PIECE":
            filtradas[k] = v

      shapes = filtradas
      if tipo_spawn == "NORMAL":

        # -------------------------
        # Calcular suma total
        # de probabilidades
        # -------------------------
        total_chance = 0

        for nombre in shapes:
            total_chance += shapes[nombre]['chance']

        # -------------------------
        # Generar numero aleatorio
        # -------------------------
        numero = random.randint(1, total_chance)

        # -------------------------
        # Seleccion ponderada
        # -------------------------
        acumulado = 0

        for nombre in shapes:

            acumulado += shapes[nombre]['chance']

            if numero <= acumulado:
                nombre_pieza = nombre
                break
      elif tipo_spawn == "POWER_UP":
          nombre_pieza = "POWER_UP_PIECE"

     # -------------------------
     # Obtener estados
     # -------------------------
      self.pieza_actual = shapes[nombre_pieza]['states']
      
      #Obtener Color
      
      self.color_actual = shapes[nombre_pieza]['color']
     # -------------------------
     # Posicion inicial
     # -------------------------
      self.pieza_x = self.ancho / 2 - 2
      self.pieza_y = 0
      self.pieza_rotacion = 0

     # -------------------------
     # Verificar colision
     # -------------------------
      if self.tetris_verificar_colision(
        self.pieza_x,
        self.pieza_y,
        self.pieza_rotacion
     ):
        self.juego_terminado = True

    def tetris_mover_pieza(self, direccion):
      if not self.pieza_actual: return
      dx, dy = 0, 0
      if direccion == 'LEFT': dx = -1
      elif direccion == 'RIGHT': dx = 1
      elif direccion == 'DOWN': dy = 1
      if not self.tetris_verificar_colision(self.pieza_x + dx, self.pieza_y + dy, self.pieza_rotacion):
        self.pieza_x += dx
        self.pieza_y += dy
      elif dy > 0:
        self.tetris_fijar_pieza()

    def tetris_rotar_pieza(self):
        if not self.pieza_actual: return
        nueva_rotacion = (self.pieza_rotacion + 1) % len(self.pieza_actual)
        if not self.tetris_verificar_colision(self.pieza_x, self.pieza_y, nueva_rotacion):
            self.pieza_rotacion = nueva_rotacion

    def tetris_fijar_pieza(self):
        matriz_pieza = self.pieza_actual[self.pieza_rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    if 0 <= self.pieza_y + y_offset < self.alto and 0 <= self.pieza_x + x_offset < self.ancho:
                        self.grid[self.pieza_y + y_offset][self.pieza_x + x_offset] = 1
        self.pieza_actual = None
        lineas = self.tetris_limpiar_lineas()
        if lineas and lineas >= 3:
          self.ejecutar_evento('ON_COMBO')
        else:
          self.ejecutar_evento('ON_START')

    def tetris_verificar_colision(self, x, y, rotacion):
        if not self.pieza_actual: return False
        matriz_pieza = self.pieza_actual[rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    nuevo_x, nuevo_y = x + x_offset, y + y_offset
                    if not (0 <= nuevo_x < self.ancho and 0 <= nuevo_y < self.alto and self.grid[nuevo_y][nuevo_x] == 0):
                        return True
        return False

    def tetris_limpiar_lineas(self):
        nuevo_grid = [fila for fila in self.grid if not all(fila)]
        lineas_limpias = self.alto - len(nuevo_grid)
        if lineas_limpias > 0:
            self.grid = [[0] * self.ancho for _ in range(lineas_limpias)] + nuevo_grid
            for _ in range(lineas_limpias):
              self.ejecutar_evento('ON_LINE_CLEAR')
            if lineas_limpias >= 3:
              return lineas_limpias
    
    def snake_spawn_jugador(self, accion):
        coords = accion['params'][0] if accion['params'] else [self.ancho / 2, self.alto / 2]
        self.serpiente_cuerpo = [(coords[0], coords[1])]
        self.serpiente_direccion = (1, 0)
        
    def snake_spawn_comida(self):
        while True:
            if self.level=="ENTUSIASTA":
                powergen = random.random() < 0.3
                if powergen and not self.powercool: self.ejecutar_evento('ON_POWER_UP') 
            x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
            if (x, y) not in self.serpiente_cuerpo:
                self.posicion_comida = (x, y)
                break
                
    def snake_spawn_fruta(self):
        while True:
            x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
            if (x, y) not in self.serpiente_cuerpo:
                self.pos_fruta = (x, y)
                break

    def snake_spawn_power(self):
        while True:
            x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
            if (x, y) not in self.serpiente_cuerpo:
                self.pos_power = (x, y)
                break

    def tanks_spawn_cura(self):
        while True:
            x, y = random.randint(0, self.ancho -1), random.randint(0, self.alto -1)
            
            if (x, y) != ((self.player_tanks['x'],self.player_tanks['y']))and (x,y) not in (self.tank_walls):
                self.pos_cura = (x, y)
                break
            


    def snake_mover_jugador(self):
        if not self.serpiente_cuerpo: return
        cabeza_x, cabeza_y = self.serpiente_cuerpo[0]
        dir_x, dir_y = self.serpiente_direccion
        nueva_cabeza = (cabeza_x + dir_x, cabeza_y + dir_y)
        #Acabar si se choca con una nube + condicion de nivel
        if (self.level=="NYAN_CAT")and(nueva_cabeza in self.nubes):
            if self.puntuacion >0:
                self.puntuacion=0
                self.ejecutar_evento('ON_START')
            else:
                self.juego_terminado=True
            return
        
        #Acabar si se choca con una pared + condicion de nivel
        if not (0 <= nueva_cabeza[0] < self.ancho and 0 <= nueva_cabeza[1] < self.alto):
            if (self.level=="NYAN_CAT")and(self.puntuacion >0):
                if self.inmortal: self.ejecutar_evento('ON_RESET')  
                else:
                    self.puntuacion=0
                    self.ejecutar_evento('ON_START')           
            else:
                if self.inmortal:
                    self.ejecutar_evento('ON_RESET')     
                else: self.ejecutar_evento('ON_COLLISION_WALL')
            return

        #Acabar si se choca con el cuerpo + condicion de nivel
        if nueva_cabeza in self.serpiente_cuerpo[:-1]:
            if (self.level=="NYAN_CAT")and(self.puntuacion >0):
                if self.inmortal: pass  
                else:
                    self.puntuacion=0
                    self.ejecutar_evento('ON_START')
            else:
                if self.inmortal: pass
                else: self.ejecutar_evento('ON_COLLISION_SELF')
            return
        
        #Acabar si se choca con la fruta venenosa + condicion de nivel
        if (self.level=="ENTUSIASTA")and(nueva_cabeza == self.pos_fruta):
            if self.puntuacion >= 10:
                self.ejecutar_evento("ON_EAT_FRUIT")
            else:
                if self.inmortal: pass
                else: self.ejecutar_evento("ON_POISON")
            return
        
        #Activar inmortalidad
        if (self.level=="ENTUSIASTA")and(nueva_cabeza == self.pos_power):
            self.temporizador = None
            self.snake_activar_inmortal()
            self.pos_power = None
            self.powercool = True
            threading.Timer(15, self.snake_fin_cooldown).start()

        self.serpiente_cuerpo.insert(0, nueva_cabeza)
        
        if nueva_cabeza == self.posicion_comida:
            self.ejecutar_evento('ON_EAT_FOOD')
        else:
            self.serpiente_cuerpo.pop()

    def snake_fin_cooldown(self):
        self.powercool = False

    def snake_activar_inmortal(self):
        self.inmortal = True
        if self.temporizador:
            self.temporizador.cancel()
        self.temporizador = threading.Timer(self.powertime, self.snake_desactivar_inmortal)
        self.temporizador.start()
        self.cabeza = "#0099FF"
        self.cuerpo = "#12FCF0"
    
    def snake_desactivar_inmortal(self):
        self.inmortal = False
        self.cabeza = '#00FF00'
        self.cuerpo = '#33CC33'

    def snake_cambiar_direccion(self, direccion):
        if direccion == 'UP' and self.serpiente_direccion[1] != 1:
            self.serpiente_direccion = (0, -1)
        elif direccion == 'DOWN' and self.serpiente_direccion[1] != -1:
            self.serpiente_direccion = (0, 1)
        elif direccion == 'LEFT' and self.serpiente_direccion[0] != 1:
            self.serpiente_direccion = (-1, 0)
        elif direccion == 'RIGHT' and self.serpiente_direccion[0] != -1:
            self.serpiente_direccion = (1, 0)

    def tanks_movimiento_player(self, direccion):
        x,y=self.player_tanks['x'],self.player_tanks['y']
        v=0.9
        if direccion == 'UP' and (self.tanks_colision_player("y",-v)) :       
           self.player_tanks['y']=y-v
           self.player_tanks['rotation']=0
        elif direccion == 'DOWN' and (self.tanks_colision_player("y",v)) :
            self.player_tanks['y']=y+v
            self.player_tanks['rotation']=2
        elif direccion == 'LEFT' and (self.tanks_colision_player("x",-v)):
            self.player_tanks['x']=x-v
            self.player_tanks['rotation']=3
        elif direccion == 'RIGHT' and (self.tanks_colision_player("x",v)) :
            self.player_tanks['x']=x+v
            self.player_tanks['rotation']=1

        print(self.pos_cura)
        print((x,y))

        if self.pos_cura:
         x1,y1=self.pos_cura
         if ((x1-x)**2 + (y1-y)**2) <= 4.5**2:
             self.player_tanks['endurance']+=1
             self.efecto_particulas(
                 self.player_tanks['x'],
                 self.player_tanks['y']
               )
             self.pos_cura=None
             threading.Timer(7, self.tanks_spawn_cura).start()
             

    def efecto_particulas(self, x, y):

    # Convertir de coordenadas del grid a píxeles
     x *= self.taman_celda
     y *= self.taman_celda

     particulas = []

    # Crear partículas
     for _ in range(25):

          r = random.randint(6, 10)

          pid = self.canvas.create_oval(
             x-r,
             y-r,
             x+r,
             y+r,
             fill="#19389e",
             outline="",
             tags="heal_particles"
           )
          self.canvas.tag_raise(pid)

          particulas.append({
             "id": pid,
             "vx": random.uniform(-1.5, 1.5),
             "vy": random.uniform(-1.2, -0.5),
             "vida": 105
           })

     def animar():

         eliminar = []

         for p in particulas:

             self.canvas.move(
                 p["id"],
                 p["vx"],
                 p["vy"]
             )

             p["vida"] -= 1

             if p["vida"] <= 0:
                 eliminar.append(p)

         for p in eliminar:
             self.canvas.delete(p["id"])
             particulas.remove(p)

         if particulas:
             self.canvas.after(50, animar)

     animar()






    def tanks_movimiento_enemy(self):
        for i in range ((len(self.enemy_tanks))):
         rotacion=self.enemy_tanks[i]['rotation']
         velocidad=self.enemy_tanks[i]['speed']
         if rotacion==0:
             if self.tanks_colision_enemy("y",-velocidad,i): 
                 self.enemy_tanks[i]['y']-=velocidad
             else:
                 self.enemy_tanks[i]['rotation']=2
                 self.enemy_tanks[i]['y']+=velocidad
         elif rotacion==2:
             if self.tanks_colision_enemy("y",velocidad,i): 
                 self.enemy_tanks[i]['y']+=velocidad
             else:
                 self.enemy_tanks[i]['rotation']=0
                 self.enemy_tanks[i]['y']-=velocidad
         elif rotacion==1:
             if self.tanks_colision_enemy("x",-velocidad,i): 
                 self.enemy_tanks[i]['x']-=velocidad
             else:
                 self.enemy_tanks[i]['rotation']=3
                 self.enemy_tanks[i]['x']+=velocidad
         elif rotacion==3:
             if self.tanks_colision_enemy("x",velocidad,i): 
                 self.enemy_tanks[i]['x']+=velocidad
             else:
                 self.enemy_tanks[i]['rotation']=1
                 self.enemy_tanks[i]['x']-=velocidad

             
    def tanks_colision_enemy(self,variable,valor,posicion):
        x,y=self.enemy_tanks[posicion]['x'],self.enemy_tanks[posicion]['y']
        if (x-5<=self.player_tanks['x']<=x+5)and(y-5<=self.player_tanks['y']<=y+5):
            return False
        for i in range(len(self.tank_walls)-1):
            x1,y1=self.tank_walls[i]
            if (variable=="y") and (x1-4 <= x < x1)and (y1-4 <= y+valor*2 < y1):
              return False
            elif (variable=="x") and (y1-4 <= y < y1) and (x1-4 <= x+valor*2 < x1):
              return False
        else:
          if (variable=="x" and (0 <= x+valor*2 < self.ancho-4.97)):
             return True
          elif (variable=="y" and (0 <= y+valor*2 < self.alto-5)):
             return True
          else:
             return False

    def tanks_colision_player(self,variable,valor):
        x=self.player_tanks['x']
        y=self.player_tanks['y']
        for i in range(len(self.tank_walls)-1):
            x1,y1=self.tank_walls[i]
            if (variable=="y") and (x1-4 <= x < x1)and (y1-4 <= y+valor*2 < y1):
              return False
            elif (variable=="x") and (y1-4 <= y < y1) and (x1-4 <= x+valor*2 < x1):
              return False

        if (variable=="x") and (0 <= x+valor*2 < self.ancho-4.97):
            return True
        elif (variable=="y") and (0 <= y+valor*2 < self.alto-5):
            return True
        else:
            return False
                                  


    def snake_crecer(self):
        pass

    def tanks_spawn_player(self):
        player_shape = None

        for nombre, shape in self.datos_juego['shapes'].items():
            if shape['type'] == 'PLAYER':
                player_shape = shape
                break

        if not player_shape:
            return

        x, y = self.obtener_posicion_valida(player_shape)

        self.player_tanks = {
            'x': x,
            'y': y,
            'color': player_shape['color'],
            'speed': player_shape['speed'],
            'endurance': player_shape['endurance'],
            'rotation': 0,
            'shape': player_shape
        }

    def tanks_spawn_enemy(self):

        self.enemies_shapes = []
        for nombre, shape in self.datos_juego['shapes'].items():
            if shape['type'] == 'ENEMY':
                self.enemies_shapes.append(shape)
        if not self.enemies_shapes:
            print("No se pudieron encontrar los tanques enemigos.")
            self.root.destroy()
            sys.exit(0)
        enemy_shape = random.choice(self.enemies_shapes)
        while True:
            x, y = self.obtener_posicion_valida(enemy_shape)

            if (x, y) != (self.player_tanks['x'], self.player_tanks['y']):
                break

        self.enemy_tanks.append({
            'x': x,
            'y': y,
            'color': enemy_shape['color'],
            'speed': enemy_shape['speed'],
            'endurance': enemy_shape['endurance'],
            'rotation': 0,
            'shape': enemy_shape
        })

    def tanks_generar_bordes(self):

        # Superior e inferior
        for x in range(self.ancho):

            self.tanks_spawn_wall(x, 0)

            self.tanks_spawn_wall(
                x,
                self.alto - 1
            )

        # Laterales
        for y in range(1, self.alto - 1):

            self.tanks_spawn_wall(0, y)

            self.tanks_spawn_wall(
                self.ancho - 1,
                y
            )


    # METODOS DE SALIDA (ADAPTADOS A GUI)
    # -----------------------------------

    def mostrar_game_over(self):
        # Muestra una ventana de mensaje de Tkinter
        tkMessageBox.showinfo("Juego Terminado", "Puntuacion Final: " + str(self.puntuacion))
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Uso: python runtime.py <archivo_juego.json>"
        sys.exit(1)
    archivo_juego = sys.argv[1]
    try:
        with open(archivo_juego, 'r') as f:
            datos_juego = json.load(f)
    except IOError:
        print "Error: No se pudo encontrar el archivo " + archivo_juego
        sys.exit(1)
    juego = Juego(datos_juego)
    juego.run()
    
