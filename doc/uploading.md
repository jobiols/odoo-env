#Generating distribution archives

verificar que tengamos las ultimas versiones

    python -m pip install --user --upgrade setuptools wheel twine
 
ejecutar en el directorio donde esta setup.py
    
    python setup.py sdist bdist_wheel
    
# Uploading the distribution archives
    
    twine upload dist/*
    
luego el proyecto se puede ver en

    https://pypi.org/project/oodo-env/

#Installing your newly uploaded package

    pip install docker-odoo-env
    

    