#!/bin/bash -e

cd /opt/star-burger
source .env
git pull origin master
echo "Git pulled - OK"

npm ci
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
echo "Frontend assembled - OK"

python_path="./venv/bin/python"
$python_path -m pip install -r requirements.txt
$python_path manage.py collectstatic --no-input
$python_path manage.py migrate --no-input
echo "Backend assembled - OK"

systemctl daemon-reload
systemctl reload nginx
systemctl stop star-burger
systemctl start star-burger
echo "Starburger started - OK"

last_commit_hash=$(git rev-parse HEAD)
curl -H "X-Rollbar-Access-Token: $ROLLBAR_ACCESS_TOKEN" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "production", "revision": "'{$last_commit_hash}'", "rollbar_name": "kasatkina235", "local_username": "root", "comment": "auto-deployment", "status": "succeeded"}'

echo "Deployment completed - OK!"

