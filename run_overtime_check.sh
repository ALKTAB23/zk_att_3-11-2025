#!/bin/bash
cd /opt/odoo16
sudo -u odoo ./odoo-bin shell -c /etc/odoo/odoo.conf -d Ahmed_2_11 < /tmp/check_overtime_data.py
