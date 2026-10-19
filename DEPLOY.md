# Как выложить STONEPARK

## 1. Репозиторий (GitHub)

Репозиторий уже инициализирован, первый коммит сделан. Создай пустой репозиторий на GitHub (без README), затем:

```bash
cd stonepark
git remote add origin git@github.com:ТВОЙ_АККАУНТ/stonepark.git
git branch -M main
git push -u origin main
```

Самый большой файл весит 12 МБ, Git LFS не нужен. Ключи и пароли в репозиторий не кладём: `.env` уже в `.gitignore`.

## 2. VPS (Ubuntu/Debian)

```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx rsync
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable
sudo mkdir -p /var/www/stonepark/web && sudo chown -R $USER /var/www/stonepark
```

Домен: A-запись (и AAAA, если есть IPv6) на IP сервера.

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/stonepark   # поменяй stonepark.example на свой домен
sudo ln -s /etc/nginx/sites-available/stonepark /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d твой-домен -d www.твой-домен             # HTTPS, продлевается сам
```

Заливка сайта с компьютера: `./deploy/deploy.sh user@IP_СЕРВЕРА`. Или на сервере: `git clone` и `git pull` при обновлениях, а `root` в nginx указывает на папку `web` в клоне.

## 3. Что важно понимать

**Общие функции.** На claude.ai стену, чат, ранкед, треки, галерею и курсоры держит платформа. На VPS их заменяет `web/js/local-runtime.js`, а он хранит всё в браузере посетителя. Поэтому на VPS сайт сначала работает «у каждого свой»: рисунки и сообщения не видны другим. Чтобы сделать их общими, нужен небольшой бэкенд (Node.js + WebSocket + SQLite или Supabase/Firebase) с тем же API, что описан в README.

**Пейджер CH.** Живые ответы шли через Claude на claude.ai. На VPS нужен серверный эндпоинт с ключом Anthropic API. Ключ хранится только на сервере (в `.env`), в браузер он не попадает. Плюс лимит запросов, иначе любой сможет тратить твой баланс. Без эндпоинта CH отвечает заготовленными фразами.

**Модерация.** Стена и чат — пользовательский контент. Проверки на сайте (длина, ссылки, частота) легко обойти, поэтому на бэкенде нужны свои лимиты и кнопка удаления для владельца.

**Бэкапы.** Как только появится база, настрой ежедневную копию (cron + архив в другое место).

**Обновления.** `index.html` не кэшируется, CSS и JS кэшируются на час, медиа на 30 дней. Если заменяешь картинку или видео, давай файлу новое имя, иначе у людей останется старая версия.
