.PHONY: install start enable status

install:
	sudo cp game_of_rapprochement_bot.service /etc/systemd/system/
	sudo systemctl daemon-reload

nano:
	nano .env
start:
	sudo systemctl start game_of_rapprochement_bot

enable:
	sudo systemctl enable game_of_rapprochement_bot

status:
	sudo systemctl status game_of_rapprochement_bot
