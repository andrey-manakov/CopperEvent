from __future__ import annotations

from telebot import types

from ..utils.dates import TIME_SLOTS


def main_reply_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("New", "My")
    markup.row("Browse", "Friends")
    markup.row("Settings", "Help")
    return markup


def time_slot_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton(text=slot, callback_data=f"TIME:{slot}") for slot in TIME_SLOTS]
    markup.add(*buttons)
    return markup


def event_action_keyboard(event_id: int, joined: bool, is_owner: bool) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    if is_owner:
        markup.add(
            types.InlineKeyboardButton("Delete", callback_data=f"DELETE:{event_id}"),
            types.InlineKeyboardButton("Share", callback_data=f"SHARE:{event_id}"),
        )
    else:
        if joined:
            markup.add(types.InlineKeyboardButton("Leave", callback_data=f"LEAVE:{event_id}"))
        else:
            markup.add(types.InlineKeyboardButton("Join", callback_data=f"JOIN:{event_id}"))
        markup.add(types.InlineKeyboardButton("Share", callback_data=f"SHARE:{event_id}"))
    markup.add(types.InlineKeyboardButton("View", callback_data=f"VIEW:{event_id}"))
    return markup


def browse_action_keyboard(event_id: int, joined: bool) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    if joined:
        markup.add(types.InlineKeyboardButton("Leave", callback_data=f"LEAVE:{event_id}"))
    else:
        markup.add(types.InlineKeyboardButton("Join", callback_data=f"JOIN:{event_id}"))
    markup.add(types.InlineKeyboardButton("View", callback_data=f"VIEW:{event_id}"))
    return markup


def share_keyboard(event_id: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Share", callback_data=f"SHARE:{event_id}"))
    return markup
