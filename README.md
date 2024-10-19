# Игра на сближение

# https://t.me/game_of_rapprochement_bot 

Бывает так, что разговор заходит в тупик, и повисает тягостное молчание. 

Вы судорожно пытаетесь придумать какой-то интересный вопрос, но в голову не приходит ничего оригинального.

Можно говорить о погоде , о работе, о детях. Но как начать разговор с незнакомым человеком? Какие вопросы можно задать для интересной и живой беседы? 

Сегодня мы рассмотрим том, какие вопросы вам удастся наполнить беседой со смыслом и поддержать интересный и живой разговор.



docker build --no-cache -t game_of_rapprochement_bot .
docker run -d --name game_of_rapprochement_bot --restart=always --env-file .env -v $(pwd)/log:/app/log game_of_rapprochement_bot


docker stop game_of_rapprochement_bot
docker rm game_of_rapprochement_bot
docker logs -f game_of_rapprochement_bot

docker-compose up -d --build
