#!/data/data/com.termux/files/usr/bin/bash

clear

if [ -z "$1" ]; then
echo ""
echo "Uso: ./jugar.sh [nombre]"
echo "Ejemplo: ./jugar.sh snake"
echo ""
exit
fi

echo "Compilando $1..."
echo "-------------------------"

python2 compiler.py games/$1.brick

if [ $? -ne 0 ]; then
echo ""
echo "Error de compilacion"
exit
fi

echo ""
echo "Iniciando juego..."
echo "-------------------------"

python2 runtime.py games/$1.json
