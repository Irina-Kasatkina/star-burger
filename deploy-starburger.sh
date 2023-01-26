#!/bin/bash -e

cd /opt/star-burger
source .env
git pull -q
python_path="./venv/bin/python"
$python_path -m pip install -q -r requirements.txt
npm install --dev --silent
./node_modules/.bin/parcel build --log-level "none" bundles-src/index.js --dist-dir bundles --public-url="./"
$python_path manage.py collectstatic --no-input
$python_path manage.py migrate --no-input
systemctl restart star-burger.service
curl -X POST https://api.rollbar.com/api/1/deploy -H "X-Rollbar-Access-Token: $ROLLBAR_ACCESS_TOKEN" -d "environment=production&revision=$(git rev-parse HEAD)"
echo "Done!"
