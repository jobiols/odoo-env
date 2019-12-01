# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoorpc

odoo = odoorpc.ODOO('localhost', port=80)
print(odoo.db.list())

odoo.db.create('admin','bulonfer_test1',demo=True,admin_password='admin')
