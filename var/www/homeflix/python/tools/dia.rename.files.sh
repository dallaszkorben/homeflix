#!/bin/sh

sor=1
FILES=./*.[jJ][pP][gG]
for file in $FILES
do

    foo=$(printf "%03d" $sor)
    mv "./$file" "A.Torok.Es.A.Tehenek_"$foo".jpg"

    echo "$file -> $foo"
    sor=`expr $sor + 1`
done
