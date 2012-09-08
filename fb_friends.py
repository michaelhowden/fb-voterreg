import facebook
from voting_api import fetch_voter
from main.models import User, Friendship
from django.db import IntegrityError

TARGET_FRIEND_COUNT = 5

def _find_existing_users(user, friend_uids):
    """ Returns first TARGET_FRIEND_COUNT admirable existing users as Friendships. """
    friendships = []
    for uid in friend_uids:
        results = User.objects.filter(fb_uid=uid)[:1]
        if len(results) == 0:
            continue
        friend = results[0]
        if friend.is_admirable():
            friendships.append(Friendship(
                    user=user,
                    user_fb_uid=user.fb_uid,
                    friend=friend,
                    friend_fb_uid=friend.fb_uid,
                    registered=friend.registered,
                    date_pledged=friend.date_pledged,
                    invited_pledge_count=friend.invited_pledge_count))
            if len(friendships) >= TARGET_FRIEND_COUNT:
                break
    return friendships

def _find_registered_voters(user, access_token, friend_uids, num_needed):
    """ Uses the voting api to return first num_needed registered 
        voters as new Friendships """
    friendships = []
    for uid in friend_uids:
        voter = fetch_voter(uid, access_token)
        if voter.registered:
            friend, created = User.objects.get_or_create(fb_uid=uid)
            # FIXME: duplication with views.py#fetch_me
            friend.registered = True
            friend.data_fetched = True
            friend.save()
            friendships.append(Friendship(
                    user=user,
                    user_fb_uid=user.fb_uid,
                    friend=friend,
                    friend_fb_uid=friend.fb_uid,
                    registered=True))
            if len(friendships) >= num_needed:
                break
    return friendships

def _plain_friendships(user, friend_uids):
    friendships = []
    for uid in friend_uids:
        friend, created = User.objects.get_or_create(fb_uid=uid)
        # TODO: make factory classmethod for creation of Friendships.
        friendships.append(Friendship(
                user=user,
                user_fb_uid=user.fb_uid,
                friend=friend,
                friend_fb_uid=friend.fb_uid))
    return friendships

def _make_friendships(user, access_token, fb_friends):
    friend_uids = set(f["id"] for f in fb_friends)
    friendships = _find_existing_users(user, friend_uids)
    if len(friendships) < TARGET_FRIEND_COUNT:
        friendship_uids = set(f.friend_fb_uid for f in friendships)
        friendships.extend(_find_registered_voters(
                user, 
                access_token,
                friend_uids - friendship_uids,
                TARGET_FRIEND_COUNT - len(friendships)))
    if len(friendships) < TARGET_FRIEND_COUNT:
        friendship_uids = set(f.friend_fb_uid for f in friendships)
        friends_not_added = list(friend_uids - friendship_uids)
        num_needed = TARGET_FRIEND_COUNT - len(friendships)
        friendships.extend(_plain_friendships(
                user, friends_not_added[:num_needed]))
    for friendship in friendships:
        # possible (but unlikely) that an identical friendship has been 
        # saved by another process.
        try:
            friendship.save()
        except IntegrityError:
            pass

def get_friends(access_token):
    graph = facebook.GraphAPI(access_token)
    return graph.get_connections("me", "friends")

def fetch_friends(fb_uid, access_token):
    # this is a long-running function. so don't run it as part of an http request.
    # TODO: run the following section in one transaction
    user = User.objects.get(fb_uid=fb_uid)
    if user.friends_fetch_started:
        return
    user.friends_fetch_started = True
    user.save()

    # TODO: run the following section in a separate transaction    
    _make_friendships(
        user, access_token, get_friends(access_token))
    user = User.objects.get(fb_uid=fb_uid)
    user.friends_fetched = True
    user.save()
