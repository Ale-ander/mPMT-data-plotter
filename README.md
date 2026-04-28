# mPMT-data-plotter
mPMT data plotter and slowcontrol webapp, based on [django](https://www.djangoproject.com/). 

To prepare the PostgreSQL database, run the following commands after cloning the repo:

```bash
python manage.py makemigrations
python manage.py migrate
```

Then, to start the server (default ip is 127.0.0.1:8000), launch:

```bash
python manage.py runserver <IP>:<PORT>
```