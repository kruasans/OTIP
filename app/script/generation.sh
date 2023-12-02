#!/bin/bash

ARRAY=('a' 'b' 'c' 'd' 'e' 'f' 'g' 'h' 'i' 'j' 'k' 'l' 'm' 'n' 'o' 'p' 'q' 'r' 's' 't' 'u' 'v' 'w' 'x' 'y' 'z')
TAGS=("Education" "Personal" "Plan")
if [[ ! $1 ]] || [[ $1 -lt 0 ]]
then
    COUNT=20
else
    COUNT="$1"
fi
for ((i=1; i <= COUNT; i++))
do
  text=""
  type="${TAGS[$RANDOM % ${#TAGS[@]}]}"
  details=""
  for j in {1..10}
  do
    text+="${ARRAY[$RANDOM % ${#ARRAY[@]}]}"
    details+="${ARRAY[$RANDOM % ${#ARRAY[@]}]}"
  done
  curl -X 'POST' \
  'http://0.0.0.0/add' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "title=$text&details=$details&type=$type"
done