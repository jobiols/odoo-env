## Who is this for?

This is mainly aimed at odoo developers but also anyone who wants to install odoo into production quickly and without problems.

## What is all this about?

Working with Odoo is difficult, it changes every year, it needs a lot of requirements and we should also follow the best installation practices.

That's why we chose to work with Docker. But there is good news: **You don't need to know docker !!**. The only you have to know about is odoo-env, a bunch of easy to learn commands.

With odoo-env you can:
- Have all the information needed to deploy the instance in a unique place, an odoo module
- Deploy a development environment with [wdb](https://github.com/Kozea/wdb) debugger included.
- Deploy a production envirionment with nginx included, or traefik and letsencrypt certificate with a little manual work if you want.
- Have in your wokstation lots of different odoo projects with different versions and each one with the right repos and images and switch between them almost instantly.
- Sleep peacefully, everywhere the libraries are the same, because they are within the image
- No knowledge of docker is required, unless the fatal question pops up. Where the hell is the data ???


<!-- ![](/assets/img/etl-dbs.png)
*<center>Picture 1</center>* -->

The proyect lives in [odoo-env](https://github.com/jobiols/odoo-env) Any feedback
is welcome, if someone likes the idea, please don't hesitate to contact me so we can work together.

If you find some issues please report it to [issues](https://github.com/jobiols/odoo-etl/issues)

Author: Jorge Obiols <jorge.obiols@gmail.com>

{% include manifest_example.md %}
{% include wich-images-to-use.md %}
{% include the-magic-begins.md %}
