from clients import Client
from metrics import jaro
from statistics import mean

class Matcher:
    def __init__(self, first_net_profiles, second_net_profiles):
        self.first_network = first_net_profiles
        self.second_network = second_net_profiles
        self.all_attributes = Client.FriendInfo._fields
        self.inverse_functional_property = ['site', 'twitter']

    def assign_weights_to_attributes(self, profiles_with_same_ipf): # name
        profiles_amount = len(profiles_with_same_ipf)
        pairs_amount = profiles_amount * (profiles_amount - 1) / 2
        v = [None] * pairs_amount
        pairs_count = 0
        for first_profile in profiles_with_same_ipf:
            for second_profile in profiles_with_same_ipf:
                if not first_profile is second_profile:
                    for attr in self.all_attributes:
                        first_attr = getattr(first_profile, attr)
                        second_attr = getattr(second_profile, attr)
                        if  first_attr and second_attr:
                            if v[pairs_count] is None:
                                v[pairs_count] = {}
                            v[pairs_count][attr] = jaro(first_attr, second_attr)
            pairs_count += 1
        weight = {}
        for attr in self.all_attributes:
            r = []
            for i in range(pairs_count):
                r.append(v[i][attr])
            weight[attr] = mean(r)
        return weight



