git pull
cd front/
source venv/bin/activate
pip install -r requirements-prod.txt
python manage.py migrate
yes | python manage.py collectstatic
sudo service apache2 restart
sudo service dramatiq restart