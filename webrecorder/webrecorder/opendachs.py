#    OpenDACHS
#    Copyright (C) 2018  Carine Dengler, Heidelberg University
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>


"""
:synopsis: Webrecorder API.
"""

# standard library imports
import re
import os
import json
import base64

# third party imports
import redis
import webrecorder.utils
import webrecorder.webreccork
import webrecorder.models.base
import webrecorder.models.importer
import webrecorder.models.usermanager
import webrecorder.rec.webrecrecorder

# library specific imports


class API(object):
    """Webrecorder API.

    :ivar UserManager user_manager: API user manager
    """

    class UserManager(webrecorder.models.usermanager.UserManager):
        """API user manager.

        :ivar BaseAccess base_access: access rights
        """

        USER_RX = re.compile(r"[0-9A-Za-z]{8}")

        def __init__(self, strict_redis, wr_config):
            """Initialize API user manager."""
            self.base_access = webrecorder.models.base.BaseAccess()
            webreccork = webrecorder.webreccork.WebRecCork.create_cork(
                strict_redis, wr_config
            )
            super().__init__(strict_redis, webreccork, wr_config)
            return

        def _get_access(self):
            """Get access rights.

            :returns: access rights
            :rtype: BaseAccess
            """
            return self.base_access

    def __init__(self):
        """Initialize Webrecorder API."""
        self.strict_redis = redis.StrictRedis.from_url(
            os.environ["REDIS_BASE_URL"], decode_responses=True
        )
        self.wr_config = webrecorder.utils.load_wr_config()
        self.user_manager = self.UserManager(self.strict_redis, self.wr_config)
        return

    @staticmethod
    def generate_upload_id():
        """Generata upload ID.

        Code snippet see webrecorder.models.importer.py
        """
        try:
            upload_id = base64.b32encode(os.urandom(5)).decode("utf-8")
        except Exception as exception:
            raise RuntimeError("failed to get upload ID") from exception
        return upload_id

    def import_warc(self, archive, user):
        """Import WARC.

        :param str archive: WARC archive filename
        :param User user: Webrecorder user
        """
        try:
            wr_indexer = (
                webrecorder.rec.webrecrecorder.WebRecRecorder.make_wr_indexer(
                    self.wr_config
                )
            )
            wr_config = {k: v for k, v in self.wr_config.items()}
            wr_config.update({"wr_temp_coll": "ticket"})
            upload_id = self.generate_upload_id()
            inplace_importer = webrecorder.models.importer.InplaceImporter(
                self.strict_redis, wr_config, user, wr_indexer, upload_id
            )
            inplace_importer.multifile_upload(user, [archive])
        except Exception as exception:
            raise RuntimeError("failed to import WARC archive") from exception
        return

    def create_user(self, filename):
        """Create user.

        :param str filename: OpenDACHS ticket
        """
        try:
            with open(filename) as fp:
                data = json.load(fp)
            username, role, password, email_addr = data["user"]
            # Webrecorder API uses email_addr in order to manage users
            # use email_addr + ticket ID to create unique email_addr
            # not a valid email_addr but Webrecorder is not sending emails
            err, user = self.user_manager.create_user_as_admin(
                email_addr + data["id"],
                username,
                password,
                password,
                role,
                "OpenDACHS ticket {}".format(data["id"])
            )
            if err is not None:
                msg = "failed to create user:error(s) {}".format(
                    ", ".join("'{}'".format(v) for v in err)
                )
                raise RuntimeError(msg)
            elif user is None:
                msg = "failed to create user"
                raise RuntimeError(msg)
            self.import_warc("/{archive}".format(
                archive=data["archive"]), user[0]
            )
        except RuntimeError:
            raise
        except Exception as exception:
            raise RuntimeError("failed to create user") from exception
        return

    def delete_user(self, filename):
        """Delete user.

        :param str filename: OpenDACHS ticket
        """
        try:
            with open(filename) as fp:
                data = json.load(fp)
            username, _, _, _ = data["user"]
            self.user_manager.delete_user(username)
        except Exception as exception:
            raise RuntimeError("failed to delete user") from exception
        return

    def manage(self):
        """Manage OpenDACHS tickets."""
        try:
            dir_ = "/tmp/json_files"
            files = os.listdir(dir_)
            for filename in files:
                try:
                    filename = "{dir}/{filename}".format(
                        dir=dir_, filename=filename
                    )
                    fp = open(filename)
                    data = json.load(fp)
                    if data["flag"] == "pending":
                        self.create_user(filename)
                    elif data["flag"] == "deleted":
                        self.delete_user(filename)
                    else:
                        msg = "invalid flag {}".format(data["flag"])
                        raise RuntimeError(msg)
                except Exception as exception:
                    if "data" in locals():
                        raise RuntimeError(
                            "failed to manage OpenDACHS ticket {}".format(
                                data["id"]
                            )
                        ) from exception
                    else:
                        raise RuntimeError(
                            "failed to manage OpenDACHS ticket"
                        ) from exception
                finally:
                    if "fp" in locals():
                        fp.close()
                    os.unlink(filename)
        except Exception as exception:
            raise RuntimeError(
                "failed to manage OpenDACHS tickets"
            ) from exception
        return


def main():
    """Main routine."""
    try:
        api = API()
        api.manage()
    except Exception as exception:
        raise SystemExit("failed to call API") from exception
    return


if __name__ == "__main__":
    main()