## Who is this for?

This guide is intended for Odoo developers who want to install the platform quickly and without issues. It's also useful for anyone who wants to learn about the benefits of using Docker in Odoo development.

## What is Odoo?

Odoo is a powerful platform for managing business operations, such as sales, accounting, and project management. It's highly customizable and can be adapted to a wide range of industries and use cases.

## What is Odoo Env?

Odoo-env is a set of easy-to-learn commands that make it simple to install and manage Odoo using Docker. With odoo-env, you can:

- Deploy an Odoo instance in minutes, without needing to know anything about Docker

- Have all the information needed to deploy the instance in a unique place, an odoo module
- Deploy a development environment with wdb debugger included
- Deploy a production environment with nginx included, or traefik and letsencrypt certificate with a little manual work if you want
- Have multiple Odoo projects with different versions on your workstation, each with the right repos and images, and switch between them almost instantly
- Sleep peacefully, knowing that the libraries are the same everywhere because they are within the image

The odoo-env project lives on [odoo-env](https://github.com/jobiols/odoo-env). Any feedback is welcome, and if you like the idea, please don't hesitate to contact me so we can work together.

If you encounter any issues, please report them on the issues page.

In conclusion, odoo-env is a powerful tool that simplifies the installation and management of Odoo using Docker. Whether you're a seasoned Odoo developer or just getting started, odoo-env can help you save time and reduce headaches. Give it a try and see for yourself!

If you find some issues please report it to [issues](https://github.com/jobiols/odoo-env/issues)

Author: Jorge Obiols <jorge.obiols@gmail.com>

{% include manifest_example.md %}
{% include wich-images-to-use.md %}
{% include the-magic-begins.md %}
