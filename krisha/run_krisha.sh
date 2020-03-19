#!/bin/bash

arenda=(
    "arenda_doma"
    "arenda_kvartiry"
    "arenda_komnaty"
    "arenda_dachi"
    "arenda_ofisa"
    "arenda_pomeshhenija"
    "arenda_zdanija"
    "arenda_magazina"
    "arenda_prombazy"
    "arenda_prochej-nedvizhimosti"
)

prodazha=(
    "prodazha_kvartiry"
    "prodazha_doma"
    "prodazha_dachi"
    "prodazha_uchastkov"
    "prodazha_ofisa"
    "prodazha_pomeshhenija"
    "prodazha_zdanija"
    "prodazha_magazina"
    "prodazha_prombazy"
    "prodazha_prochej-nedvizhimosti"
    "prodazha_zarubezhnoj-nedvizhimosti"
)

i=1
for t in ${arenda[@]}; do
    screen -dm -S "$i-$t" bash -c "python3 krisha.py $t; exec sh"
    echo "$t started"
    ((i++))
done
j=1
for a in ${prodazha[@]}; do
    screen -dm -S "$j-$a" bash -c "python3 krisha.py $a; exec sh"
    echo "$a started"
    ((j++))
done
