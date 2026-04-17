import sys
import os

# Ajouter le dossier projet au path Python
path = '/home/VOTRE_USERNAME/processinsight'
if path not in sys.path:
    sys.path.insert(0, path)

# Importer l'application Flask
from app import create_app
application = create_app()