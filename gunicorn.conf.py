import multiprocessing

# Nombre de workers basé sur le nombre de cœurs CPU
workers = multiprocessing.cpu_count() * 2 + 1

# Type de worker
worker_class = 'sync'

# Timeout en secondes
timeout = 120

# Port d'écoute
bind = '0.0.0.0:8080'

# Logs
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Rechargement automatique
reload = False

# En-têtes pour le proxy
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}
