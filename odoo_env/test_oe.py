##############################################################################

import unittest

from odoo_env.client import Client
from odoo_env.command import Command, CreateNginxTemplate, MakedirCommand
from odoo_env.config import OeConfig
from odoo_env.images import Image, Image2
from odoo_env.odooenv import OdooEnv
from odoo_env.repos import Repo, Repo2


class TestRepository(unittest.TestCase):
    def test_install(self):
        """################################################# TEST INSTALLATION"""
        options = {
            "debug": False,
            "no-repos": False,
            "nginx": True,
        }

        base_dir = "/odoo_ar/"
        oe = OdooEnv(options)
        cmds = oe.install("test_client")
        self.assertEqual(cmds[0].args, base_dir)
        self.assertEqual(cmds[0].command, "sudo mkdir " + base_dir)
        self.assertEqual(cmds[0].usr_msg, "Installing client test_client")

        self.assertEqual(
            cmds[2].args, "{}odoo-9.0/test_client/postgresql".format(base_dir)
        )
        self.assertEqual(
            cmds[2].command,
            "mkdir -p {}odoo-9.0/test_client/postgresql".format(base_dir),
        )
        self.assertEqual(cmds[2].usr_msg, False)

        self.assertEqual(cmds[3].args, "/odoo_ar/odoo-9.0/test_client/config")
        self.assertEqual(
            cmds[3].command, "mkdir -p /odoo_ar/odoo-9.0/test_client/config"
        )
        self.assertEqual(cmds[3].usr_msg, False)

        self.assertEqual(cmds[4].args, "/odoo_ar/odoo-9.0/test_client/data_dir")
        self.assertEqual(
            cmds[4].command, "mkdir -p /odoo_ar/odoo-9.0/test_client/data_dir"
        )
        self.assertEqual(cmds[4].usr_msg, False)

        self.assertEqual(cmds[5].args, "/odoo_ar/odoo-9.0/test_client/backup_dir")
        self.assertEqual(
            cmds[5].command, "mkdir -p /odoo_ar/odoo-9.0/test_client/backup_dir"
        )
        self.assertEqual(cmds[5].usr_msg, False)

        self.assertEqual(cmds[6].args, "/odoo_ar/odoo-9.0/test_client/log")
        self.assertEqual(cmds[6].command, "mkdir -p /odoo_ar/odoo-9.0/test_client/log")
        self.assertEqual(cmds[6].usr_msg, False)

        self.assertEqual(cmds[7].args, "/odoo_ar/odoo-9.0/test_client/sources")
        self.assertEqual(
            cmds[7].command, "mkdir -p /odoo_ar/odoo-9.0/test_client/sources"
        )
        self.assertEqual(cmds[7].usr_msg, False)

        self.assertEqual(cmds[8].args, False)
        self.assertEqual(
            cmds[8].command, "chmod o+w /odoo_ar/odoo-9.0/test_client/config"
        )
        self.assertEqual(cmds[8].usr_msg, False)

        self.assertEqual(cmds[9].args, False)
        self.assertEqual(
            cmds[9].command, "chmod o+w /odoo_ar/odoo-9.0/test_client/data_dir"
        )
        self.assertEqual(cmds[9].usr_msg, False)

        self.assertEqual(cmds[10].args, False)
        self.assertEqual(
            cmds[10].command, "chmod o+w /odoo_ar/odoo-9.0/test_client/log"
        )
        self.assertEqual(cmds[10].usr_msg, False)

        self.assertEqual(cmds[11].args, False)
        self.assertEqual(
            cmds[11].command, "chmod o+w /odoo_ar/odoo-9.0/test_client/backup_dir"
        )
        self.assertEqual(cmds[11].usr_msg, False)

        self.assertEqual(cmds[12].args, "/odoo_ar/nginx/cert")
        self.assertEqual(cmds[12].command, "mkdir -p /odoo_ar/nginx/cert")
        self.assertEqual(cmds[12].usr_msg, False)

        self.assertEqual(cmds[13].args, "/odoo_ar/nginx/conf")
        self.assertEqual(cmds[13].command, "mkdir -p /odoo_ar/nginx/conf")
        self.assertEqual(cmds[13].usr_msg, False)

        self.assertEqual(cmds[14].args, "/odoo_ar/nginx/log")
        self.assertEqual(cmds[14].command, "mkdir -p /odoo_ar/nginx/log")
        self.assertEqual(cmds[14].usr_msg, False)

        self.assertEqual(cmds[15].args, "/odoo_ar/nginx/conf/nginx.conf")
        self.assertEqual(cmds[15].command, "/odoo_ar/nginx/conf/nginx.conf")
        self.assertEqual(cmds[15].usr_msg, "Generating nginx.conf template")

        self.assertEqual(
            cmds[16].args, "/odoo_ar/odoo-9.0/test_client/sources/cl-test-client"
        )
        self.assertEqual(
            cmds[16].command,
            "git -C /odoo_ar/odoo-9.0/test_client/sources/ clone --depth 1 "
            "-b 9.0 https://github.com/jobiols/cl-test-client",
        )
        self.assertEqual(
            cmds[16].usr_msg, "cloning b 9.0     jobiols/cl-test-client        "
        )

        self.assertEqual(
            cmds[17].args, "/odoo_ar/odoo-9.0/test_client/sources/cl-test-client"
        )
        self.assertEqual(
            cmds[17].command,
            "git -C /odoo_ar/odoo-9.0/test_client/sources/cl-test-client pull",
        )
        self.assertEqual(
            cmds[17].usr_msg, "pulling b 9.0     jobiols/cl-test-client        "
        )

        self.assertEqual(
            cmds[18].args, "/odoo_ar/odoo-9.0/test_client/sources/odoo-addons"
        )
        self.assertEqual(
            cmds[18].command,
            "git -C /odoo_ar/odoo-9.0/test_client/sources/ clone --depth 1 "
            "-b 9.0 https://github.com/jobiols/odoo-addons",
        )
        self.assertEqual(
            cmds[18].usr_msg, "cloning b 9.0     jobiols/odoo-addons           "
        )

        self.assertEqual(
            cmds[19].args, "/odoo_ar/odoo-9.0/test_client/sources/odoo-addons"
        )
        self.assertEqual(
            cmds[19].command,
            "git -C /odoo_ar/odoo-9.0/test_client/sources/odoo-addons pull",
        )
        self.assertEqual(
            cmds[19].usr_msg, "pulling b 9.0     jobiols/odoo-addons           "
        )

    def test_install2(self):
        """################################################# TEST INSTALLATION"""
        options = {
            "debug": False,
            "no-repos": False,
            "nginx": True,
        }

        base_dir = "/odoo_ar/"
        oe = OdooEnv(options)
        cmds = oe.install("test2_client")
        self.assertEqual(cmds[0].args, base_dir)
        self.assertEqual(cmds[0].command, "sudo mkdir " + base_dir)
        self.assertEqual(cmds[0].usr_msg, "Installing client test2_client")

        self.assertEqual(
            cmds[2].args, "{}odoo-9.0/test2_client/postgresql".format(base_dir)
        )
        self.assertEqual(
            cmds[2].command,
            "mkdir -p {}odoo-9.0/test2_client/postgresql".format(base_dir),
        )
        self.assertEqual(cmds[2].usr_msg, False)

        self.assertEqual(cmds[3].args, "/odoo_ar/odoo-9.0/test2_client/config")
        self.assertEqual(
            cmds[3].command, "mkdir -p /odoo_ar/odoo-9.0/test2_client/config"
        )
        self.assertEqual(cmds[3].usr_msg, False)

        self.assertEqual(cmds[4].args, "/odoo_ar/odoo-9.0/test2_client/data_dir")
        self.assertEqual(
            cmds[4].command, "mkdir -p /odoo_ar/odoo-9.0/test2_client/data_dir"
        )
        self.assertEqual(cmds[4].usr_msg, False)

        self.assertEqual(cmds[5].args, "/odoo_ar/odoo-9.0/test2_client/backup_dir")
        self.assertEqual(
            cmds[5].command, "mkdir -p /odoo_ar/odoo-9.0/test2_client/backup_dir"
        )
        self.assertEqual(cmds[5].usr_msg, False)

        self.assertEqual(cmds[6].args, "/odoo_ar/odoo-9.0/test2_client/log")
        self.assertEqual(cmds[6].command, "mkdir -p /odoo_ar/odoo-9.0/test2_client/log")
        self.assertEqual(cmds[6].usr_msg, False)

        self.assertEqual(cmds[7].args, "/odoo_ar/odoo-9.0/test2_client/sources")
        self.assertEqual(
            cmds[7].command, "mkdir -p /odoo_ar/odoo-9.0/test2_client/sources"
        )
        self.assertEqual(cmds[7].usr_msg, False)

        self.assertEqual(cmds[8].args, False)
        self.assertEqual(
            cmds[8].command, "chmod o+w /odoo_ar/odoo-9.0/test2_client/config"
        )
        self.assertEqual(cmds[8].usr_msg, False)

        self.assertEqual(cmds[9].args, False)
        self.assertEqual(
            cmds[9].command, "chmod o+w /odoo_ar/odoo-9.0/test2_client/data_dir"
        )
        self.assertEqual(cmds[9].usr_msg, False)

        self.assertEqual(cmds[10].args, False)
        self.assertEqual(
            cmds[10].command, "chmod o+w /odoo_ar/odoo-9.0/test2_client/log"
        )
        self.assertEqual(cmds[10].usr_msg, False)

        self.assertEqual(cmds[11].args, False)
        self.assertEqual(
            cmds[11].command, "chmod o+w /odoo_ar/odoo-9.0/test2_client/backup_dir"
        )
        self.assertEqual(cmds[11].usr_msg, False)

        self.assertEqual(cmds[12].args, "/odoo_ar/nginx/cert")
        self.assertEqual(cmds[12].command, "mkdir -p /odoo_ar/nginx/cert")
        self.assertEqual(cmds[12].usr_msg, False)

        self.assertEqual(cmds[13].args, "/odoo_ar/nginx/conf")
        self.assertEqual(cmds[13].command, "mkdir -p /odoo_ar/nginx/conf")
        self.assertEqual(cmds[13].usr_msg, False)

        self.assertEqual(cmds[14].args, "/odoo_ar/nginx/log")
        self.assertEqual(cmds[14].command, "mkdir -p /odoo_ar/nginx/log")
        self.assertEqual(cmds[14].usr_msg, False)

        self.assertEqual(cmds[15].args, "/odoo_ar/nginx/conf/nginx.conf")
        self.assertEqual(cmds[15].command, "/odoo_ar/nginx/conf/nginx.conf")
        self.assertEqual(cmds[15].usr_msg, "Generating nginx.conf template")

        self.assertEqual(
            cmds[16].args, "/odoo_ar/odoo-9.0/test2_client/sources/odoo-addons"
        )
        self.assertEqual(
            cmds[16].command,
            "git -C /odoo_ar/odoo-9.0/test2_client/sources/ clone --depth 1 "
            "-b 9.0 https://github.com/jobiols/odoo-addons.git",
        )
        self.assertEqual(
            cmds[16].usr_msg,
            "cloning b 9.0     https://github.com/jobiols/odoo-addons.git",
        )

        self.assertEqual(
            cmds[17].args, "/odoo_ar/odoo-9.0/test2_client/sources/odoo-addons"
        )
        self.assertEqual(
            cmds[17].command,
            "git -C /odoo_ar/odoo-9.0/test2_client/sources/odoo-addons pull",
        )
        self.assertEqual(
            cmds[17].usr_msg,
            "pulling b 9.0     https://github.com/jobiols/odoo-addons.git",
        )

        self.assertEqual(
            cmds[18].args, "/odoo_ar/odoo-9.0/test2_client/sources/adhoc-odoo-argentina"
        )

        self.assertEqual(
            cmds[18].command,
            "git -C /odoo_ar/odoo-9.0/test2_client/sources/ clone --depth 1 "
            "-b 9.0 https://github.com/ingadhoc/odoo-argentina.git adhoc-odoo-argentina",
        )
        self.assertEqual(
            cmds[18].usr_msg,
            "cloning b 9.0     https://github.com/ingadhoc/odoo-argentina.git >> adhoc-odoo-argentina",
        )

        self.assertEqual(
            cmds[19].args, "/odoo_ar/odoo-9.0/test2_client/sources/adhoc-odoo-argentina"
        )
        self.assertEqual(
            cmds[19].command,
            "git -C /odoo_ar/odoo-9.0/test2_client/sources/adhoc-odoo-argentina pull",
        )
        self.assertEqual(
            cmds[19].usr_msg,
            "pulling b 9.0     https://github.com/ingadhoc/odoo-argentina.git >> adhoc-odoo-argentina",
        )

    def test_install2_enterprise(self):
        """################################### TEST INSTALLATION v2 ENTERPRISE"""
        options = {
            "debug": True,
            "no-repos": False,
            "nginx": True,
            "extract_sources": False,
        }

        base_dir = "/odoo_ar/"
        oe = OdooEnv(options)
        cmds = oe.install("test2e_client")
        self.assertEqual(cmds[0].args, base_dir)
        self.assertEqual(cmds[0].command, "sudo mkdir " + base_dir)
        self.assertEqual(cmds[0].usr_msg, "Installing client test2e_client")

        self.assertEqual(
            cmds[2].args, "{}odoo-9.0e/test2e_client/postgresql".format(base_dir)
        )
        self.assertEqual(
            cmds[2].command,
            "mkdir -p {}odoo-9.0e/test2e_client/postgresql".format(base_dir),
        )
        self.assertEqual(cmds[2].usr_msg, False)

        self.assertEqual(cmds[8].args, "/odoo_ar/odoo-9.0e/dist-packages")
        self.assertEqual(cmds[8].command, "mkdir -p /odoo_ar/odoo-9.0e/dist-packages")
        self.assertEqual(cmds[8].usr_msg, False)

    def test_cmd(self):
        """########################################################## TEST CMD"""
        options = {
            "debug": False,
            "no-repos": False,
            "nginx": False,
        }
        oe = OdooEnv(options)

        # si no tiene argumentos para chequear no requiere chequeo
        c = Command(oe, command="cmd", usr_msg="hola")
        self.assertEqual(c.command, "cmd")
        self.assertEqual(c.usr_msg, "hola")
        self.assertEqual(c.args, False)
        self.assertEqual(c.check(), True)

        c = MakedirCommand(oe, command="cmd", args="no_existe_este_directorio")
        self.assertEqual(c.check_args(), True)

        c = CreateNginxTemplate(
            oe, command="cmd", args="no_exist", usr_msg="Testing msg"
        )
        self.assertEqual(c.usr_msg, "Testing msg")

    def test_qa(self):
        """########################################################### TEST QA"""
        options = {"debug": False}
        client_name = "test_client"
        database = "cliente_test"
        modules = "modulo_a_testear"

        oe = OdooEnv(options)
        client = Client(oe, client_name)

        cmds = oe.qa(client_name, database, modules, client_test=client)

        cmd = cmds[0]
        self.assertEqual(
            cmd.usr_msg,
            "Performing tests on module "
            "modulo_a_testear for client "
            "test_client and database cliente_test",
        )

        command = (
            "sudo docker run --rm -it "
            "-v /odoo_ar/odoo-9.0/test_client/config:/opt/odoo/etc/ "
            "-v /odoo_ar/odoo-9.0/test_client/data_dir:/opt/odoo/data "
            "-v /odoo_ar/odoo-9.0/test_client/log:/var/log/odoo "
            "-v /odoo_ar/odoo-9.0/test_client/sources:"
            "/opt/odoo/custom-addons "
            "-v /odoo_ar/odoo-9.0/test_client/backup_dir:/var/odoo/backups/ "
            "--link wdb "
            "-e WDB_SOCKET_SERVER=wdb "
            "-e ODOO_CONF=/dev/null "
            "--link pg-test_client:db jobiols/odoo-jeo:9.0.debug -- "
            "-d cliente_test "
            "--stop-after-init "
            "--log-level=test "
            "--test-enable "
            "-u modulo_a_testear "
        )

        self.assertEqual(cmd.command, command)

    def test_run_cli(self):
        """###################################################### TEST RUN CLI"""
        options = {
            "debug": False,
            "nginx": False,
        }
        client_name = "test_client"
        oe = OdooEnv(options)
        cmds = oe.run_client(client_name)

        cmd = cmds[0]
        self.assertEqual(
            cmd.usr_msg, "Starting Odoo image for client " "test_client on port 8069"
        )

        command = (
            "sudo docker run -d "
            "--link aeroo:aeroo "
            "-p 8069:8069 "
            "-p 8072:8072 "
            "-v /odoo_ar/odoo-9.0/test_client/config:/opt/odoo/etc/ "
            "-v /odoo_ar/odoo-9.0/test_client/data_dir:/opt/odoo/data "
            "-v /odoo_ar/odoo-9.0/test_client/log:/var/log/odoo "
            "-v /odoo_ar/odoo-9.0/test_client/sources:"
            "/opt/odoo/custom-addons "
            "-v /odoo_ar/odoo-9.0/test_client/backup_dir:/var/odoo/backups/ "
            "--link pg-test_client:db "
            "--restart=always "
            "--name test_client "
            "-e ODOO_CONF=/dev/null "
            "jobiols/odoo-jeo:9.0 "
            "--logfile=/var/log/odoo/odoo.log "
        )

        self.assertEqual(cmd.command, command)

    def test_run_cli_debug(self):
        """############################################## TEST RUN CLI W/DEBUG"""
        options = {
            "debug": True,
            "nginx": False,
        }
        client_name = "test_client"
        oe = OdooEnv(options)
        cmds = oe.run_client(client_name)

        cmd = cmds[0]
        self.assertEqual(
            cmd.usr_msg, "Starting Odoo image for client " "test_client on port 8069"
        )
        command = (
            "sudo docker run --rm -it "
            "--link aeroo:aeroo "
            "--link wdb "
            "-p 8069:8069 -p 8072:8072 "
            "-v /odoo_ar/odoo-9.0/test_client/config:/opt/odoo/etc/ "
            "-v /odoo_ar/odoo-9.0/test_client/data_dir:/opt/odoo/data "
            "-v /odoo_ar/odoo-9.0/test_client/log:/var/log/odoo "
            "-v /odoo_ar/odoo-9.0/test_client/sources:"
            "/opt/odoo/custom-addons "
            "-v /odoo_ar/odoo-9.0/test_client/backup_dir:/var/odoo/backups/ "
            "-v /odoo_ar/odoo-9.0/extra-addons:/opt/odoo/extra-addons "
            "-v /odoo_ar/odoo-9.0/dist-packages:"
            "/usr/lib/python2.7/dist-packages "
            "-v /odoo_ar/odoo-9.0/dist-local-packages:"
            "/usr/local/lib/python2.7/dist-packages "
            "--link pg-test_client:db "
            "--name test_client "
            "-e ODOO_CONF=/dev/null "
            "-e WDB_SOCKET_SERVER=wdb jobiols/odoo-jeo:9.0.debug "
            "--logfile=/dev/stdout "
        )

        self.assertEqual(cmd.command, command)

    def test_pull_images(self):
        """################################################## TEST PULL IMAGES"""
        options = {
            "debug": False,
            "nginx": False,
        }
        client_name = "test_client"
        oe = OdooEnv(options)
        cmds = oe.pull_images(client_name)

        cmd = cmds[0]
        self.assertEqual(cmd.usr_msg, "Pulling Image aeroo")
        command = "sudo docker pull jobiols/aeroo-docs"
        self.assertEqual(cmd.command, command)

        cmd = cmds[1]
        self.assertEqual(cmd.usr_msg, "Pulling Image odoo")
        command = "sudo docker pull jobiols/odoo-jeo:9.0"
        self.assertEqual(cmd.command, command)

        cmd = cmds[2]
        self.assertEqual(cmd.usr_msg, "Pulling Image postgres")
        command = "sudo docker pull postgres:9.5"
        self.assertEqual(cmd.command, command)

        cmd = cmds[3]
        self.assertEqual(cmd.usr_msg, "Pulling Image nginx")
        command = "sudo docker pull nginx:latest"
        self.assertEqual(cmd.command, command)

    def test_update(self):
        """################################################## TEST PULL UPDATE"""
        options = {
            "debug": False,
            "nginx": False,
        }
        client_name = "test_client"
        oe = OdooEnv(options)
        cmds = oe.update(client_name, "client_prod", ["all"])
        command = (
            "sudo docker run --rm -it "
            "-v /odoo_ar/odoo-9.0/test_client/config:/opt/odoo/etc/ "
            "-v /odoo_ar/odoo-9.0/test_client/data_dir:/opt/odoo/data "
            "-v /odoo_ar/odoo-9.0/test_client/log:/var/log/odoo "
            "-v /odoo_ar/odoo-9.0/test_client/sources:"
            "/opt/odoo/custom-addons "
            "-v /odoo_ar/odoo-9.0/test_client/backup_dir:/var/odoo/backups/ "
            "--link pg-test_client:db "
            "-e ODOO_CONF=/dev/null jobiols/odoo-jeo:9.0 "
            "-- "
            "--stop-after-init "
            "--logfile=false "
            "-d client_prod "
            "-u all "
        )
        self.assertEqual(cmds[0].command, command)

    def test_restore(self):
        """################################################# TEST PULL RESTORE"""
        options = {
            "debug": False,
            "nginx": False,
        }
        client_name = "test_client"
        database = "client_prod"
        backup_file = "bkp.zip"
        oe = OdooEnv(options)
        cmds = oe.restore(client_name, database, backup_file, no_deactivate=False)
        command = (
            "sudo docker run --rm -i "
            "--link pg-test_client:db "
            "-v /odoo_ar/odoo-9.0/test_client/backup_dir/:/backup "
            "-v /odoo_ar/odoo-9.0/test_client/data_dir/filestore:/filestore "
            "--env NEW_DBNAME=client_prod "
            "--env ZIPFILE=bkp.zip "
            "--env DEACTIVATE=True "
            "jobiols/dbtools:1.2.0 "
        )

        self.assertEqual(cmds[0].command, command)

    def test_download_image_sources(self):
        """####################################### TEST DOWNLOAD IMAGE SOURCES"""
        options = {
            "debug": True,
            "no-repos": False,
            "nginx": False,
            "extract_sources": True,
        }
        oe = OdooEnv(options)
        cmds = oe.install("test_client")

        command = "sudo mkdir /odoo_ar/"
        self.assertEqual(cmds[0].command, command)

        # command = 'sudo chown jobiols:jobiols /odoo_ar/'
        # self.assertEqual(cmds[1].command, command)

        command = "mkdir -p /odoo_ar/odoo-9.0/test_client/postgresql"
        self.assertEqual(cmds[2].command, command)

        command = "mkdir -p /odoo_ar/odoo-9.0/test_client/config"
        self.assertEqual(cmds[3].command, command)

        command = "mkdir -p /odoo_ar/odoo-9.0/test_client/data_dir"
        self.assertEqual(cmds[4].command, command)

        command = "mkdir -p /odoo_ar/odoo-9.0/test_client/backup_dir"
        self.assertEqual(cmds[5].command, command)

        command = "mkdir -p /odoo_ar/odoo-9.0/test_client/log"
        self.assertEqual(cmds[6].command, command)

        command = "mkdir -p /odoo_ar/odoo-9.0/test_client/sources"
        self.assertEqual(cmds[7].command, command)

        command = "mkdir -p /odoo_ar/odoo-9.0/dist-packages"
        self.assertEqual(cmds[8].command, command)

        command = "mkdir -p /odoo_ar/odoo-9.0/dist-local-packages"
        self.assertEqual(cmds[9].command, command)

        command = "mkdir -p /odoo_ar/odoo-9.0/extra-addons"
        self.assertEqual(cmds[10].command, command)

        command = "chmod og+w /odoo_ar/odoo-9.0/dist-packages"
        self.assertEqual(cmds[11].command, command)

        command = "chmod og+w /odoo_ar/odoo-9.0/dist-local-packages"
        self.assertEqual(cmds[12].command, command)

        command = "chmod og+w /odoo_ar/odoo-9.0/extra-addons"
        self.assertEqual(cmds[13].command, command)

        command = "chmod o+w /odoo_ar/odoo-9.0/test_client/config"
        self.assertEqual(cmds[14].command, command)

        command = "chmod o+w /odoo_ar/odoo-9.0/test_client/data_dir"
        self.assertEqual(cmds[15].command, command)

        command = "chmod o+w /odoo_ar/odoo-9.0/test_client/log"
        self.assertEqual(cmds[16].command, command)

        command = "chmod o+w /odoo_ar/odoo-9.0/test_client/backup_dir"
        self.assertEqual(cmds[17].command, command)

        command = (
            "sudo docker run -it --rm "
            "--entrypoint=/extract_dist-packages.sh "
            "-v /odoo_ar/odoo-9.0/dist-packages/:/mnt/dist-packages "
            "jobiols/odoo-jeo:9.0.debug "
        )
        self.assertEqual(cmds[18].command, command)

        command = (
            "sudo docker run -it --rm "
            "--entrypoint=/extract_dist-local-packages.sh "
            "-v /odoo_ar/odoo-9.0/dist-local-packages/:"
            "/mnt/dist-local-packages "
            "jobiols/odoo-jeo:9.0.debug "
        )
        self.assertEqual(cmds[19].command, command)

        command = (
            "sudo docker run -it --rm "
            "--entrypoint=/extract_extra-addons.sh "
            "-v /odoo_ar/odoo-9.0/extra-addons/:/mnt/extra-addons "
            "jobiols/odoo-jeo:9.0.debug "
        )
        self.assertEqual(cmds[20].command, command)

        command = "sudo chmod -R og+w /odoo_ar/odoo-9.0/dist-packages/"
        self.assertEqual(cmds[21].command, command)

        command = "sudo chmod -R og+w /odoo_ar/odoo-9.0/dist-local-packages/"
        self.assertEqual(cmds[22].command, command)

        command = "sudo chmod -R og+w /odoo_ar/odoo-9.0/extra-addons/"
        self.assertEqual(cmds[23].command, command)

        command = "/odoo_ar/odoo-9.0/dist-packages/.gitignore"
        self.assertEqual(cmds[24].command, command)

        command = "/odoo_ar/odoo-9.0/dist-local-packages/.gitignore"
        self.assertEqual(cmds[25].command, command)

        command = "/odoo_ar/odoo-9.0/extra-addons/.gitignore"
        self.assertEqual(cmds[26].command, command)

        command = "git -C /odoo_ar/odoo-9.0/dist-packages/ init "
        self.assertEqual(cmds[27].command, command)

        command = "git -C /odoo_ar/odoo-9.0/dist-local-packages/ init "
        self.assertEqual(cmds[28].command, command)

        command = "git -C /odoo_ar/odoo-9.0/extra-addons/ init "
        self.assertEqual(cmds[29].command, command)

        command = "git -C /odoo_ar/odoo-9.0/dist-packages/ add . "
        self.assertEqual(cmds[30].command, command)

        command = "git -C /odoo_ar/odoo-9.0/dist-local-packages/ add . "
        self.assertEqual(cmds[31].command, command)

        command = "git -C /odoo_ar/odoo-9.0/extra-addons/ add . "
        self.assertEqual(cmds[32].command, command)

        command = "git -C /odoo_ar/odoo-9.0/dist-packages/ commit -m inicial "
        self.assertEqual(cmds[33].command, command)

        command = "git -C /odoo_ar/odoo-9.0/dist-local-packages/ " "commit -m inicial "
        self.assertEqual(cmds[34].command, command)

        command = "git -C /odoo_ar/odoo-9.0/extra-addons/ commit -m inicial "
        self.assertEqual(cmds[35].command, command)

        command = (
            "git -C /odoo_ar/odoo-9.0/test_client/sources/ "
            "clone --depth 1 -b 9.0 "
            "https://github.com/jobiols/cl-test-client"
        )
        self.assertEqual(cmds[36].command, command)

        command = (
            "git -C " "/odoo_ar/odoo-9.0/test_client/sources/cl-test-client " "pull"
        )
        self.assertEqual(cmds[37].command, command)

        command = (
            "git -C /odoo_ar/odoo-9.0/test_client/sources/ "
            "clone --depth 1 "
            "-b 9.0 https://github.com/jobiols/odoo-addons"
        )
        self.assertEqual(cmds[38].command, command)

        command = "git -C " "/odoo_ar/odoo-9.0/test_client/sources/odoo-addons " "pull"
        self.assertEqual(cmds[39].command, command)

    def test_check_version(self):
        """##################################################### CHECK VERSION"""
        self.assertTrue(OeConfig().check_version())

    def test_environment(self):
        """##################################################### CHECK VERSION"""
        env = OeConfig().get_environment()
        OeConfig().save_environment("prod")
        env = OeConfig().get_environment()
        self.assertEqual(env, "prod")
        OeConfig().save_environment("debug")
        env = OeConfig().get_environment()
        self.assertEqual(env, "debug")

    def test_save_multiple_clients(self):
        OeConfig().save_client_path("test_clientx", "multiple_path1")
        OeConfig().save_client_path("test_clientx", "multiple_path2")
        self.assertEqual(OeConfig().get_client_path("test_clientx"), "multiple_path1")

    def test_repo_clone(self):
        repo = Repo({"usr": "jobiols", "repo": "project", "branch": "9.0"})
        self.assertEqual(
            repo.clone, "clone --depth 1 -b 9.0 https://github.com/jobiols/project"
        )

    def test_repo2_clone(self):
        repo = Repo2("https://github.com/jobiols/project.git", "9.0")
        self.assertEqual(repo.dir_name, "project")
        self.assertEqual(repo.branch, "9.0")
        self.assertEqual(repo.url, "https://github.com/jobiols/project.git")
        self.assertEqual(
            repo.formatted, "b 9.0     https://github.com/jobiols/project.git"
        )
        self.assertEqual(
            repo.clone, "clone --depth 1 -b 9.0 https://github.com/jobiols/project.git"
        )
        self.assertEqual(repo.pull, "pull")

    def test_repo2_clone_branch(self):
        repo = Repo2("https://github.com/jobiols/project.git -b 9.0", "8.0")
        self.assertEqual(repo.dir_name, "project")
        self.assertEqual(repo.branch, "9.0")
        self.assertEqual(repo.url, "https://github.com/jobiols/project.git")
        self.assertEqual(
            repo.formatted, "b 9.0     https://github.com/jobiols/project.git"
        )
        self.assertEqual(
            repo.clone, "clone --depth 1 -b 9.0 https://github.com/jobiols/project.git"
        )
        self.assertEqual(repo.pull, "pull")

    def test_repo2_clone_dir(self):
        repo = Repo2("https://github.com/jobiols/project.git adhoc-project", "9.0")
        self.assertEqual(repo.dir_name, "adhoc-project")
        self.assertEqual(repo.branch, "9.0")
        self.assertEqual(
            repo.url, "https://github.com/jobiols/project.git adhoc-project"
        )
        self.assertEqual(
            repo.formatted,
            "b 9.0     https://github.com/jobiols/project.git >> adhoc-project",
        )
        self.assertEqual(
            repo.clone,
            "clone --depth 1 -b 9.0 https://github.com/jobiols/project.git adhoc-project",
        )
        self.assertEqual(repo.pull, "pull")

    def test_repo2_clone_branch_dir(self):
        repo = Repo2(
            "https://github.com/jobiols/project.git adhoc-project -b 9.0", "8.0"
        )
        self.assertEqual(repo.dir_name, "adhoc-project")
        self.assertEqual(repo.branch, "9.0")
        self.assertEqual(
            repo.url, "https://github.com/jobiols/project.git adhoc-project"
        )
        self.assertEqual(
            repo.formatted,
            "b 9.0     https://github.com/jobiols/project.git >> adhoc-project",
        )
        self.assertEqual(
            repo.clone,
            "clone --depth 1 -b 9.0 https://github.com/jobiols/project.git adhoc-project",
        )
        self.assertEqual(repo.pull, "pull")

    def test_image(self):
        image = Image(
            {"name": "odoo", "usr": "jobiols", "img": "odoo-jeo", "ver": "9.0"}
        )
        self.assertEqual(image.name, "jobiols/odoo-jeo:9.0")
        self.assertEqual(image.version, "9.0")
        self.assertEqual(image.short_name, "odoo")

    def test_image2(self):
        image = Image2("odoo jobiols/odoo-jeo:9.0")
        self.assertEqual(image.name, "jobiols/odoo-jeo:9.0")
        self.assertEqual(image.version, "9.0")
        self.assertEqual(image.short_name, "odoo")
