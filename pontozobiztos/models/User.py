from functools import reduce
import operator
from datetime import datetime

from pontozobiztos import chatmongo
from pontozobiztos import utils
from pontozobiztos.models import Point
from pontozobiztos.models import Multiplier


# TODO: This should be turned into a cache if performance issues arise.
# consider using the signal library, to signal changes back from the
# chatmongo module.

class User:
    def __new__(cls, userid, *args, **kwargs):
        if chatmongo.get_user_info(userid):
            return super().__new__(cls, *args, **kwargs)
        else:
            return None

    def __init__(self, userid):
        self.uid = userid

    def __repr__(self):
        attr_dict = {
            "fullname": self.fullname,
            "nickname": self.nickname,
            "multiplier": self.multiplier,
            "points": self.points_sum
        }
        return str(attr_dict)

    @property
    def nickname(self):
        """Nickname of the user"""
        return chatmongo.get_user_info(self.uid).get("nickname")

    @nickname.setter
    def nickname(self, value):
        chatmongo.update_info(self.uid, 'nickname', value)

    @property
    def fullname(self):
        """Last name of the user"""
        return chatmongo.get_user_info(self.uid).get("fullname")

    @fullname.setter
    def fullname(self, value):
        chatmongo.update_info(self.uid, 'fullname', value)

    @property
    def last_read_at(self):
        return chatmongo.get_user_info(self.uid).get('last_read_at')

    @last_read_at.setter
    def last_read_at(self, value):
        chatmongo.update_info(self.uid, 'last_read_at', value)

    @property
    def points_sum(self):
        """Sum of points in the current season"""
        return chatmongo.get_points_sum(self.uid)

    @property
    def is_admin(self):
        return chatmongo.get_user_info(self.uid).get("is_admin", False)

    @property
    def multiplier(self):
        """Current multiplier"""
        try:
            return reduce(operator.mul, [mul.value for mul
                                         in self.get_multiplier_list()])
        except TypeError:
            return 1.0

    def set_multiplier(self, value, typename, days=0, hours=0, minutes=0):
        """Sets a multiplier for the current user until the given time.
        If all values left at 0 the multiplier will last until
        the end of the current season.

        Args:
            value (float): multiplication factor
            typename (str): typename of the multiplier
            days (int): days displacement
            hours (int): hours displacement
            minutes (int): minutes displacement
        """
        if not any((days, hours, minutes)):
            expiry_date = utils.get_season_end()
        else:
            expiry_date = utils.get_later_datetime(days, hours, minutes)
        chatmongo.set_multiplier(self.uid, value, typename, expiry_date)

    def get_multiplier_list(self, include_expired=False):
        """Retrieves currently active multipliers from db if
         include_expired is False, otherwise all of them.

        Args:
            include_expired (bool): Flag to include non active
                multipliers

        Returns:
            list: list of Multiplier objects
        """
        mul_list = chatmongo.get_multipliers(self.uid, include_expired)
        return [Multiplier.Multiplier(**mult) for mult in mul_list]

    def get_point_list(self, from_date=None, to_date=None):
        """Retrieves the list of points that the player received
        in between from_date and to_date. By default it selects the
        current season.

        Args:
            from_date (datetime): beginning date and time to retrieve
                information from the database
            to_date (datetime): ending date and time to retrieve
                information from the database

        Returns:
              list: list of Point objects. (empty list if none found)
        """
        pts_list = chatmongo.get_points(self.uid, from_date, to_date)
        return [Point.Point(**point) for point in pts_list]

    def add_points(self, value, source, mid, desc="", apply_multiplier=True):
        """Adds 'value' amount of points to the user at the current
        timestamp. Can also be a negative amount.

        Args:
            value (float): amount of points to add
            source (str): source of the points (module name)
            mid (str): facebook message_id
            desc (str): (optional) extra info
            apply_multiplier (bool): apply multiplier
        """
        mult = self.multiplier if apply_multiplier else 1
        return chatmongo.add_points(self.uid, value * mult, source, mid=mid,
                                    desc=desc + f" (multiplier: {mult})")

    # def add_message(self, message_object):
    #     """Registers a message to the user.
    #
    #     Args:
    #         message_object (Message): fbchat.Message object
    #     """
    #     chatmongo.insert_or_update_message(message_object)

    def get_message_list(self, from_date=None, to_date=None):
        """Retrieves messages for the current user from the database,
        between the given dates.

        Args:
            from_date (datetime): beginning date and time to retrieve
                information from the database
            to_date (datetime): ending date and time to retrieve
                information from the database

        Returns:
            list: list of fbchat.Message objects.
                (empty list if none found)
        """
        msg_list = chatmongo.get_messages_by_user_ids(
            self.uid, from_date=from_date, to_date=to_date)
        return msg_list


if __name__ == "__main__":
    print(a := User("100001108161207"))
    print(a.uid)