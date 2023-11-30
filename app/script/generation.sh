#!/bin/bash

ARRAY=('a' 'b' 'c' 'd' 'e' 'f' 'g' 'h' 'i' 'j' 'k' 'l' 'm' 'n' 'o' 'p' 'q' 'r' 's' 't' 'u' 'v' 'w' 'x' 'y' 'z')
TAGS=("Education" "Personal" "Plan")
for i in {1..20}
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