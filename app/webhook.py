from __future__ import annotations

import logging
import json
from urllib.parse import parse_qs

from aiohttp import web
from aiogram import Bot

from app.services.webhooks.fawaterk_webhook import FawaterkWebhookError, handle_fawaterk_invoice_webhook
from app.services.webhooks.zeno_webhook import ZenoWebhookError, handle_zeno_checkout_webhook


logger = logging.getLogger(__name__)


def create_zeno_webhook_app(bot: Bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/webhooks/zeno", zeno_webhook_handler)
    app.router.add_post("/webhooks/fawaterk", fawaterk_webhook_handler)
    app.router.add_get("/health", health_handler)
    return app


async def health_handler(_: web.Request) -> web.Response:
    return web.json_response({"ok": True})


async def zeno_webhook_handler(request: web.Request) -> web.Response:
    raw_body = await request.text()
    _log_incoming_webhook("Zeno", request, raw_body)
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        logger.warning("Zeno webhook invalid JSON: body=%s", raw_body)
        return web.json_response({"ok": False, "error": "Invalid JSON payload."}, status=400)

    if not isinstance(payload, dict):
        logger.warning("Zeno webhook non-object JSON: payload=%r", payload)
        return web.json_response({"ok": False, "error": "Payload must be a JSON object."}, status=400)

    bot = request.app["bot"]
    try:
        result = await handle_zeno_checkout_webhook(payload, bot)
    except ZenoWebhookError as error:
        logger.warning("Zeno webhook rejected: %s", error)
        return web.json_response({"ok": False, "error": str(error)}, status=400)
    except Exception:
        logger.exception("Unexpected Zeno webhook failure.")
        return web.json_response({"ok": False, "error": "Webhook processing failed."}, status=500)

    logger.info("Zeno webhook result: target=%s handled=%s message=%s", result.target, result.handled, result.message)
    return web.json_response(
        {
            "ok": True,
            "handled": result.handled,
            "target": result.target,
            "message": result.message,
        }
    )


async def fawaterk_webhook_handler(request: web.Request) -> web.Response:
    raw_body = await request.text()
    _log_incoming_webhook("Fawaterk", request, raw_body)
    payload: dict | None = None
    content_type = (request.content_type or "").lower()
    if content_type == "application/x-www-form-urlencoded":
        payload = _parse_form_payload(raw_body)
    else:
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            if "=" in raw_body:
                payload = _parse_form_payload(raw_body)
            else:
                logger.warning("Fawaterk webhook invalid JSON: body=%s", raw_body)
                return web.json_response({"ok": False, "error": "Invalid JSON payload."}, status=400)

    if not isinstance(payload, dict):
        logger.warning("Fawaterk webhook non-object JSON: payload=%r", payload)
        return web.json_response({"ok": False, "error": "Payload must be a JSON object."}, status=400)

    if not payload:
        logger.warning("Fawaterk webhook empty payload: body=%s", raw_body)
        return web.json_response({"ok": False, "error": "Payload is empty."}, status=400)

    bot = request.app["bot"]
    try:
        result = await handle_fawaterk_invoice_webhook(payload, bot)
    except FawaterkWebhookError as error:
        logger.warning("Fawaterk webhook rejected: %s", error)
        return web.json_response({"ok": False, "error": str(error)}, status=400)
    except Exception:
        logger.exception("Unexpected Fawaterk webhook failure.")
        return web.json_response({"ok": False, "error": "Webhook processing failed."}, status=500)

    logger.info(
        "Fawaterk webhook result: target=%s handled=%s message=%s",
        result.target,
        result.handled,
        result.message,
    )
    return web.json_response(
        {
            "ok": True,
            "handled": result.handled,
            "target": result.target,
            "message": result.message,
        }
    )


def _log_incoming_webhook(provider: str, request: web.Request, raw_body: str) -> None:
    headers = {key: value for key, value in request.headers.items()}
    logger.info(
        "%s webhook received: method=%s path=%s remote=%s headers=%s body=%s",
        provider,
        request.method,
        request.path_qs,
        request.remote,
        headers,
        raw_body,
    )


def _parse_form_payload(raw_body: str) -> dict:
    parsed = parse_qs(raw_body, keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}
