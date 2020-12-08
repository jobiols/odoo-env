# Introduction to odoo-env

Odoo Environment es una pequeña herramienta para manejar ambientes de odoo en forma
dockerizada, permite tener ambientes de produccion y de desarrollo.
Principales características:

- Toda la informacion del proyecto se encuentra en un solo lugar
- Rapido deploy en produccion
- Rapido switch entre proyectos en desarrollo sin importar la version de odoo
- Creacion automatica del archivo de configuracion odoo.conf
- Modo debug basado en wdb
- Instalacion automatica de nginx como proxy inverso en produccion
- Restauracion de backups con un solo comando
- Persistencia de variables de entorno

El ambiente se basa en dos comandos sd y oe

    sd (atajo para sudo docker) es muy util para teclar menos y sobre todo cuando
    queremos limpiar la memoria de imagenes con rmall, el comando rmdiskall es

    sd [cualquier comando de docker] [-h] [--help] [rmall] [inside <image name>]
       [rmdiskall] [attach <name>]

Opciones:
    rmall       Remueve todas las imagenes de memoria
    rmdiskall   Remueve todas las imagenes de disco
    inside <image name> entra en una imagen de docker de disco
    attach <image name> entra en una imagen de docker en ejecucion


![](/assets/img/etl-dbs.png)
*<center>Picture 1</center>*


The proyect lives in [odoo-env](https://github.com/jobiols/odoo-env) Any feedback
is welcome, if someone likes the idea, please don't hesitate to contact me so
we can work together.

If you find some issues please report it to [issues](https://github.com/jobiols/odoo-etl/issues)

Jorge Obiols <jorge.obiols@gmail.com>

{% include capitulo2.md %}
{% include capitulo3.md %}
{% include where-to-install.md %}
