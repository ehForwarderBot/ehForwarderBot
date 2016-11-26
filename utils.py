class Emojis:
    GROUP_EMOJI = "👥"
    USER_EMOJI = "👤"
    SYSTEM_EMOJI = "💻"
    UNKNOWN_EMOJI = "❓"
    LINK_EMOJI = "🔗"

    @staticmethod
    def get_source_emoji(t):
        if t == "User":
            return Emojis.USER_EMOJI
        elif t == "Group":
            return Emojis.GROUP_EMOJI
        elif t == "System":
            return Emojis.SYSTEM_EMOJI
        else:
            return Emojis.UNKNOWN_EMOJI


def extra(**kw):
    def attr_dec(f):
        if not "name" in kw or not "desc" in kw:
            raise ValueError("Key `name` and `desc` is required for extra functions.")
        f.__setattr__("extra_fn", True)
        for i in kw:
            f.__setattr__(i, kw[i])
        return f
    return attr_dec
