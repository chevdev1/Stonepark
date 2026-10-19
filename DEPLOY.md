# Как выложить STONEPARK на VPS (Ubuntu)

Репозиторий: https://github.com/chevdev1/Stonepark.git

Что где работает:
- `web/` — сайт. Раздаёт nginx.
- `server/` — бэкенд (Node.js + SQLite). Хранит стену, чат, галерею и рассылает рисунки всем игрокам сразу. nginx проксирует ему `/ws` и `/api`.
- База — один файл `/var/lib/stonepark/stonepark.db`. Рисунки стены остаются там навсегда.

Команды ниже выполняй на сервере по SSH.

## 1. Пакеты и Node.js 22

```bash
sudo apt update && sudo apt install -y nginx git curl certbot python3-certbot-nginx
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node -v        # должно быть v22.13 или выше
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable
```

## 2. Код

```bash
sudo useradd --system --home /var/www/stonepark --shell /usr/sbin/nologin stonepark
sudo git clone https://github.com/chevdev1/Stonepark.git /var/www/stonepark
cd /var/www/stonepark/server && sudo npm install --omit=dev
sudo mkdir -p /var/lib/stonepark && sudo chown stonepark /var/lib/stonepark
```

## 3. Настройки бэкенда

```bash
sudo cp /var/www/stonepark/server/.env.example /etc/stonepark.env
sudo chmod 600 /etc/stonepark.env
sudo nano /etc/stonepark.env
```

В файле поменяй:
- `ADMIN_TOKEN` — длинный пароль владельца (придумай сам или `openssl rand -base64 24`). Запиши его.
- `ALLOWED_ORIGINS` — твой домен с `https://`.

Запуск:

```bash
sudo cp /var/www/stonepark/deploy/stonepark.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now stonepark
curl localhost:3000/api/health        # ответ: ok
sudo journalctl -u stonepark -f       # логи (выход: Ctrl+C)
```

## 4. nginx и HTTPS

Домен: A-запись на IP сервера.

```bash
sudo cp /var/www/stonepark/deploy/nginx.conf /etc/nginx/sites-available/stonepark
sudo nano /etc/nginx/sites-available/stonepark     # замени stonepark.example на свой домен
sudo ln -s /etc/nginx/sites-available/stonepark /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d твой-домен -d www.твой-домен
```

Если домена пока нет, оставь `server_name _;` и открывай сайт по IP (по http).

## 5. Владелец

Один раз открой `https://твой-домен/?admin=ТВОЙ_ADMIN_TOKEN`. Браузер запомнит токен. Дальше у тебя появятся: кнопка сброса стены, удаление любых штрихов и сообщений, загрузка треков и работ в галерею. Остальные игроки — обычные: рисуют, пишут в чат, голосуют, удалять могут только свои штрихи. Выйти из режима владельца: `?logout`.

## 6. Обновление сайта

На сервере:

```bash
cd /var/www/stonepark && sudo git pull
sudo systemctl restart stonepark      # только если менялась папка server/
```

База при обновлении не трогается (она в `/var/lib/stonepark`).

## 7. Бэкап

```bash
sudo crontab -e
# добавь строку (копия базы каждую ночь в 04:00, хранится 14 дней):
0 4 * * * mkdir -p /var/backups/stonepark && sqlite3 /var/lib/stonepark/stonepark.db ".backup /var/backups/stonepark/sp-$(date +\%F).db" && find /var/backups/stonepark -mtime +14 -delete
```

Нужен `sudo apt install -y sqlite3`.

## Что важно знать

- **Игроки анонимные.** Каждому браузеру сервер выдаёт id. Свои штрихи человек удалить может, чужие нет. Если очистить данные браузера, id сменится.
- **Лимиты.** На соединение действует лимит записей в секунду, в чате не больше одного сообщения в 1,5 с (пачками до 3), на одной эпохе стены не больше 30 000 штрихов. Сверх лимита сайт показывает «стена заполнена». Владелец может сбросить стену, старые рисунки при этом остаются в базе.
- **Пейджер CH.** Живые ответы от Claude не подключены, CH отвечает заготовленными фразами. Для живых нужен отдельный эндпоинт с ключом Anthropic (только на сервере).
- **Если сервер лёг**, сайт переходит в гостевой режим: рисуют каждый у себя, ничего не теряется и не ломается.
