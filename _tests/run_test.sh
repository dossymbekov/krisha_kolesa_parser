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

i=1
for t in ${arenda[@]}; do
    screen -dm -S "$i-test-$t" bash -c "python3 test1.py $t; exec sh;"
    echo "test-$t started"
    ((i++))
done