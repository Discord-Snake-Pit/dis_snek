from typing import TYPE_CHECKING, List, Optional, Union

from dis_snek.models.discord_objects.message import process_message_payload
from dis_snek.models.enums import MessageFlags

if TYPE_CHECKING:
    from pathlib import Path

    from aiohttp.formdata import FormData

    from dis_snek.client import Snake
    from dis_snek.models.discord_objects.components import BaseComponent
    from dis_snek.models.discord_objects.embed import Embed
    from dis_snek.models.discord_objects.message import AllowedMentions, Message, MessageReference
    from dis_snek.models.discord_objects.sticker import Sticker
    from dis_snek.models.snowflake import Snowflake_Type


class SendMixin:
    _client: "Snake"

    async def _send_http_request(self, message_payload: Union[dict, "FormData"]) -> dict:
        raise NotImplementedError

    async def send(
            self,
            content: Optional[str] = None,
            embeds: Optional[Union[List[Union["Embed", dict]], Union["Embed", dict]]] = None,
            components: Optional[
                Union[
                    List[List[Union["BaseComponent", dict]]], List[Union["BaseComponent", dict]], "BaseComponent", dict]
            ] = None,
            stickers: Optional[Union[List[Union["Sticker", "Snowflake_Type"]], "Sticker", "Snowflake_Type"]] = None,
            allowed_mentions: Optional[Union["AllowedMentions", dict]] = None,
            reply_to: Optional[Union["MessageReference", "Message", dict, "Snowflake_Type"]] = None,
            filepath: Optional[Union[str, "Path"]] = None,
            tts: bool = False,
            flags: Optional[Union[int, "MessageFlags"]] = None,
    ) -> "Message":
        """
        Send a message.

        :param content: Message text content.
        :param embeds: Embedded rich content (up to 6000 characters).
        :param components: The components to include with the message.
        :param stickers: IDs of up to 3 stickers in the server to send in the message.
        :param allowed_mentions: Allowed mentions for the message.
        :param reply_to: Message to reference, must be from the same channel.
        :param filepath: Location of file to send, defaults to None.
        :param tts: Should this message use Text To Speech.
        :param flags: Message flags to apply.

        :return: New message object that was sent.
        """
        message_payload = process_message_payload(
            content=content,
            embeds=embeds,
            components=components,
            stickers=stickers,
            allowed_mentions=allowed_mentions,
            reply_to=reply_to,
            filepath=filepath,
            tts=tts,
            flags=flags,
        )

        message_data = await self._send_http_request(message_payload)
        if message_data:
            return self._client.cache.place_message_data(message_data)
